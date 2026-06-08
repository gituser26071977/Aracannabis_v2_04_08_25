#!/usr/bin/env python3
"""
ARAOS Week 11C — Demo Environment Setup
Cria Tenant Demo Cannabis + usuários + 30+ pacientes fictícios completos.
"""
import sys
import os
import random
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_cors_livre import create_app
from models import db, Profissional, Paciente, Sintoma, Dosagem, Evolucao, Consulta, Exame
from association.models import Associacao
from models_extra import UsuarioAssociacao

from faker import Faker

fake = Faker('pt_BR')
Faker.seed(42)
random.seed(42)

# ───────────────────────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────────────────────
TENANT_NAME = "Clínica Cannabis Demo"
TENANT_SLUG = "clinica-cannabis-demo"
TENANT_CNPJ = "12345678000199"

USERS = [
    {"nome": "Dr. Ricardo Almeida", "email": "medico@demo.cannabis", "role": "profissional", "crm": "DEMOMED01", "senha": "Medico@123"},
    {"nome": "Dra. Fernanda Costa", "email": "admin@demo.cannabis", "role": "admin", "crm": "DEMOADM01", "senha": "Admin@123"},
    {"nome": "Mariana Souza", "email": "secretaria@demo.cannabis", "role": "auxiliar", "crm": "DEMOAUX01", "senha": "Sec@123"},
]

CONDITIONS = [
    ("Dor Crônica", "dor_cronica"),
    ("Fibromialgia", "fibromialgia"),
    ("Ansiedade Generalizada", "ansiedade"),
    ("Insônia", "insonia"),
    ("TEA", "tea"),
    ("Epilepsia", "epilepsia"),
    ("Parkinson", "parkinson"),
    ("Dor Neuropática", "dor_neuropatica"),
]

PRODUCTS = [
    {"nome": "CBD 30mg/ml", "cbd": 30.0, "thc": 0.0, "cbg": 0.0, "cbn": 0.0},
    {"nome": "CBD 50mg/ml + THC 2mg/ml", "cbd": 50.0, "thc": 2.0, "cbg": 0.0, "cbn": 0.0},
    {"nome": "THC 10mg/ml", "cbd": 0.0, "thc": 10.0, "cbg": 0.0, "cbn": 0.0},
    {"nome": "Óleo Full Spectrum 100mg/ml", "cbd": 60.0, "thc": 5.0, "cbg": 15.0, "cbn": 5.0},
    {"nome": "CBG 20mg/ml", "cbd": 5.0, "thc": 0.0, "cbg": 20.0, "cbn": 0.0},
]

SYMPTOM_POOL = ["Dor", "Ansiedade", "Insônia", "Depressão", "Irritabilidade", "Falta de Apetite", "Náusea", "Espasticidade"]

app = create_app()


def create_tenant():
    tenant = Associacao.query.filter_by(slug=TENANT_SLUG).first()
    if tenant:
        print(f"ℹ️  Tenant já existe: {tenant.nome} (ID: {tenant.id})")
        return tenant
    tenant = Associacao(
        nome=TENANT_NAME,
        slug=TENANT_SLUG,
        cnpj=TENANT_CNPJ,
        email="contato@demo.cannabis",
        endereco="Rua das Flores, 420 — São Paulo, SP",
        telefone="(11) 99999-8888",
        ativo=True
    )
    db.session.add(tenant)
    db.session.commit()
    print(f"✅ Tenant criado: {tenant.nome} (ID: {tenant.id})")
    return tenant


def create_users(tenant):
    created = []
    for u in USERS:
        prof = Profissional.query.filter_by(email=u["email"]).first()
        if not prof:
            prof = Profissional(
                nome=u["nome"],
                email=u["email"],
                usuario=u["email"],
                senha=generate_password_hash(u["senha"], method='pbkdf2:sha256:100000'),
                role=u["role"],
                crm=u["crm"],
                uf_crm="SP",
                status_cadastro="aprovado",
                aprovado_por="system",
                data_aprovacao=datetime.utcnow(),
                email_verified=True,
                onboarding_completed=True,
            )
            db.session.add(prof)
            db.session.commit()
            print(f"✅ Usuário criado: {u['email']} ({u['role']})")
        else:
            print(f"ℹ️  Usuário já existe: {u['email']}")

        link = UsuarioAssociacao.query.filter_by(profissional_id=prof.id, associacao_id=tenant.id).first()
        if not link:
            link = UsuarioAssociacao(
                profissional_id=prof.id,
                associacao_id=tenant.id,
                role="admin" if u["role"] in ("admin", "profissional") else "member",
                status="active"
            )
            db.session.add(link)
            db.session.commit()
            print(f"   → Vinculado ao tenant como {link.role}")
        created.append(prof)
    return created


