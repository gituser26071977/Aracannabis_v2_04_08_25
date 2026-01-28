from app_cors_livre import create_app
from models import db, SolicitacoesCadastro

app = create_app()

with app.app_context():
    print("--- Limpando SolicitacoesCadastro ---")
    
    # Opção 1: Limpar tudo (mais simples para resetar o ambiente)
    deleted = SolicitacoesCadastro.query.delete()
    
    # Opção 2 (comentada): Limpar apenas o email específico
    # deleted = SolicitacoesCadastro.query.filter_by(email="ultrasson.unimed@gmail.com").delete()

    print(f"Registros removidos de SolicitacoesCadastro: {deleted}")
    
    db.session.commit()
    print("Commit realizado com sucesso.")
