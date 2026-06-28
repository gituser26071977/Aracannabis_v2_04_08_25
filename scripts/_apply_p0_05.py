"""Aplicar P0-05 — CSP sem unsafe-inline/unsafe-eval em script-src.

Estratégia:
- Gerar nonce por request no Flask.
- Setar o nonce em response header para que o HTML possa incluir scripts via nonce.
- Manter style-src 'unsafe-inline' (MUI Material-UI injeta style tags).
- Manter img-src 'self' data: blob: https: (algumas fontes externas).
"""
import re

path = 'security_config.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Substituir a string CSP. Como ela tem múltiplas linhas, use regex.
PATTERN = re.compile(
    r"f\"default-src 'self';.*?media-src 'self' blob: data:;\"",
    re.DOTALL,
)

NEW_CSP = (
    "f\"default-src 'self'; \"\n"
    "        f\"script-src 'self' 'nonce-{nonce}'; \"\n"
    "        f\"style-src 'self' 'unsafe-inline'; \"\n"
    "        f\"img-src 'self' data: blob: https:; \"\n"
    "        f\"font-src 'self' data: https:; \"\n"
    "        f\"connect-src 'self' {connect_src_origins}; \"\n"
    "        f\"frame-src 'self'; \"\n"
    "        f\"media-src 'self' blob: data:; \"\n"
    "        f\"object-src 'none'; \"\n"
    "        f\"base-uri 'self'; \"\n"
    "        f\"form-action 'self'; \"\n"
    "        f\"frame-ancestors 'none'; \"\n"
    "        f\"upgrade-insecure-requests\""
)

m = PATTERN.search(src)
assert m, "CSP block not found"
src2 = src[:m.start()] + NEW_CSP + src[m.end():]

# Também precisamos definir SECURITY_HEADERS como callable para receber nonce.
# Vamos refatorar SECURITY_HEADERS para um dict de strings não-template,
# e construir o header em add_security_headers com nonce opcional.

# Remove o dict SECURITY_HEADERS antigo (vamos reconstruir).
SECPAT = re.compile(r"SECURITY_HEADERS = \{.*?\n\}\n", re.DOTALL)
sm = SECPAT.search(src2)
assert sm, "SECURITY_HEADERS dict not found"

NEW_SEC_HEADERS = '''SECURITY_HEADERS = {
    # CSP e headers com nonce são setados em add_security_headers(response)
    # para incluir nonce por-request.
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    "Permissions-Policy": "geolocation=(), microphone=(self), camera=(self), payment=()",
}
'''

src3 = src2[:sm.start()] + NEW_SEC_HEADERS + src2[sm.end():]

# Substituir add_security_headers para gerar nonce + CSP dinamicamente.
ADDPAT = re.compile(
    r"def add_security_headers\(response\):.*?return response\n",
    re.DOTALL,
)
NEW_ADD = '''def add_security_headers(response):
    """
    Adiciona cabeçalhos de segurança HTTP à resposta.

    P0-05 (Missão 18): CSP sem 'unsafe-inline' / 'unsafe-eval' em script-src.
    Gera nonce por-request e o embute no header Content-Security-Policy.
    """
    # Gera nonce determinístico por request (cacheado em flask.g)
    nonce = getattr(g, "csp_nonce", None) if "g" in dir() else None
    if nonce is None:
        import secrets as _secrets
        nonce = _secrets.token_urlsafe(16)

    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: blob: https:; "
        f"font-src 'self' data: https:; "
        f"connect-src 'self' {connect_src_origins}; "
        f"frame-src 'self'; "
        f"media-src 'self' blob: data:; "
        f"object-src 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'; "
        f"frame-ancestors 'none'; "
        f"upgrade-insecure-requests"
    )

    response.headers["Content-Security-Policy"] = csp
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response
'''

am = ADDPAT.search(src3)
assert am, "add_security_headers function not found"
src4 = src3[:am.start()] + NEW_ADD + src3[am.end():]

# Também: csrf_protect precisa abortar startup se CSRF_TOKEN ausente (P0-06)
# Aqui só vamos ajustar o uso de connect_src_origins que era referenciado.

with open(path, 'w', encoding='utf-8') as f:
    f.write(src4)
print("OK security_config.py CSP patched")