def generate_patient(tenant, doctor, index):
    cond_label, cond_code = random.choice(CONDITIONS)
    birth_date = fake.date_of_birth(minimum_age=18, maximum_age=75)
    patient = Paciente(
        nome=fake.name(),
        data_nascimento=birth_date,
        cpf=fake.cpf(),
        genero=random.choice(["Masculino", "Feminino", "Outro"]),
        telefone=fake.phone_number(),
        email=fake.email(),
        endereco=fake.address(),
        diagnostico=f"Paciente com {cond_label}. Histórico de sintomas crônicos. Iniciou tratamento com cannabis medicinal.",
        condicao_medica=cond_label,
        observacoes=fake.text(max_nb_chars=200),
        em_tratamento=True,
        profissional_responsavel_id=doctor.id,
        associacao_id=tenant.id,
        consentimento_lgpd=True,
        data_consentimento=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
    )
    db.session.add(patient)
    db.session.commit()
    return patient


def generate_symptoms(patient, days=180):
    """Gera registros de sintomas ao longo do tempo."""
    symptoms_for_condition = {
        "Dor Crônica": ["Dor", "Irritabilidade", "Falta de Apetite"],
        "Fibromialgia": ["Dor", "Insônia", "Depressão", "Ansiedade"],
        "Ansiedade Generalizada": ["Ansiedade", "Insônia", "Irritabilidade"],
        "Insônia": ["Insônia", "Ansiedade", "Irritabilidade"],
        "TEA": ["Ansiedade", "Irritabilidade", "Insônia"],
        "Epilepsia": ["Ansiedade", "Náusea", "Irritabilidade"],
        "Parkinson": ["Espasticidade", "Dor", "Depressão"],
        "Dor Neuropática": ["Dor", "Ansiedade", "Depressão"],
    }
    cond = patient.condicao_medica or "Dor Crônica"
    target_symptoms = symptoms_for_condition.get(cond, ["Dor", "Ansiedade"])

    records = []
    for day_offset in range(0, days, random.choice([3, 7, 14])):
        record_date = date.today() - timedelta(days=day_offset)
        for sym in target_symptoms:
            # Simula melhora gradual ao longo do tempo
            base_intensity = random.randint(3, 8)
            improvement = int(day_offset / days * 3)  # Melhora ~3 pontos em 6 meses
            intensity = max(1, min(10, base_intensity - improvement + random.randint(-1, 1)))
            records.append(Sintoma(
                paciente_id=patient.id,
                associacao_id=patient.associacao_id,
                data=record_date,
                sintoma=sym,
                intensidade=intensity
            ))
    db.session.add_all(records)
    db.session.commit()


def generate_dosages(patient, days=180):
    """Gera histórico de doses ao longo do tempo."""
    product = random.choice(PRODUCTS)
    records = []
    current_gotas = random.randint(3, 8)
    start_date = date.today() - timedelta(days=days)

    # 3 fases: titulação, estabilização, ajuste
    phases = [
        (0, 30, current_gotas),           # titulação
        (30, 120, current_gotas + 2),     # estabilização
        (120, days, current_gotas + 1),   # ajuste fino
    ]

    for start, end, gotas in phases:
        for day_offset in range(start, min(end, days), random.choice([1, 2, 3])):
            record_date = start_date + timedelta(days=day_offset)
            variation = random.randint(-1, 1)
            actual_gotas = max(1, gotas + variation)
            records.append(Dosagem(
                paciente_id=patient.id,
                associacao_id=patient.associacao_id,
                data=record_date,
                dosagem=product["nome"],
                gotas=actual_gotas,
                frequencia_diaria=random.choice([2, 3]),
                concentracao_cbd=product["cbd"],
                concentracao_thc=product["thc"],
                concentracao_cbg=product["cbg"],
                concentracao_cbn=product["cbn"],
                gotas_por_ml=30,
                tipo_dose="fixa",
                via_administracao=random.choice(["sublingual", "oral"]),
            ))
    db.session.add_all(records)
    db.session.commit()


