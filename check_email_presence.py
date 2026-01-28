from app_cors_livre import create_app
from models import db, Profissional, SolicitacoesCadastro

app = create_app()

target_email = "ultrasson.unimed@gmail.com"

with app.app_context():
    print(f"--- Investigando email: {target_email} ---")
    
    # 1. Check Profissionais
    prof = Profissional.query.filter_by(email=target_email).first()
    if prof:
        print(f"⚠️ ENCONTRADO em 'Profissional': ID={prof.id}, Nome='{prof.nome}', Usuario='{prof.usuario}'")
    else:
        print("✅ NÃO encontrado em 'Profissional'")

    # 2. Check SolicitacoesCadastro
    try:
        solic = SolicitacoesCadastro.query.filter_by(email=target_email).first()
        if solic:
            print(f"⚠️ ENCONTRADO em 'SolicitacoesCadastro': ID={solic.id}, Status='{solic.status}', Nome='{solic.nome}'")
        else:
            print("✅ NÃO encontrado em 'SolicitacoesCadastro'")
    except Exception as e:
        print(f"Erro ao verificar SolicitacoesCadastro: {e}")

    # 3. Check Admin/User details just in case
    print("\n--- Usuários Atuais ---")
    users = Profissional.query.all()
    for u in users:
        print(f"ID={u.id}, User={u.usuario}, Email={u.email}")
