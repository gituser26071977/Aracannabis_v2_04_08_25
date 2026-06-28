"""
Webhook Auth — Helper centralizado para validacao de webhooks (P0-A FASE 4)

Funcoes:
- validate_mercadopago_signature: padrao oficial Mercado Pago (x-signature + x-request-id + data.id)
- validate_generic_hmac_signature: HMAC SHA256 generico (Evolution API)
- validate_internal_key: compare_digest para X-Internal-Key
- check_replay: idempotencia via WebhookLog (provider + provider_event_id)

Variaveis ENV esperadas:
- MERCADOPAGO_WEBHOOK_SECRET
- MERCADOPAGO_MODULOS_WEBHOOK_SECRET
- EVOLUTION_WEBHOOK_SECRET
- DR_ANDERSON_WEBHOOK_SECRET
- INTERNAL_SERVICE_KEY
- ALLOW_WEBHOOK_SIMULATION (1/0)
"""
import hmac
import hashlib
import json
import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from flask import current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────
MAX_TIMESTAMP_AGE_SECONDS = 300  # anti-replay: 5 min
REPLAY_TTL_HOURS = 24  # persistencia do event_id no WebhookLog


# ──────────────────────────────────────────────────────────────────
# Helpers de baixo nivel (sem dependencia de Flask)
# ──────────────────────────────────────────────────────────────────
def _compute_hmac_sha256(secret: str, message: str) -> str:
    """Calcula HMAC SHA256 hex de uma mensagem."""
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _get_env(name: str) -> Optional[str]:
    val = os.environ.get(name)
    return val if val else None


# ──────────────────────────────────────────────────────────────────
# Validacao de timestamp
# ──────────────────────────────────────────────────────────────────
def validate_timestamp(timestamp_str: str, max_age: int = MAX_TIMESTAMP_AGE_SECONDS) -> bool:
    """
    Verifica que o timestamp esta dentro de max_age segundos de agora.
    Retorna True se OK, False caso contrario.
    """
    if not timestamp_str:
        return False
    try:
        ts = int(timestamp_str)
    except (TypeError, ValueError):
        return False
    now = int(time.time())
    return abs(now - ts) <= max_age


# ──────────────────────────────────────────────────────────────────
# Padrao oficial Mercado Pago
# https://www.mercadopago.com.br/developers/pt/reference/notifications/webhooks
# ──────────────────────────────────────────────────────────────────
def validate_mercadopago_signature(
    secret: str,
    x_signature: str,
    x_request_id: str,
    data_id: str,
    raw_body: str,
) -> Tuple[bool, str]:
    """
    Valida assinatura do MercadoPago no formato:
      x-signature: ts=1700000000,v1=abc123...
      template:    id:{data_id};request-id:{x_request_id};ts:{ts};

    FASE 4.5 — aplica .lower() no data_id conforme spec oficial do MP
    (funcao buildManifest do SDK Go: id value é lowecased antes do HMAC).

    Args:
        secret:        secret do MP (env MERCADOPAGO_WEBHOOK_SECRET)
        x_signature:   valor cru do header x-signature
        x_request_id:  valor do header x-request-id
        data_id:       valor de data.id (query param ou body)
        raw_body:      corpo bruto (string) para eventual re-check futuro

    Returns:
        (True, "ok")  ou  (False, "<motivo>")
    """
    if not secret:
        return False, "secret ausente"
    if not x_signature or not x_request_id or not data_id:
        return False, "headers incompletos (x-signature/x-request-id/data.id)"

    # Extrair ts e v1 do header x-signature
    parts = dict(p.split("=", 1) for p in x_signature.split(",") if "=" in p)
    ts = parts.get("ts", "")
    v1 = parts.get("v1", "")
    if not ts or not v1:
        return False, "x-signature malformado (esperado ts=...,v1=...)"

    # Anti-replay: timestamp dentro de 5 min
    if not validate_timestamp(ts):
        return False, "timestamp stale (>5min)"

    # FASE 4.5 — Spec oficial MP: id value é LOWERCASED antes do HMAC.
    # SDK Go: buildManifest() -> id:<dataID_lower>...
    data_id_normalized = str(data_id).strip().lower()

    # Montar template oficial MP (com data_id normalizado)
    template = f"id:{data_id_normalized};request-id:{x_request_id};ts:{ts};"
    expected = _compute_hmac_sha256(secret, template)

    if not hmac.compare_digest(expected, v1):
        return False, "assinatura invalida"

    return True, "ok"


