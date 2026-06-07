"""
AraOS Platform — Event Conventions.

Regras obrigatórias para TODOS os eventos da plataforma.
Quebrar uma dessas regras = evento rejeitado pelo Event Bus.
"""

from typing import Dict, Any
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════
# 1. NAMING CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

EVENT_TYPE_PATTERN = "{DOMAIN}_{ACTION}"

VALID_DOMAINS = {
    "patient", "consultation", "clinical_record", "document",
    "communication", "voice", "smart_flow", "payment", "security",
    "billing", "association", "catalog", "ai", "integration",
}

VALID_ACTIONS = {
    "created", "updated", "deleted", "merged",
    "scheduled", "started", "finished", "cancelled", "no_show",
    "requested", "received", "sent", "delivered", "failed",
    "detected", "completed", "entered", "left", "exceeded",
    "uploaded", "processed", "purged", "exported",
    "succeeded", "revoked", "changed", "enabled", "disabled",
    "renewed", "expired", "executed", "assigned",
}


def validate_event_name(event_type: str) -> tuple:
    """
    Valida nome de evento segundo as convenções.
    
    Returns:
        (is_valid: bool, error_message: str or None)
    """
    if not event_type:
        return False, "event_type cannot be empty"
    
    # Deve ser UPPER_CASE
    if event_type != event_type.upper():
        return False, f"event_type must be UPPER_CASE. Got: {event_type}"
    
    # Deve ter exatamente um underscore separando domain e action
    parts = event_type.split("_")
    if len(parts) < 2:
        return False, f"event_type must follow DOMAIN_ACTION pattern. Got: {event_type}"
    
    domain = "_".join(parts[:-1]).lower()
    action = parts[-1].lower()
    
    # Domain pode ser composto (ex: clinical_record)
    # Action é sempre a última parte
    
    if action not in VALID_ACTIONS:
        return False, f"Invalid action '{action}'. Valid: {sorted(VALID_ACTIONS)}"
    
    return True, None


# ═══════════════════════════════════════════════════════════════════════
# 2. VERSIONING CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

CURRENT_EVENT_VERSION = "1.0"

# Regras de versionamento semântico para eventos:
# - PATCH (1.0.1): Correção de bug, campos opcionais adicionados
# - MINOR (1.1.0): Novos campos obrigatórios, novos consumers
# - MAJOR (2.0.0): Mudança estrutural, campos removidos, breaking change
#
# Regra de ouro: NUNCA remova campos. Deprecie com @deprecated em documentação.


def bump_version(current: str, change_type: str) -> str:
    """
    Incrementa versão de evento.
    
    Args:
        current: Versão atual (ex: "1.0")
        change_type: "patch", "minor", ou "major"
    
    Returns:
        Nova versão
    """
    parts = current.split(".")
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    
    if change_type == "patch":
        patch += 1
    elif change_type == "minor":
        minor += 1
        patch = 0
    elif change_type == "major":
        major += 1
        minor = 0
        patch = 0
    
    if patch > 0:
        return f"{major}.{minor}.{patch}"
    return f"{major}.{minor}"


# ═══════════════════════════════════════════════════════════════════════
# 3. RETRY & DLQ CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_MAX_RETRIES = 3
RETRY_BACKOFF_STRATEGY = "exponential"  # exponential | linear | fixed
RETRY_BASE_DELAY_SECONDS = 1
RETRY_MAX_DELAY_SECONDS = 60

# Dead Letter Queue naming
DLQ_SUFFIX = "_dlq"
RETRY_SUFFIX = "_retry"


def calculate_retry_delay(attempt: int, strategy: str = None) -> int:
    """
    Calcula delay antes da próxima tentativa.
    
    Args:
        attempt: Número da tentativa (1-indexed)
        strategy: "exponential", "linear", ou "fixed"
    
    Returns:
        Delay em segundos
    """
    strategy = strategy or RETRY_BACKOFF_STRATEGY
    base = RETRY_BASE_DELAY_SECONDS
    max_delay = RETRY_MAX_DELAY_SECONDS
    
    if strategy == "exponential":
        delay = base * (2 ** (attempt - 1))
    elif strategy == "linear":
        delay = base * attempt
    else:  # fixed
        delay = base
    
    return min(delay, max_delay)


# ═══════════════════════════════════════════════════════════════════════
# 4. IDEMPOTENCY CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

# Todo evento DEVE ter um event_id único (UUID4)
# Consumers idempotentes devem rastrear event_ids processados

IDEMPOTENCY_KEY_HEADER = "X-Idempotency-Key"
IDEMPOTENCY_TTL_HOURS = 24  # Quanto tempo manter registro de ids processados


def generate_idempotency_key(event_type: str, aggregate_id: str, timestamp: str) -> str:
    """
    Gera chave de idempotência baseada em conteúdo determinístico.
    
    Útil para reprocessamentos onde event_id muda mas conteúdo é igual.
    """
    import hashlib
    content = f"{event_type}:{aggregate_id}:{timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


