from app_cors_livre import create_app
from models import db, Paciente, Profissional

app = create_app()
with app.app_context():
    total_pacientes = Paciente.query.count()
    print(f"Total de pacientes no banco: {total_pacientes}")
    
    if total_pacientes > 0:
        print("\nListando até 20 pacientes:")
        pacientes = Paciente.query.limit(20).all()
        for p in pacientes:
            resp = Profissional.query.get(p.profissional_responsavel_id)
            resp_nome = resp.nome if resp else f"ID {p.profissional_responsavel_id} (Não encontrado)"
            print(f"- Paciente: {p.nome} (ID: {p.id}) | Responsável: {resp_nome}")
    else:
        print("Nenhum paciente encontrado.")