# ──────────────────────────────────────────────────────────────────
# HMAC SHA256 generico (Evolution API ou outros)
# ──────────────────────────────────────────────────────────────────
def validate_generic_hmac_signature(
    secret: str,
    signature_header: str,
    raw_body: str,
    prefix: str = "sha256=",
) -> Tuple[bool, str]:
    """
    Valida assinatura HMAC SHA256 generica.

    Args:
        secret:           secret compartilhado (env)
        signature_header: valor cru do header (ex: x-webhook-signature)
        raw_body:         corpo bruto (string) do request
        prefix:           prefixo esperado (default: "sha256=")

    Returns:
        (True, "ok")  ou  (False, "<motivo>")
    """
    if not secret:
        return False, "secret ausente"
    if not signature_header:
        return False, "header de assinatura ausente"

    received = signature_header.strip()
    if prefix and received.startswith(prefix):
        received = received[len(prefix):]

    expected = _compute_hmac_sha256(secret, raw_body)
    if not hmac.compare_digest(expected, received):
        return False, "assinatura invalida"

    return True, "ok"


# ──────────────────────────────────────────────────────────────────
# X-Internal-Key (compare_digest)
# ──────────────────────────────────────────────────────────────────
def validate_internal_key(provided: str, expected: str) -> bool:
    """
    Compara X-Internal-Key usando compare_digest (anti timing-attack).
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided, expected)


# ──────────────────────────────────────────────────────────────────
# Anti-replay via WebhookLog (reutiliza tabela existente)
# ──────────────────────────────────────────────────────────────────
def check_replay(provider: str, event_id: str) -> Tuple[bool, Optional[int]]:
    """
    DEPRECATED (FASE 4.1): usar register_webhook_event em vez desta funcao.
    Mantida por compatibilidade com testes legados.
    Verifica se (provider, event_id) ja foi registrado.
    """
    if not event_id:
        return False, None
    try:
        from models_extra import WebhookLog
        existing = WebhookLog.query.filter_by(
            provider=provider, provider_event_id=str(event_id)
        ).first()
        if existing:
            return True, existing.id
    except Exception as e:
        logger.warning(f"[webhook_auth] check_replay falhou: {e}")
    return False, None


def register_webhook_event(
    provider: str,
    event_id: str,
    event_type: str = "unknown",
    payload: Any = None,
) -> Tuple[bool, Optional[int]]:
    """
    FASE 4.1 — Registro atomico de webhook event via INSERT + UNIQUE constraint.

    Garante idempotencia real para TODOS os webhooks (W1..W5) sem depender
    de feature flags. Substitui o padrao fragil check_replay+process() por
    um INSERT atomico: a UNIQUE(provider, provider_event_id) faz a deduplicacao
    no banco, eliminando a race condition SELECT+INSERT.

    Args:
        provider:   nome canonico do provedor (mercadopago, evolution_tenant,
                    evolution_dr_anderson, modulos, etc.)
        event_id:   identificador unico do evento (data.id, message id, etc.)
        event_type: tipo do evento (mercadopago_webhook, messages.upsert, etc.)
        payload:    payload JSON (opcional, para auditoria)

    Returns:
        (True, log_id)   se evento ja existia (replay detectado)
        (False, log_id)  se evento foi registrado agora (novo)
        (False, None)    se event_id vazio ou erro nao-recuperavel

    Comportamento atomico:
        - INSERT direto, sem SELECT previo
        - UNIQUE(provider, provider_event_id) -> IntegrityError se duplicado
        - db.session.rollback() no IntegrityError, depois SELECT para obter id
        - requests simultaneas: a 2a request pega IntegrityError, rollback,
          SELECT, retorna replay=True. Nenhum 500 retornado.
    """
    if not provider or not event_id:
        return False, None
    try:
        from models import db
        from models_extra import WebhookLog

        log = WebhookLog(
            provider=provider,
            event_type=event_type,
            provider_event_id=str(event_id),
            payload=payload,
            processed=False,
        )
        db.session.add(log)
        db.session.commit()
        # INSERT OK: evento novo
        return False, log.id

    except IntegrityError as e:
        # UNIQUE violation: replay detectado
        try:
            from models import db as _db
            _db.session.rollback()
        except Exception:
            pass
        try:
            from models_extra import WebhookLog
            existing = WebhookLog.query.filter_by(
                provider=provider, provider_event_id=str(event_id)
            ).first()
            return True, existing.id if existing else None
        except Exception:
            return True, None

    except Exception as e:
        # Erro nao-recuperavel (DB down, etc): permite processamento sem lock
        try:
            from models import db as _db
            _db.session.rollback()
        except Exception:
            pass
        logger.warning(
            f"[webhook_auth] register_webhook_event falhou "
            f"(provider={provider} event_id={event_id}): {e}"
        )
        return False, None


# ──────────────────────────────────────────────────────────────────
# Decorators
# ──────────────────────────────────────────────────────────────────
def mercadopago_webhook_required(
    get_data_id: Callable[[Any], str],
    env_var: str = "MERCADOPAGO_WEBHOOK_SECRET",
):
    """
    Decorator para webhooks do MercadoPago.

    FASE 4.5 — Melhorias:
      * env_var: aceita env var customizada (default MERCADOPAGO_WEBHOOK_SECRET).
        Para W5 (modulos), passar MERCADOPAGO_MODULOS_WEBHOOK_SECRET.
      * data_id é lido PRIMEIRO do query string (?data.id=...) conforme spec
        oficial MP, e só depois do JSON body via get_data_id(payload) como
        fallback (MP envia nos dois lugares, mas spec manda usar query).
      * data_id é normalizado (.strip().lower()) dentro de
        validate_mercadopago_signature.

    Args:
        get_data_id: funcao que extrai data_id do JSON body (fallback)
        env_var:     nome da env var que guarda o secret do MP
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            secret = _get_env(env_var)
            if not secret:
                current_app.logger.error(
                    f"[mercadopago_webhook] {env_var} nao configurado"
                )
                return jsonify({"error": "server misconfigured"}), 500

            x_sig = request.headers.get("x-signature", "")
            x_req = request.headers.get("x-request-id", "")

            # FASE 4.5 — Spec oficial MP: data.id vem do query string.
            # Flask parseia ?data.id=12345 como args["data.id"].
            data_id_from_query = str(request.args.get("data.id", "") or "").strip()

            try:
                payload = request.get_json(silent=True) or {}
            except Exception:
                payload = {}

            # Fallback: extrai do body via callback
            data_id_from_body = ""
            if not data_id_from_query:
                try:
                    data_id_from_body = str(get_data_id(payload) or "").strip()
                except Exception:
                    data_id_from_body = ""

            data_id = data_id_from_query or data_id_from_body
            raw_body = request.get_data(as_text=True) or ""

            ok, reason = validate_mercadopago_signature(
                secret=secret,
                x_signature=x_sig,
                x_request_id=x_req,
                data_id=data_id,
                raw_body=raw_body,
            )
            if not ok:
                current_app.logger.warning(
                    f"[mercadopago_webhook] rejeitado: {reason} (ip={request.remote_addr})"
                )
                return jsonify({"error": "invalid signature", "reason": reason}), 401

            return func(*args, **kwargs)
        return wrapper
    return decorator


