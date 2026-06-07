from app_cors_livre import create_app
from models import SolicitacoesCadastro

app = create_app()
with app.app_context():
    solicitacao = SolicitacoesCadastro.query.filter(SolicitacoesCadastro.nome.ilike('%Anderson%')).first()
    if solicitacao:
        print(f"Found request: ID={solicitacao.id}, Nome={solicitacao.nome}, Email={solicitacao.email}, Status={solicitacao.status}")
    else:
        print("No request found for Anderson.")