def generate_evolutions(patient, count=8):
    """Gera notas de evolução clínica."""
    templates = [
        "Paciente relata melhora significativa nos sintomas. Continuar com dose atual.",
        "Paciente menciona sonolência excessiva. Reduzir dose noturna em 1 gota.",
        "Boa adesão ao tratamento. Nenhum efeito adverso relatado.",
        "Paciente relata redução de {x}% na dor. Satisfação alta.",
        "Reavaliação: sintomas estáveis. Manter esquema terapêutico.",
        "Paciente relatou náusea leve após aumento de dose. Ajustar para dose anterior.",
        "Consulta de retorno: paciente muito satisfeito. Melhora do sono e humor.",
        "Paciência em titulação. Dose atual bem tolerada. Agendar retorno em 30 dias.",
    ]
    records = []
    for i in range(count):
        evo_date = date.today() - timedelta(days=random.randint(7, 180))
        text = random.choice(templates).format(x=random.randint(30, 70))
        records.append(Evolucao(
            paciente_id=patient.id,
            profissional_id=patient.profissional_responsavel_id,
            associacao_id=patient.associacao_id,
            data_evolucao=datetime.combine(evo_date, datetime.min.time()),
            nota_evolucao=text,
        ))
    db.session.add_all(records)
    db.session.commit()


def generate_consultas(patient, count=6):
    """Gera consultas agendadas/realizadas."""
    statuses = ["realizada", "realizada", "realizada", "agendada", "cancelada", "realizada"]
    tipos = ["presencial", "presencial", "telemedicina"]
    records = []
    for i in range(count):
        consulta_date = datetime.now() - timedelta(days=random.randint(7, 180)) + timedelta(hours=random.randint(8, 17))
        records.append(Consulta(
            paciente_id=patient.id,
            profissional_id=patient.profissional_responsavel_id,
            associacao_id=patient.associacao_id,
            data_hora=consulta_date,
            tipo_consulta=random.choice(tipos),
            status=random.choice(statuses),
            observacoes=fake.text(max_nb_chars=100),
            duracao_minutos=random.choice([30, 45, 60]),
        ))
    db.session.add_all(records)
    db.session.commit()


def generate_exames(patient, count=4):
    """Gera exames laboratoriais."""
    exame_titles = ["Hemograma Completo", "Função Hepática", "Função Renal", "Colesterol Total", "Glicose", "TSH"]
    records = []
    for i in range(count):
        exame_date = date.today() - timedelta(days=random.randint(14, 120))
        titulo = random.choice(exame_titles)
        valor = round(random.uniform(50, 300), 2)
        records.append(Exame(
            paciente_id=patient.id,
            profissional_id=patient.profissional_responsavel_id,
            associacao_id=patient.associacao_id,
            data_exame=exame_date,
            titulo=titulo,
            tipo_exame="numerico",
            descricao=fake.text(max_nb_chars=150),
            valor=valor,
            unidade="mg/dL" if "Colesterol" in titulo or "Glicose" in titulo else "un",
            is_chartable=True,
        ))
    db.session.add_all(records)
    db.session.commit()


def main():
    with app.app_context():
        print("=" * 60)
        print("ARAOS Week 11C — Demo Environment Setup")
        print("=" * 60)

        tenant = create_tenant()
        users = create_users(tenant)
        doctor = next(u for u in users if u.role == "profissional")

        # Quantidade de pacientes existentes no tenant
        existing_count = Paciente.query.filter_by(associacao_id=tenant.id).count()
        target_total = 35
        to_create = target_total - existing_count

        if to_create <= 0:
            print(f"\nℹ️  Já existem {existing_count} pacientes no tenant. Nenhum novo criado.")
        else:
            print(f"\n🚀 Criando {to_create} pacientes fictícios...")
            for i in range(to_create):
                patient = generate_patient(tenant, doctor, i)
                generate_symptoms(patient)
                generate_dosages(patient)
                generate_evolutions(patient)
                generate_consultas(patient)
                generate_exames(patient)
                if (i + 1) % 5 == 0:
                    print(f"   → {i + 1}/{to_create} pacientes criados...")
            print(f"\n✅ {to_create} pacientes criados com dados completos!")

        final_count = Paciente.query.filter_by(associacao_id=tenant.id).count()
        print("\n" + "=" * 60)
        print("RESUMO DO AMBIENTE DEMO")
        print("=" * 60)
        print(f"Tenant: {tenant.nome} (ID: {tenant.id})")
        print(f"Pacientes: {final_count}")
        print(f"\nCredenciais:")
        for u in USERS:
            print(f"  {u['role']:15s} → {u['email']} / {u['senha']}")
        print("=" * 60)


if __name__ == "__main__":
    main()