# ═══════════════════════════════════════════════════════════════════════
# 5. TEMPORAL CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

TIMESTAMP_FORMAT = "ISO8601"  # YYYY-MM-DDTHH:MM:SS.sssZ
TIMESTAMP_TIMEZONE = "UTC"    # Todos os timestamps em UTC


def validate_timestamp(ts: str) -> tuple:
    """
    Valida formato de timestamp.
    
    Returns:
        (is_valid: bool, error_message: str or None)
    """
    try:
        # Aceita com ou sem microssegundos e com ou sem Z
        ts_clean = ts.replace("Z", "+00:00")
        datetime.fromisoformat(ts_clean)
        return True, None
    except (ValueError, TypeError):
        return False, f"Invalid timestamp format: {ts}. Expected ISO8601 UTC."


# ═══════════════════════════════════════════════════════════════════════
# 6. PAYLOAD CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

# Regras para payloads:
# - NUNCA inclua senhas, tokens, ou chaves privadas
# - Dados sensíveis devem ser mascarados ou hasheados
# - Preferir IDs (UUIDs) sobre dados pessoais
# - Campos obrigatórios: sempre presentes
# - Campos opcionais: omitir quando null (não enviar null)

MAX_PAYLOAD_SIZE_BYTES = 256 * 1024  # 256KB


def validate_payload_size(payload: Dict[str, Any]) -> tuple:
    """
    Valida tamanho do payload.
    
    Returns:
        (is_valid: bool, size_bytes: int, error_message: str or None)
    """
    import json
    payload_str = json.dumps(payload)
    size = len(payload_str.encode("utf-8"))
    
    if size > MAX_PAYLOAD_SIZE_BYTES:
        return False, size, f"Payload exceeds {MAX_PAYLOAD_SIZE_BYTES} bytes: {size}"
    
    return True, size, None


# ═══════════════════════════════════════════════════════════════════════
# 7. AGGREGATE CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

# Todo evento deve referenciar um aggregate (entidade de domínio)
# Isso permite rastreamento e projections por entidade

VALID_AGGREGATE_TYPES = {
    "patient", "consultation", "evolution", "prescription",
    "document", "voice_session", "checkin", "room_event",
    "message", "invoice", "payment", "subscription",
    "session", "credential", "lgpd_request", "alert", "flow",
}


def validate_aggregate_type(agg_type: str) -> tuple:
    """
    Valida tipo de aggregate.
    
    Returns:
        (is_valid: bool, error_message: str or None)
    """
    if agg_type not in VALID_AGGREGATE_TYPES:
        return False, f"Invalid aggregate_type: {agg_type}. Valid: {sorted(VALID_AGGREGATE_TYPES)}"
    return True, None


# ═══════════════════════════════════════════════════════════════════════
# 8. PRIORITY CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

# Níveis de prioridade para processamento:
PRIORITY_NORMAL = 0   # Eventos assíncronos, não críticos
PRIORITY_HIGH = 1     # Eventos de negócio importantes
PRIORITY_CRITICAL = 2 # Eventos de segurança, pagamento, LGPD

PRIORITY_NAMES = {
    PRIORITY_NORMAL: "normal",
    PRIORITY_HIGH: "high",
    PRIORITY_CRITICAL: "critical",
}

# Eventos críticos por padrão:
CRITICAL_EVENT_TYPES = {
    "LOGIN_SUCCEEDED",
    "LOGIN_FAILED",
    "DATA_EXPORT_REQUESTED",
    "DATA_PURGED",
    "PAYMENT_RECEIVED",
    "PAYMENT_FAILED",
}


def get_default_priority(event_type: str) -> int:
    """Retorna prioridade padrão para um tipo de evento."""
    if event_type in CRITICAL_EVENT_TYPES:
        return PRIORITY_CRITICAL
    return PRIORITY_NORMAL


# ═══════════════════════════════════════════════════════════════════════
# 9. SOURCE CONVENTIONS
# ═══════════════════════════════════════════════════════════════════════

# Identificação da origem do evento:
VALID_SOURCES = {
    "siap",           # Flask backend principal
    "voice",          # Servidor de voz
    "smart_flow",     # Visual Smart Flow
    "concierge",      # IA Concierge
    "connect",        # Comunicação (WhatsApp, email)
    "knowledge",      # Knowledge base
    "audit",          # Sistema de auditoria
    "identity",       # Serviço de identidade
    "billing",        # Faturamento
    "integration",    # Integrações externas
    "gateway",        # API Gateway
    "mobile",         # App mobile
    "web",            # Frontend web
}


def validate_source(source: str) -> tuple:
    """
    Valida identificação de origem.
    
    Returns:
        (is_valid: bool, error_message: str or None)
    """
    if source not in VALID_SOURCES:
        return False, f"Invalid source: {source}. Valid: {sorted(VALID_SOURCES)}"
    return True, None
