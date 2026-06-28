"""Aplicar P0-06 — CSRF token obrigatório + compare_digest."""
import re

path = 'security_config.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

PATTERN = re.compile(
    r"def csrf_protect\(f\):.*?return decorated_function\n",
    re.DOTALL,
)

NEW_CSRF = '''def csrf_protect(f):
    """
    Decorator para proteção CSRF (P0-06 — Missão 18).

    Garantias:
      1. Token é obrigatório no header X-CSRF-Token (ou form field csrf_token).
      2. Token nunca pode ser comparado contra None:
         - se app.config["CSRF_TOKEN"] não estiver setado, ABORTA no startup
           (ver app_cors_livre.py: create_app chama _ensure_csrf_token()).
      3. Comparação via hmac.compare_digest (constant-time, anti timing-attack).
    """
    import hmac

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return f(*args, **kwargs)

        expected = current_app.config.get("CSRF_TOKEN")
        if not expected:
            # Fail closed: se a config está quebrada, recusa TUDO.
            current_app.logger.error(
                "csrf_protect: CSRF_TOKEN não configurado — abortando request"
            )
            return jsonify({"error": "CSRF misconfiguration"}), 503

        token = request.headers.get("X-CSRF-Token") or (
            request.form.get("csrf_token") if request.form else None
        )
        if not token:
            return jsonify({"error": "CSRF token ausente"}), 403

        if not hmac.compare_digest(str(token), str(expected)):
            return jsonify({"error": "CSRF token inválido"}), 403

        return f(*args, **kwargs)
    return decorated_function


def _ensure_csrf_token(app):
    """
    Garante que app.config["CSRF_TOKEN"] está setado em produção.
    Em produção ABORTA se não houver valor seguro.
    """
    import os
    token = app.config.get("CSRF_TOKEN")
    if token and len(str(token)) >= 32:
        return token

    is_prod = os.environ.get("ENVIRONMENT", "development").lower() in ("production", "prod")
    if is_prod:
        raise RuntimeError(
            "[SECURITY] CSRF_TOKEN ausente ou fraco. Defina um valor de "
            "pelo menos 32 caracteres antes de iniciar em produção."
        )
    # dev: gera placeholder aleatório
    import secrets as _secrets
    new_token = _secrets.token_hex(32)
    app.config["CSRF_TOKEN"] = new_token
    return new_token
'''

m = PATTERN.search(src)
assert m, "csrf_protect not found"
src2 = src[:m.start()] + NEW_CSRF + src[m.end():]
with open(path, 'w', encoding='utf-8') as f:
    f.write(src2)
print("OK csrf_protect hardened")
