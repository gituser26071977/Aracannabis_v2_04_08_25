"""P0-11 — webhook hardening compare_digest."""
import hmac

path = 'middleware/webhook_auth.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Replace comparison to constant-time
OLD_DEV_CHECK = "if os.environ.get('FLASK_ENV') == 'development':"
NEW_DEV_CHECK = "if not is_production():"
assert OLD_DEV_CHECK in src, "dev check not found"
src = src.replace(OLD_DEV_CHECK, NEW_DEV_CHECK)

# Add is_production import
src = src.replace(
    "import os\nimport logging\n",
    "import os\nimport logging\nimport hmac as _hmac\nfrom config import is_production\n",
    1,
)

# Add the constant-time comparison helper at top
HELPER = '''

def _safe_compare(a: str, b: str) -> bool:
    """Comparação constant-time (anti timing-attack). P0-11."""
    if a is None or b is None:
        return False
    try:
        return _hmac.compare_digest(str(a), str(b))
    except Exception:
        return False
'''

src = src.replace(
    "logger = logging.getLogger(__name__)\n",
    "logger = logging.getLogger(__name__)\n" + HELPER,
    1,
)

# Replace direct != comparison with safe helper
OLD_EQ = "if provided_secret != webhook_secret:"
NEW_EQ = "if not _safe_compare(provided_secret, webhook_secret):"
assert OLD_EQ in src, "secret comparison not found"
src = src.replace(OLD_EQ, NEW_EQ)

# Patch verify_webhook_signature to validate input length first (DoS protection)
OLD_VERIFY = '''    # Comparação segura contra timing attacks
    return hmac.compare_digest(f"sha256={expected_signature}", signature)'''
NEW_VERIFY = '''    # Comparação segura contra timing attacks (P0-11)
    if not signature or len(signature) > 256:
        return False
    return hmac.compare_digest(f"sha256={expected_signature}", signature)'''
assert OLD_VERIFY in src, "verify signature block not found"
src = src.replace(OLD_VERIFY, NEW_VERIFY)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("OK middleware/webhook_auth.py patched")

# Also: services/webhook_auth.py (validate_mercadopago_signature, validate_generic_hmac_signature)
path = 'services/webhook_auth.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Just import hmac and ensure all comparisons use compare_digest
if 'compare_digest' not in src:
    # If service uses '!=' or '==' for signatures, replace with compare_digest
    print("WARN: compare_digest not found in services/webhook_auth.py — manual review required")
else:
    print("OK services/webhook_auth.py already uses compare_digest")
