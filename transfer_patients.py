from app_cors_livre import create_app
from models import db, Paciente, Profissional

app = create_app()
with app.app_context():
    # Find target user
    novo_dono = Profissional.query.filter_by(usuario='abholzwarth').first()
    if not novo_dono:
        print("User 'abholzwarth' not found!")
        exit(1)

    print(f"Target User Found: {novo_dono.nome} (ID: {novo_dono.id})")

    # Find patients belonging to Admin (assuming Admin is any other user or specifically ID 1/2)
    # Strategy: Move ALL patients that are NOT already owned by target user
    pacientes = Paciente.query.filter(Paciente.profissional_responsavel_id != novo_dono.id).all()
    
    count = 0
    for p in pacientes:
        old_id = p.profissional_responsavel_id
        p.profissional_responsavel_id = novo_dono.id
        print(f"Transferring patient '{p.nome}' (ID: {p.id}) from {old_id} to {novo_dono.id}")
        count += 1

    if count > 0:
        db.session.commit()
        print(f"\nSuccessfully transferred {count} patients to {novo_dono.usuario}.")
    else:
        print("\nNo patients needed transfer.")
