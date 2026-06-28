"""Aplicar P0-09 — remover skip_tenant=True com user input via regex."""
import re

# --- 1. routes/ai_chat_simples.py ---
path = 'routes/ai_chat_simples.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

# Patch 1: adicionar parâmetro profissional_id em buscar_contexto_paciente e validar acesso.
# Substituir: "def buscar_contexto_paciente(paciente_id):"
src = src.replace(
    "def buscar_contexto_paciente(paciente_id):",
    "def buscar_contexto_paciente(paciente_id, profissional_id):",
    1,
)

# Patch 2: injetar bloco de validação ANTES do stmt Paciente
OLD_STMT_BLOCK = """        # Usar select() com execution_options para bypass seguro do tenant filter
        stmt = select(Paciente).where(Paciente.id == paciente_id).execution_options(skip_tenant=True)
        paciente = db.session.execute(stmt).scalar_one_or_none()"""

NEW_STMT_BLOCK = """        # P0-09 (Missão 18): validar acesso do profissional ANTES de consultar
        # sem filtro de tenant. O profissional pode atuar em multi-associação;
        # mas cada paciente só pode ser acessado se ele for responsável ou
        # tiver compartilhamento ativo.
        try:
            from routes.pacientes import verificar_acesso_paciente
            tem_acesso, _, _ = verificar_acesso_paciente(profissional_id, paciente_id)
            if not tem_acesso:
                logger.warning(
                    "ai_chat.buscar_contexto: acesso negado user=%s paciente=%s",
                    profissional_id, paciente_id,
                )
                return None
        except Exception as _e:
            logger.error("ai_chat.buscar_contexto: erro de validação: %s", _e)
            return None

        # skip_tenant=True JUSTIFICADO: o profissional pode estar em
        # multi-associação e o paciente pode estar em outra associação
        # (compartilhamento). A autorização acima é obrigatória.
        stmt = select(Paciente).where(Paciente.id == paciente_id).execution_options(skip_tenant=True)
        paciente = db.session.execute(stmt).scalar_one_or_none()"""

assert OLD_STMT_BLOCK in src, "stmt block not found"
src = src.replace(OLD_STMT_BLOCK, NEW_STMT_BLOCK)

# Patch 3: passar profissional_id na chamada
src = src.replace(
    "contexto = buscar_contexto_paciente(paciente_id)",
    "contexto = buscar_contexto_paciente(paciente_id, current_user_id)",
    1,
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("OK routes/ai_chat_simples.py patched")

# --- 2. routes/pacientes.py — DOCUMENTAR usos legítimos ---
path = 'routes/pacientes.py'
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

OLD_DOC = '''def obter_pacientes_acessiveis(profissional_id):
    """
    Retorna query com pacientes que o profissional pode acessar
    """'''

NEW_DOC = '''def obter_pacientes_acessiveis(profissional_id):
    """
    Retorna query com pacientes que o profissional pode acessar.

    P0-09 (Missão 18): uso de skip_tenant=True DOCUMENTADO e JUSTIFICADO.

    Justificativa: o profissional pode atuar em MÚLTIPLAS Associações
    (multi-tenant por design da feature de compartilhamento de pacientes).
    A função aplica filtros manuais:
      1. role in {'admin', 'superadmin'} → vê tudo (skip_tenant=True)
      2. profissional_responsavel_id == profissional_id → seus pacientes
         mesmo em outra associação (skip_tenant=True)
      3. pacientes compartilhados via CompartilhamentoPaciente
         (skip_tenant=True — uniões cross-association são intencionais)
    """'''

assert OLD_DOC in src, "doc block not found"
src = src.replace(OLD_DOC, NEW_DOC)

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("OK routes/pacientes.py documented")
