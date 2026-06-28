"""P0-12 — tenant vem exclusivamente do JWT."""

path = 'middleware/tenant_middleware.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Use regex with flexible whitespace
import re

OLD_BLOCK = re.compile(
    r"            user_id = int\(identity\)\n\n"
    r"            # 1\. Try to get Association ID from Header.*?"
    r"                 # We don't block here, we let the route handle if it needs association\n",
    re.DOTALL,
)

NEW_BLOCK = '''            user_id = int(identity)

            # P0-12 (Missão 18): tenant vem EXCLUSIVAMENTE do JWT.
            # O header X-Association-ID NÃO é mais lido para escolher tenant.
            # Esse vetor permitia spoof cross-tenant (atacante enviava
            # X-Association-ID: <id_de_outra_assoc>).
            #
            # Ordem de resolução (somente JWT):
            #   1. role global == 'superadmin' → g.is_superadmin = True
            #   2. primeira UsuarioAssociacao ativa do profissional
            profissional = Profissional.query.get(user_id)
            if profissional:
                g.user_role = profissional.role
                if profissional.role == 'superadmin':
                    g.is_superadmin = True
                    g.current_association = None
                    return

            link = UsuarioAssociacao.query.filter_by(
                profissional_id=user_id, status='active'
            ).first()
            if link:
                g.current_association = link.associacao
                g.user_role = link.role
            else:
                g.current_association = None
'''

m = OLD_BLOCK.search(src)
assert m, "block not found"
src2 = src[:m.start()] + NEW_BLOCK + src[m.end():]
with open(path, 'w', encoding='utf-8') as f:
    f.write(src2)
print("OK middleware/tenant_middleware.py patched")

# 2. CORS — remover X-Association-ID
path = 'app_cors_livre.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

OLD_ALLOW = '''        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
            "X-Requested-With",
            "X-Association-ID",
        ],'''
NEW_ALLOW = '''        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
            "X-Requested-With",
            # P0-12: X-Association-ID REMOVIDO do CORS (bloqueia vetor spoof)
        ],'''
assert OLD_ALLOW in src, "CORS allow_headers not found"
src = src.replace(OLD_ALLOW, NEW_ALLOW)

OLD_EXPOSE = '''        expose_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
            "X-Association-ID",
        ],'''
NEW_EXPOSE = '''        expose_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
        ],'''
assert OLD_EXPOSE in src, "CORS expose_headers not found"
src = src.replace(OLD_EXPOSE, NEW_EXPOSE)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("OK app_cors_livre.py CORS hardened")