def hmac_webhook_required(
    secret_env: str,
    signature_header: str = "x-webhook-signature",
    provider_name: str = "generic",
):
    """
    Decorator para webhooks com HMAC SHA256 generico (ex: Evolution).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            secret = _get_env(secret_env)
            if not secret:
                current_app.logger.error(
                    f"[hmac_webhook] {secret_env} nao configurado"
                )
                return jsonify({"error": "server misconfigured"}), 500

            sig = request.headers.get(signature_header, "")
            raw_body = request.get_data(as_text=True) or ""

            ok, reason = validate_generic_hmac_signature(
                secret=secret, signature_header=sig, raw_body=raw_body
            )
            if not ok:
                current_app.logger.warning(
                    f"[{provider_name}_webhook] rejeitado: {reason} (ip={request.remote_addr})"
                )
                return jsonify({"error": "invalid signature", "reason": reason}), 401

            return func(*args, **kwargs)
        return wrapper
    return decorator


def internal_key_required(
    env_var: str = "INTERNAL_SERVICE_KEY",
    header_name: str = "X-Internal-Key",
):
    """
    Decorator para endpoints internos com compare_digest (anti timing-attack).

    FASE 4.5 — Aceita header customizado:
      * W3 (criar-lead) usa X-Internal-Key (default, sem mudar chamada)
      * W2/W4 (Evolution webhooks) usam X-Internal-Token (header_name passado)

    Args:
        env_var:     nome da env var que guarda o secret esperado
        header_name: nome do header HTTP a ser lido (default X-Internal-Key)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            expected = _get_env(env_var)
            if not expected:
                current_app.logger.error(
                    f"[internal_key] {env_var} nao configurado"
                )
                return jsonify({"error": "server misconfigured"}), 500
            provided = request.headers.get(header_name, "")
            if not validate_internal_key(provided, expected):
                current_app.logger.warning(
                    f"[internal_key] rejeitado de ip={request.remote_addr} "
                    f"endpoint={request.path} header={header_name}"
                )
                return jsonify({"error": "unauthorized"}), 401
            return func(*args, **kwargs)
        return wrapper
    return decorator


def assert_required_secrets_on_startup(env_vars: list, is_production: bool):
    """
    Chamado em app factory para abortar startup se secrets obrigatorios faltarem.
    """
    if not is_production:
        return
    missing = [v for v in env_vars if not _get_env(v)]
    if missing:
        raise RuntimeError(
            f"[webhook_auth] ABORT STARTUP: secrets obrigatorios ausentes em producao: {missing}"
        )
