"""Aplicar P0-04 — patch sanitize_input via raw bytes (sem depender de whitespace)."""
import re

path = 'security_config.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Encontrar o bloco inteiro pelo regex multiline.
PATTERN = re.compile(
    r'def sanitize_input\(data\):.*?return data\n',
    re.DOTALL,
)

NEW = '''# P0-04 (Missão 18): campos de senha NUNCA devem ser sanitizados.
# Sanitização que remove < > \' " ; quebra senhas com esses caracteres.
_PASSWORD_KEYS = frozenset({
    "senha",
    "password",
    "confirm_password",
    "new_password",
    "old_password",
    "senha_atual",
    "nova_senha",
    "current_password",
})


def sanitize_input(data):
    """
    Sanitiza dados de entrada para prevenir injeção em campos NÃO-credenciais.

    IMPORTANTE (P0-04): campos de senha NUNCA são sanitizados. Senhas com
    caracteres como < > \' " ; são válidas (o sanitize_input é projetado
    para remover XSS/SQLi de campos HTML, não de credenciais).

    Args:
        data: str, dict, list ou escalar a ser sanitizado

    Returns:
        Dados sanitizados (senhas pass-through intactas)
    """
    if isinstance(data, str):
        return re.sub(r\'[<>\\\'";]\', \'\', data)
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in _PASSWORD_KEYS:
                # Senha é preservada integralmente (pass-through)
                out[k] = v
            else:
                out[k] = sanitize_input(v)
        return out
    if isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data
'''

m = PATTERN.search(src)
assert m, "sanitize_input function not found"
src2 = src[:m.start()] + NEW + src[m.end():]
with open(path, 'w', encoding='utf-8') as f:
    f.write(src2)
print(f"OK: replaced {m.end()-m.start()} bytes with {len(NEW)} bytes")
