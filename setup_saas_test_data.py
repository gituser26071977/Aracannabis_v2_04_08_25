from app_cors_livre import create_app
from models import db, Profissional
from association.models import Associacao
from models_extra import UsuarioAssociacao

def setup_test_data():
    app = create_app()
    with app.app_context():
        print("🛠️ Setting up SaaS Verification Data...")

        # 1. Create 'Clínica B'
        assoc_b = Associacao.query.filter_by(cnpj='99.999.999/0001-99').first()
        if not assoc_b:
            assoc_b = Associacao(
                nome="Clínica B - SaaS Test",
                slug="clinica-b",
                cnpj="99.999.999/0001-99",
                endereco="Rua Teste, 123",
                ativo=True
            )
            db.session.add(assoc_b)
            db.session.commit()
            print(f"✅ Created Association: {assoc_b.nome}")
        else:
            print(f"ℹ️ Association {assoc_b.nome} already exists.")

        # 2. Link Admin User (Assuming 'admin' or 'erick' or ID 1)
        # Let's try to find a user with role 'admin'
        admin_user = Profissional.query.filter(Profissional.role == 'admin').first()
        
        if not admin_user:
            # Fallback to ID 1
            admin_user = Profissional.query.get(1)
        
        if not admin_user:
            print("❌ No admin user found to link!")
            return

        print(f"👤 Found Admin User: {admin_user.nome} (ID: {admin_user.id})")

        # 3. Create Link
        link = UsuarioAssociacao.query.filter_by(
            profissional_id=admin_user.id,
            associacao_id=assoc_b.id
        ).first()

        if not link:
            link = UsuarioAssociacao(
                profissional_id=admin_user.id,
                associacao_id=assoc_b.id,
                role='admin',
                status='active'
            )
            db.session.add(link)
            db.session.commit()
            print("✅ Linked Admin to Clínica B.")
        else:
            print("ℹ️ Admin already linked to Clínica B.")

        print("🚀 Setup Complete! Refresh your browser to see the dropdown.")

if __name__ == '__main__':
    setup_test_data()
