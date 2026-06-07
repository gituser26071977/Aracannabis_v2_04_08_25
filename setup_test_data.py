from app_cors_livre import create_app, db
from models import Profissional, Paciente
from models_extra import UsuarioAssociacao
from association.models import Associacao
from werkzeug.security import generate_password_hash
from datetime import datetime, date

app = create_app()

def create_data():
    with app.app_context():
        # 1. Create Superadmin
        superadmin_email = "abholzwarth@gmail.com"
        superadmin = Profissional.query.filter_by(email=superadmin_email).first()
        if not superadmin:
            print(f"Creating superadmin {superadmin_email}...")
            superadmin = Profissional(
                nome="Anderson Holzwarth",
                email=superadmin_email,
                usuario=superadmin_email,
                senha=generate_password_hash("Aracannabis@2025", method='pbkdf2:sha256:100000'),
                role='admin',
                crm="000000",
                uf_crm="SP",
                status_cadastro='aprovado',
                aprovado_por='system',
                data_aprovacao=datetime.utcnow()
            )
            db.session.add(superadmin)
            db.session.commit()
        else:
            print(f"Superadmin {superadmin_email} already exists. Updating role...")
            superadmin.role = 'admin'
            superadmin.senha = generate_password_hash("Aracannabis@2025", method='pbkdf2:sha256:100000')
            db.session.commit()

        # 2. Create Associations (Tenants)
        clinics = [
            {"name": "Clínica Holística", "slug": "clinica-holistica", "cnpj": "11111111000111"},
            {"name": "Centro de Terapia Canabinoide", "slug": "centro-terapia", "cnpj": "22222222000122"},
            {"name": "Instituto de Saúde Verde", "slug": "instituto-verde", "cnpj": "33333333000133"}
        ]

        created_doctors = []

        for i, clinic_data in enumerate(clinics):
            # Create Association
            assoc = Associacao.query.filter_by(slug=clinic_data["slug"]).first()
            if not assoc:
                print(f"Creating association {clinic_data['name']}...")
                assoc = Associacao(
                    nome=clinic_data["name"],
                    slug=clinic_data["slug"],
                    cnpj=clinic_data["cnpj"],
                    ativo=True
                )
                db.session.add(assoc)
                db.session.commit()
            
            # Create Doctor
            doc_email = f"medico{i+1}@teste.com"
            doctor = Profissional.query.filter_by(email=doc_email).first()
            if not doctor:
                print(f"Creating doctor {doc_email}...")
                doctor = Profissional(
                    nome=f"Dr. Teste {i+1}",
                    email=doc_email,
                    usuario=doc_email,
                    senha=generate_password_hash("Medico@123", method='pbkdf2:sha256:100000'),
                    role='profissional',
                    crm=f"1234{i}",
                    uf_crm="SP",
                    status_cadastro='aprovado',
                    aprovado_por=str(superadmin.id),
                    data_aprovacao=datetime.utcnow()
                )
                db.session.add(doctor)
                db.session.commit()
            
            created_doctors.append({"email": doc_email, "password": "Medico@123", "clinic": clinic_data["name"]})

            # Link Doctor to Association (as Admin of that association to see dashboard?)
            # Or just member. Let's make them admin of their clinic to verify "dashboard per tenant".
            link = UsuarioAssociacao.query.filter_by(profissional_id=doctor.id, associacao_id=assoc.id).first()
            if not link:
                print(f"Linking {doc_email} to {clinic_data['name']}...")
                link = UsuarioAssociacao(
                    profissional_id=doctor.id,
                    associacao_id=assoc.id,
                    role='admin', # Admin of their clinic
                    status='active'
                )
                db.session.add(link)
                db.session.commit()

            # Create Patients
            for j in range(3): # 3 patients per doctor
                pat_name = f"Paciente {j+1} da {clinic_data['name']}"
                patient = Paciente.query.filter_by(nome=pat_name).first()
                if not patient:
                    print(f"Creating patient {pat_name}...")
                    patient = Paciente(
                        nome=pat_name,
                        data_nascimento=date(1980+j, 1, 1),
                        cpf=f"{i}{j}000000000",
                        email=f"paciente{i}{j}@teste.com",
                        profissional_responsavel_id=doctor.id,
                        associacao_id=assoc.id, # Belongs to this tenant
                        em_tratamento=True
                    )
                    db.session.add(patient)
            db.session.commit()

        print("\n=== SYSTEM SETUP COMPLETE ===")
        print(f"Total Users: {Profissional.query.count()}")
        print(f"Total Associations: {Associacao.query.count()}")
        print(f"Total Patients: {Paciente.query.count()}")
        print("\n=== CREDENTIALS ===")
        print(f"Superadmin: {superadmin_email} / Aracannabis@2025")
        for doc in created_doctors:
            print(f"Doctor: {doc['email']} / {doc['password']} (Clinic: {doc['clinic']})")

if __name__ == "__main__":
    create_data()
