"""
SIAP Homologation Dataset Generator — API-1B

Gera dataset sintético completo para homologação do MeshOS + SIAP.
3 médicos × 5 pacientes = 15 pacientes com histórico clínico completo.

Usage:
    cd /home/holzwarth/Projetos/Aracannabis_SO/Aracannabis_SIAP
    .venv/bin/python scripts/homologation/dataset_generator.py
"""

import requests
import json
import random
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
import time
import psycopg2

# ───────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────
BASE_URL = "http://localhost:5002"
ADMIN_USER = "admin"
ADMIN_PASS = "Aracannabis@2025"

# Médicos sintéticos
PHYSICIANS = [
    {
        "nome": "Dra. Helena Marques",
        "crm": "123456",
        "uf_crm": "SP",
        "usuario": "helena.cannabis",
        "senha": "Teste@123456",
        "email": "helena.cannabis@siap.test",
        "especialidade": "Cannabis Medicinal",
        "clinica": "Centro de Cannabis Medicinal São Paulo",
        "perfil": "Especialista em cannabis medicinal com 12 anos de experiência. Focada em dor crônica, fibromialgia e neurologia.",
    },
    {
        "nome": "Dr. Ricardo Oliveira",
        "crm": "234567",
        "uf_crm": "RJ",
        "usuario": "ricardo.dor",
        "senha": "Teste@123456",
        "email": "ricardo.dor@siap.test",
        "especialidade": "Medicina da Dor",
        "clinica": "Instituto de Dor e Reabilitação Rio",
        "perfil": "Médico da dor com pós-doutorado em neurofisiologia. Especialista em manejo multidisciplinar de dor crônica refratária.",
    },
    {
        "nome": "Dra. Fernanda Costa",
        "crm": "345678",
        "uf_crm": "MG",
        "usuario": "fernanda.neuro",
        "senha": "Teste@123456",
        "email": "fernanda.neuro@siap.test",
        "especialidade": "Neurologia",
        "clinica": "Neuroclínica Minas",
        "perfil": "Neurologista com subespecialização em epilepsia e distúrbios do movimento. Pesquisadora em cannabis para condições neurológicas.",
    },
]

# ───────────────────────────────────────────────
# SYNTHETIC PATIENT DATA
# ───────────────────────────────────────────────
FIRST_NAMES_F = ["Ana", "Maria", "Juliana", "Fernanda", "Carolina", "Beatriz", "Larissa", "Patrícia", "Camila", "Isabela", "Luísa", "Mariana", "Tatiane", "Vanessa", "Roberta"]
FIRST_NAMES_M = ["João", "Carlos", "Pedro", "Lucas", "Marcelo", "André", "Bruno", "Felipe", "Gustavo", "Ricardo", "Daniel", "Alexandre", "Rodrigo", "Fernando", "Eduardo"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Rodrigues", "Almeida", "Ferreira", "Barbosa", "Ribeiro", "Gomes", "Martins", "Araújo", "Cardoso", "Teixeira", "Melo", "Dias", "Castro"]

CITIES = ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Porto Alegre", "Salvador", "Brasília", "Recife", "Fortaleza", "Manaus"]
OCCUPATIONS = ["Professora", "Engenheira", "Advogada", "Designer", "Enfermeira", "Contadora", "Psicóloga", "Administradora", "Estudante", "Aposentada", "Autônoma", "Vendedora", "Técnica de Enfermagem", "Assistente Social", "Farmacêutica"]

CLINICAL_CONDITIONS = [
    {"nome": "Endometriose", "sintomas_principais": ["Dor pélvica crônica", "Dispareunia", "Dismenorreia severa"], "sintomas_secundarios": ["Náusea", "Fadiga", "Irritabilidade"]},
    {"nome": "Fibromialgia", "sintomas_principais": ["Dor musculoesquelética difusa", "Pontos dolorosos", "Fadiga persistente"], "sintomas_secundarios": ["Insônia", "Cefaleia", "Nevoeiro mental"]},
    {"nome": "Insônia Crônica", "sintomas_principais": ["Dificuldade para iniciar sono", "Despertares noturnos", "Sono não restaurador"], "sintomas_secundarios": ["Sonolência diurna", "Irritabilidade", "Dificuldade de concentração"]},
    {"nome": "Transtorno de Ansiedade Generalizada", "sintomas_principais": ["Preocupação excessiva", "Inquietação motora", "Tensão muscular"], "sintomas_secundarios": ["Irritabilidade", "Fadiga", "Dificuldade de concentração"]},
    {"nome": "Dor Crônica", "sintomas_principais": ["Dor lombar persistente", "Dor irradiada", "Rigidez matinal"], "sintomas_secundarios": ["Limitação funcional", "Humor deprimido", "Distúrbio do sono"]},
    {"nome": "Dor Neuropática", "sintomas_principais": ["Dor em queimação", "Parestesia", "Alodinia"], "sintomas_secundarios": ["Dormência", "Formigamento", "Dor noturna"]},
    {"nome": "Enxaqueca", "sintomas_principais": ["Cefaleia pulsátil unilateral", "Fotofobia", "Fonofobia"], "sintomas_secundarios": ["Náusea", "Vômito", "Aura visual"]},
    {"nome": "TEPT", "sintomas_principais": ["Flashbacks intrusivos", "Evitação", "Hipervigilância"], "sintomas_secundarios": ["Pesadelos", "Irritabilidade", "Insônia"]},
    {"nome": "Distúrbio do Pânico", "sintomas_principais": ["Crises de pânico", "Palpitações", "Dispneia"], "sintomas_secundarios": ["Sudorese", "Tremores", "Sensação de morte iminente"]},
    {"nome": "Esclerose Múltipla", "sintomas_principais": ["Fraqueza motora", "Espasticidade", "Dor neuropática"], "sintomas_secundarios": ["Fadiga", "Distúrbios vesicais", "Nistagmo"]},
    {"nome": "Neuropatia Periférica", "sintomas_principais": ["Dor em queimação distal", "Parestesia", "Hipoestesia"], "sintomas_secundarios": ["Dificuldade de marcha", "Dor noturna", "Atrofia muscular"]},
    {"nome": "Artrose", "sintomas_principais": ["Dor articular mecânica", "Rigidez", "Limitação de movimento"], "sintomas_secundarios": ["Crepitação", "Edema articular", "Deformidade"]},
    {"nome": "Dor Lombar Crônica", "sintomas_principais": ["Dor lombar mecânica", "Dor ciática", "Rigidez"], "sintomas_secundarios": ["Limitação funcional", "Espasmo muscular", "Postura alterada"]},
    {"nome": "TDAH", "sintomas_principais": ["Desatenção", "Hiperatividade", "Impulsividade"], "sintomas_secundarios": ["Dificuldade organizacional", "Esquecimentos", "Frustração"]},
    {"nome": "TEA", "sintomas_principais": ["Dificuldade de interação social", "Comportamentos repetitivos", "Hipersensibilidade sensorial"], "sintomas_secundarios": ["Ansiedade social", "Dificuldade de comunicação", "Ritualização"]},
]

CANNABIS_PRODUCTS = [
    {"nome": "CBD 20% 30ml", "cbd_mg_ml": 200, "thc_mg_ml": 0, "via": "Sublingual"},
    {"nome": "THC 5% 30ml", "cbd_mg_ml": 0, "thc_mg_ml": 50, "via": "Sublingual"},
    {"nome": "CBD 10% + THC 2% 30ml", "cbd_mg_ml": 100, "thc_mg_ml": 20, "via": "Sublingual"},
    {"nome": "CBD 15% 30ml", "cbd_mg_ml": 150, "thc_mg_ml": 0, "via": "Sublingual"},
    {"nome": "THC 10% 30ml", "cbd_mg_ml": 0, "thc_mg_ml": 100, "via": "Sublingual"},
    {"nome": "CBD 5% + THC 5% 30ml", "cbd_mg_ml": 50, "thc_mg_ml": 50, "via": "Sublingual"},
    {"nome": "CBD 30% 10ml", "cbd_mg_ml": 300, "thc_mg_ml": 0, "via": "Sublingual"},
    {"nome": "Óleo 1:1 CBD:THC 30ml", "cbd_mg_ml": 100, "thc_mg_ml": 100, "via": "Sublingual"},
]

EXAM_TEMPLATES = [
    {"titulo": "Hemograma Completo", "tipo": "texto", "descricao_modelo": "Hemácias: {} milhões/µL, Leucócitos: {} mil/µL, Plaquetas: {} mil/µL, Hemoglobina: {} g/dL, Hematócrito: {}%. Observação: {}"},
    {"titulo": "Função Hepática (TGO/TGP)", "tipo": "texto", "descricao_modelo": "TGO (AST): {} U/L, TGP (ALT): {} U/L, Gama-GT: {} U/L, FA: {} U/L, Bilirrubina total: {} mg/dL. Observação: {}"},
    {"titulo": "Função Renal (Creatinina/Uréia)", "tipo": "texto", "descricao_modelo": "Creatinina: {} mg/dL, Ureia: {} mg/dL, Ácido Úrico: {} mg/dL, TFG: {} mL/min. Observação: {}"},
    {"titulo": "Perfil Lipídico", "tipo": "texto", "descricao_modelo": "Colesterol total: {} mg/dL, HDL: {} mg/dL, LDL: {} mg/dL, Triglicerídeos: {} mg/dL, VLDL: {} mg/dL. Observação: {}"},
    {"titulo": "Vitamina D (25-OH)", "tipo": "numerico", "unidade": "ng/mL", "valor_min": 15, "valor_max": 60},
    {"titulo": "Perfil Tireoidiano (TSH/T4L)", "tipo": "texto", "descricao_modelo": "TSH: {} µUI/mL, T4 Livre: {} ng/dL, T3 Livre: {} pg/mL. Observação: {}"},
    {"titulo": "HbA1c (Hemoglobina Glicada)", "tipo": "numerico", "unidade": "%", "valor_min": 4.5, "valor_max": 9.0},
    {"titulo": "Ferro Sérico e Ferritina", "tipo": "texto", "descricao_modelo": "Ferro sérico: {} µg/dL, Ferritina: {} ng/mL, Transferrina: {} mg/dL, Sat. transferrina: {}%. Observação: {}"},
    {"titulo": "Eletroforese de Hemoglobina", "tipo": "texto", "descricao_modelo": "HbA: {}%, HbA2: {}%, HbF: {}%, HbS: ausente. Observação: {}"},
    {"titulo": "Exame de Urina (EAS)", "tipo": "texto", "descricao_modelo": "Aspecto: {}, pH: {}, Densidade: {}, Leucócitos: {}, Hemácias: {}. Observação: {}"},
    {"titulo": "Proteína C Reativa (PCR)", "tipo": "numerico", "unidade": "mg/L", "valor_min": 0.1, "valor_max": 15},
    {"titulo": "Hemoglobina Glicada", "tipo": "numerico", "unidade": "%", "valor_min": 4.0, "valor_max": 10.0},
]

# ───────────────────────────────────────────────
# API CLIENT
# ───────────────────────────────────────────────

class SIAPClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}

    def login(self, usuario: str, senha: str) -> bool:
        """Autentica e obtém JWT token."""
        resp = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"usuario": usuario, "senha": senha},
            headers=self.headers
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.headers["Authorization"] = f"Bearer {self.token}"
            return True
        print(f"[LOGIN FAIL] {usuario}: {resp.status_code} {resp.text[:200]}")
        return False

    def post_json(self, path: str, payload: Dict) -> Optional[Dict]:
        """POST com JSON e retorno padronizado."""
        resp = requests.post(f"{self.base_url}{path}", json=payload, headers=self.headers)
        if resp.status_code in (200, 201):
            return resp.json()
        print(f"[POST FAIL] {path}: {resp.status_code} {resp.text[:300]}")
        return None

    def post_form(self, path: str, data: Dict) -> Optional[Dict]:
        """POST com form-data (sem Content-Type para deixar requests definir)."""
        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
        resp = requests.post(f"{self.base_url}{path}", data=data, headers=headers)
        if resp.status_code in (200, 201):
            return resp.json()
        print(f"[POST FORM FAIL] {path}: {resp.status_code} {resp.text[:300]}")
        return None

    def get_json(self, path: str) -> Optional[Dict]:
        resp = requests.get(f"{self.base_url}{path}", headers=self.headers)
        if resp.status_code == 200:
            return resp.json()
        return None


# ───────────────────────────────────────────────
# GENERATOR UTILITIES
# ───────────────────────────────────────────────

def random_date(start: date, end: date) -> date:
    """Retorna data aleatória entre start e end."""
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generate_cpf() -> str:
    """Gera CPF sintético válido (apenas formato)."""
    nums = [random.randint(0, 9) for _ in range(9)]
    # Dígito 1
    d1 = sum((10 - i) * n for i, n in enumerate(nums)) % 11
    d1 = 0 if d1 < 2 else 11 - d1
    nums.append(d1)
    # Dígito 2
    d2 = sum((11 - i) * n for i, n in enumerate(nums)) % 11
    d2 = 0 if d2 < 2 else 11 - d2
    nums.append(d2)
    return "".join(str(n) for n in nums)


def generate_patient_name(gender: str) -> str:
    first = random.choice(FIRST_NAMES_F if gender == "F" else FIRST_NAMES_M)
    last1 = random.choice(LAST_NAMES)
    last2 = random.choice(LAST_NAMES)
    return f"{first} {last1} {last2}"


def generate_patient(physician_id: int, physician_specialty: str, patient_index: int) -> Dict:
    """Gera um paciente sintético completo."""
    gender = random.choice(["F", "M"])
    nome = generate_patient_name(gender)
    birth = random_date(date(1960, 1, 1), date(1995, 12, 31))
    age = (date.today() - birth).days // 365

    # Atribuir 1-3 condições clínicas
    num_conditions = random.choices([1, 2, 3], weights=[40, 45, 15])[0]
    conditions = random.sample(CLINICAL_CONDITIONS, num_conditions)

    # Gerar sintomas com severidade
    symptoms = []
    for cond in conditions:
        for sp in cond["sintomas_principais"]:
            symptoms.append({
                "sintoma": sp,
                "intensidade": random.randint(5, 10),
                "origem": cond["nome"],
                "tipo": "principal"
            })
        for ss in cond["sintomas_secundarios"]:
            symptoms.append({
                "sintoma": ss,
                "intensidade": random.randint(3, 7),
                "origem": cond["nome"],
                "tipo": "secundario"
            })

    # Histórico de medicação
    failed_meds = random.sample([
        "Amitriptilina", "Pregabalina", "Duloxetina", "Tramadol", "Gabapentina",
        "Carbamazepina", "Clonazepam", "Sertralina", "Fluoxetina", "Venlafaxina",
        "Oxcarbazepina", "Topiramato", "Nortriptilina", "Ciclobenzaprina"
    ], k=random.randint(2, 5))

    failed_reasons = {
        "Amitriptilina": "Efeitos anticolinérgicos intoleráveis (boca seca, constipação)",
        "Pregabalina": "Ganho de peso excessivo e edema periférico",
        "Duloxetina": "Náuseas persistentes e insônia",
        "Tramadol": "Dependência e tolerância rápida",
        "Gabapentina": "Sonolência excessiva e tontura",
        "Carbamazepina": "Hepatotoxicidade e rash cutâneo",
        "Clonazepam": "Sedação diurna e dependência",
        "Sertralina": "Disfunção sexual e tremores",
        "Fluoxetina": "Insônia e agitação",
        "Venlafaxina": "Hipertensão e sudorese excessiva",
        "Oxcarbazepina": "Hiponatremia e rash",
        "Topiramato": "Cognição prejudicada e perda de peso",
        "Nortriptilina": "Taquecardia e boca seca",
        "Ciclobenzaprina": "Sedação excessiva"
    }

    med_history = []
    for med in failed_meds:
        med_history.append({
            "medicamento": med,
            "motivo_falha": failed_reasons.get(med, "Efeitos colaterais intoleráveis"),
            "duracao_meses": random.randint(3, 24),
            "eficacia": random.randint(1, 4)
        })

    # Protocolo cannabis
    selected_products = random.sample(CANNABIS_PRODUCTS, k=random.randint(2, 4))
    cannabis_protocol = []
    for prod in selected_products:
        gotas = random.choice([2, 3, 4, 5, 6])
        freq = random.choice([2, 3])
        cannabis_protocol.append({
            "produto": prod,
            "gotas": gotas,
            "frequencia_diaria": freq,
            "posologia_texto": f"{gotas} gotas, {freq} vezes ao dia",
            "titulacao": f"Iniciar com {gotas-1} gotas por 7 dias, aumentar gradualmente até {gotas+1} gotas conforme tolerância",
            "meta_tratamento": random.choice([
                "Redução de 50% na intensidade da dor",
                "Melhora do sono (mínimo 6h contínuas)",
                "Redução da frequência de crises",
                "Melhora da funcionalidade diária",
                "Redução do uso de opioides"
            ])
        })

    # Gerar evoluções (timeline: D0, D30, D60, D90, D180)
    base_date = date.today() - timedelta(days=200)
    evolution_dates = [
        base_date,
        base_date + timedelta(days=30),
        base_date + timedelta(days=60),
        base_date + timedelta(days=90),
        base_date + timedelta(days=180),
    ]

    # Gerar exames
    selected_exams = random.sample(EXAM_TEMPLATES, k=5)

    return {
        "nome": nome,
        "data_nascimento": birth.strftime("%Y-%m-%d"),
        "genero": "Feminino" if gender == "F" else "Masculino",
        "cpf": generate_cpf(),
        "telefone": f"11{random.randint(900000000, 999999999)}",
        "email": f"paciente{patient_index}@siap.test",
        "endereco": f"Rua {random.choice(['das Flores', 'das Acácias', 'dos Ipês', 'Principa', 'Brasil'])}, {random.randint(100, 9999)}, {random.choice(CITIES)}",
        "diagnostico": "; ".join(c["nome"] for c in conditions),
        "observacoes": f"Paciente encaminhado por {physician_specialty}. Histórico de {len(failed_meds)} falhas medicamentosas.",
        "em_tratamento": True,
        "peso_kg": round(random.uniform(55, 95), 1),
        "altura_cm": random.randint(155, 185),
        "imc": None,  # calculado depois
        "ocupacao": random.choice(OCCUPATIONS),
        "cidade": random.choice(CITIES),
        "estado_civil": random.choice(["Solteira", "Casada", "Divorciada", "Viúva"]),
        "escolaridade": random.choice(["Ensino Médio", "Superior Completo", "Pós-Graduação", "Mestrado"]),
        "condicoes": conditions,
        "sintomas": symptoms,
        "historico_medicacao": med_history,
        "protocolo_cannabis": cannabis_protocol,
        "evolucao_datas": evolution_dates,
        "exames": selected_exams,
    }


def build_evolution_text(patient: Dict, visit_num: int, visit_date: date) -> str:
    """Constrói texto de evolução clínica sintética."""
    condition = patient["condicoes"][0]["nome"]
    pain_scores = [8, 6, 5, 4, 3]
    sleep_scores = [3, 4, 5, 6, 7]
    anxiety_scores = [7, 6, 5, 4, 3]

    pain = pain_scores[visit_num]
    sleep = sleep_scores[visit_num]
    anxiety = anxiety_scores[visit_num]

    side_effects_options = [
        "Nenhum efeito colateral relatado.",
        "Leve boca seca no início, resolvida com hidratação.",
        "Sonolência leve nas primeiras 2 semanas, melhorando.",
        "Náusea leve transitória, sem necessidade de intervenção.",
        "Tontura ocasional ao aumentar a dose, já estabilizada."
    ]

    adherence = ["Iniciou tratamento conforme orientado.",
                 "Adesão boa, utilizando conforme prescrição.",
                 "Adesão excelente, relatou melhora significativa.",
                 "Continua em uso regular, mantém benefício.",
                 "Tratamento estabilizado, benefício mantido."][visit_num]

    assessments = [
        f"Primeira avaliação. Paciente com {condition}, dor {pain}/10. Iniciado protocolo de cannabis medicinal.",
        f"Retorno em 30 dias. Dor reduziu para {pain}/10. Sono melhorou ({sleep}/10). Ansiedade {anxiety}/10. {side_effects_options[visit_num]}",
        f"Retorno em 60 dias. Evolução favorável. Dor {pain}/10. Qualidade do sono em {sleep}/10. {adherence}",
        f"Retorno em 90 dias. Paciente relatando melhora funcional. Dor {pain}/10. {side_effects_options[visit_num]} {adherence}",
        f"Retorno em 180 dias. Tratamento estabilizado. Dor basal {pain}/10. Sono restaurado ({sleep}/10). Manter protocolo atual."
    ]

    return assessments[visit_num]


# ───────────────────────────────────────────────
# INSERTION FUNCTIONS
# ───────────────────────────────────────────────

def get_physician_id_by_email(email: str) -> Optional[int]:
    """Busca ID do profissional pelo email direto no banco."""
    try:
        conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5434/aracannabis')
        cur = conn.cursor()
        cur.execute("SELECT id FROM profissionais WHERE email = %s", (email,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"  [DB ERROR] {e}")
        return None


def create_physician(client: SIAPClient, physician: Dict) -> Optional[int]:
    """Cria médico via API de registro."""
    payload = {
        "nome": physician["nome"],
        "crm": physician["crm"],
        "uf_crm": physician["uf_crm"],
        "usuario": physician["usuario"],
        "senha": physician["senha"],
        "email": physician["email"],
    }
    resp = client.post_json("/api/auth/register", payload)
    if resp and "profissional" in resp:
        pid = resp["profissional"].get("id")
        print(f"  [+] Médico criado: {physician['nome']} (ID: {pid})")
        return pid
    # Se já existir, buscar ID no banco
    pid = get_physician_id_by_email(physician["email"])
    if pid:
        print(f"  [=] Médico já existia: {physician['nome']} (ID: {pid})")
        return pid
    return None


def create_patient(client: SIAPClient, patient_data: Dict) -> Optional[int]:
    """Cria paciente via API."""
    payload = {
        "nome": patient_data["nome"],
        "data_nascimento": patient_data["data_nascimento"],
        "cpf": patient_data["cpf"],
        "genero": patient_data["genero"],
        "telefone": patient_data["telefone"],
        "email": patient_data["email"],
        "endereco": patient_data["endereco"],
        "diagnostico": patient_data["diagnostico"],
        "observacoes": patient_data["observacoes"],
        "em_tratamento": patient_data["em_tratamento"],
    }
    resp = client.post_json("/api/pacientes/", payload)
    if resp and "paciente" in resp:
        pid = resp["paciente"].get("id")
        print(f"    [+] Paciente criado: {patient_data['nome']} (ID: {pid})")
        return pid
    return None


def create_symptom(client: SIAPClient, paciente_id: int, symptom: Dict, data_str: str) -> bool:
    """Cria sintoma via API."""
    payload = {
        "data": data_str,
        "sintoma": symptom["sintoma"],
        "intensidade": symptom["intensidade"],
        "observacoes": f"Sintoma {symptom['tipo']} relacionado a {symptom['origem']}. Escala 0-10."
    }
    resp = client.post_json(f"/api/sintomas/paciente/{paciente_id}", payload)
    return resp is not None


def create_dosage(client: SIAPClient, paciente_id: int, protocol: Dict, data_str: str) -> bool:
    """Cria dosagem (medicação) via API."""
    prod = protocol["produto"]
    payload = {
        "data": data_str,
        "dosagem": prod["nome"],
        "via_administracao": prod["via"],
        "gotas": protocol["gotas"],
        "frequencia_diaria": protocol["frequencia_diaria"],
        "concentracao_cbd": prod["cbd_mg_ml"] * 30,  # total mg no frasco
        "concentracao_thc": prod["thc_mg_ml"] * 30,
        "instrucoes_uso": protocol["posologia_texto"] + " | " + protocol["titulacao"],
        "observacoes": protocol["meta_tratamento"]
    }
    resp = client.post_json(f"/api/dosagens/paciente/{paciente_id}", payload)
    return resp is not None


def create_evolution(client: SIAPClient, paciente_id: int, text: str, data_str: str) -> bool:
    """Cria evolução via API."""
    payload = {
        "nota_evolucao": text,
        "data_evolucao": data_str,
        "use_ai_processing": False
    }
    resp = client.post_json(f"/api/evolucoes/paciente/{paciente_id}", payload)
    return resp is not None


def create_exam(client: SIAPClient, paciente_id: int, profissional_id: int, exam_template: Dict, data_str: str) -> bool:
    """Cria exame via API (form-data)."""
    if exam_template["tipo"] == "numerico":
        valor = round(random.uniform(exam_template["valor_min"], exam_template["valor_max"]), 1)
        descricao = f"Resultado: {valor} {exam_template['unidade']}. Valor dentro da faixa de referência."
    else:
        # Gerar valores aleatórios para preencher o template
        parts = []
        for _ in range(5):
            parts.append(str(round(random.uniform(10, 500), 1)))
        parts.append("Sem alterações significativas.")
        descricao = exam_template["descricao_modelo"].format(*parts)
        valor = None

    payload = {
        "paciente_id": str(paciente_id),
        "profissional_id": str(profissional_id),
        "data_exame": data_str,
        "tipo_exame": exam_template["tipo"],
        "titulo": exam_template["titulo"],
        "descricao": descricao,
    }
    if valor is not None:
        payload["valor"] = str(valor)
        payload["unidade"] = exam_template.get("unidade", "")

    resp = client.post_form("/api/exames", payload)
    return resp is not None


def create_consultation(client: SIAPClient, paciente_id: int, data_hora: str, tipo: str = "Rotina") -> bool:
    """Cria consulta via API."""
    payload = {
        "paciente_id": paciente_id,
        "data_hora": data_hora,
        "tipo": tipo,
        "status": "realizada",
        "observacoes": "Consulta de acompanhamento do tratamento com cannabis medicinal."
    }
    resp = client.post_json("/api/consultas/", payload)
    return resp is not None


def create_prescription(client: SIAPClient, paciente_id: int, dosagem_ids: List[int]) -> bool:
    """Cria prescrição via API."""
    payload = {
        "paciente_id": paciente_id,
        "dosagens_ids": dosagem_ids,
        "observacoes": "Prescrição de cannabis medicinal conforme protocolo estabelecido."
    }
    resp = client.post_json("/api/prescricoes/gerar", payload)
    if resp:
        print(f"      [+] Prescrição gerada")
    return resp is not None


# ───────────────────────────────────────────────
# MAIN DATASET BUILDER
# ───────────────────────────────────────────────

def build_dataset():
    print("=" * 60)
    print("SIAP HOMOLOGATION DATASET GENERATOR")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Physicians: 3 | Patients per physician: 5 | Total patients: 15")
    print("-" * 60)

    # 1. Login as admin
    admin_client = SIAPClient()
    if not admin_client.login(ADMIN_USER, ADMIN_PASS):
        print("[FATAL] Admin login failed")
        return
    print("[OK] Admin authenticated")

    # 2. Create physicians
    physicians_created = []
    for i, physician in enumerate(PHYSICIANS, 1):
        print(f"\n[{i}/3] Creating physician: {physician['nome']}")
        pid = create_physician(admin_client, physician)
        if pid:
            physicians_created.append({"id": pid, **physician})
        time.sleep(0.5)

    if len(physicians_created) != 3:
        print(f"[WARN] Expected 3 physicians, got {len(physicians_created)}")

    # 3. For each physician, create patients and clinical data
    all_patients_summary = []
    patient_counter = 0

    for phys in physicians_created:
        print(f"\n{'='*60}")
        print(f"PHYSICIAN: {phys['nome']} ({phys['especialidade']})")
        print(f"{'='*60}")

        # Login as this physician
        phys_client = SIAPClient()
        if not phys_client.login(phys["usuario"], phys["senha"]):
            print(f"[SKIP] Could not login as {phys['usuario']}")
            continue

        for p_idx in range(1, 6):
            patient_counter += 1
            print(f"\n  [Patient {p_idx}/5] Generating...")

            # Generate patient data
            patient_data = generate_patient(phys["id"], phys["especialidade"], patient_counter)

            # Create patient
            paciente_id = create_patient(phys_client, patient_data)
            if not paciente_id:
                print(f"    [SKIP] Failed to create patient")
                continue

            base_date = patient_data["evolucao_datas"][0]

            # 3a. Create symptoms (at D0)
            print(f"    [+] Creating {len(patient_data['sintomas'])} symptoms...")
            for symptom in patient_data["sintomas"]:
                create_symptom(phys_client, paciente_id, symptom, base_date.strftime("%Y-%m-%d"))
                time.sleep(0.1)

            # 3b. Create dosages (medications) at D0
            print(f"    [+] Creating {len(patient_data['protocolo_cannabis'])} dosages...")
            dosagem_ids = []
            for protocol in patient_data["protocolo_cannabis"]:
                # First create via API to get ID
                resp = phys_client.post_json(
                    f"/api/dosagens/paciente/{paciente_id}",
                    {
                        "data": base_date.strftime("%Y-%m-%d"),
                        "dosagem": protocol["produto"]["nome"],
                        "via_administracao": protocol["produto"]["via"],
                        "gotas": protocol["gotas"],
                        "frequencia_diaria": protocol["frequencia_diaria"],
                        "concentracao_cbd": protocol["produto"]["cbd_mg_ml"] * 30,
                        "concentracao_thc": protocol["produto"]["thc_mg_ml"] * 30,
                        "instrucoes_uso": protocol["posologia_texto"],
                        "observacoes": protocol["meta_tratamento"]
                    }
                )
                if resp and "dosagem" in resp:
                    dosagem_ids.append(resp["dosagem"]["id"])
                elif resp and "id" in resp:
                    dosagem_ids.append(resp["id"])
                time.sleep(0.1)

            # 3c. Create evolutions (D0, D30, D60, D90, D180)
            print(f"    [+] Creating 5 evolutions...")
            for vnum, vdate in enumerate(patient_data["evolucao_datas"]):
                text = build_evolution_text(patient_data, vnum, vdate)
                create_evolution(phys_client, paciente_id, text, vdate.strftime("%Y-%m-%d"))
                time.sleep(0.1)

            # 3d. Create exams (5 per patient)
            print(f"    [+] Creating 5 exams...")
            for exam_tpl in patient_data["exames"]:
                exam_date = base_date + timedelta(days=random.randint(-7, 7))
                create_exam(phys_client, paciente_id, phys["id"], exam_tpl, exam_date.strftime("%Y-%m-%d"))
                time.sleep(0.1)

            # 3e. Create consultations (5 per patient)
            print(f"    [+] Creating 5 consultations...")
            for vnum, vdate in enumerate(patient_data["evolucao_datas"]):
                dt_str = f"{vdate.strftime('%Y-%m-%d')} {random.randint(9,17):02d}:00:00"
                create_consultation(phys_client, paciente_id, dt_str)
                time.sleep(0.1)

            # 3f. Create prescriptions (3 per patient at D0, D30, D90)
            print(f"    [+] Creating 3 prescriptions...")
            for prescr_date_offset in [0, 30, 90]:
                prescr_date = base_date + timedelta(days=prescr_date_offset)
                # Re-create dosages for each prescription date if needed
                current_dos_ids = []
                for protocol in patient_data["protocolo_cannabis"]:
                    resp = phys_client.post_json(
                        f"/api/dosagens/paciente/{paciente_id}",
                        {
                            "data": prescr_date.strftime("%Y-%m-%d"),
                            "dosagem": protocol["produto"]["nome"],
                            "via_administracao": protocol["produto"]["via"],
                            "gotas": max(1, protocol["gotas"] + random.randint(-1, 1)),
                            "frequencia_diaria": protocol["frequencia_diaria"],
                            "concentracao_cbd": protocol["produto"]["cbd_mg_ml"] * 30,
                            "concentracao_thc": protocol["produto"]["thc_mg_ml"] * 30,
                            "instrucoes_uso": protocol["posologia_texto"],
                            "observacoes": protocol["meta_tratamento"]
                        }
                    )
                    if resp and "dosagem" in resp:
                        current_dos_ids.append(resp["dosagem"]["id"])
                    elif resp and "id" in resp:
                        current_dos_ids.append(resp["id"])
                    time.sleep(0.1)

                if current_dos_ids:
                    create_prescription(phys_client, paciente_id, current_dos_ids)
                time.sleep(0.2)

            # Summary
            all_patients_summary.append({
                "id": paciente_id,
                "nome": patient_data["nome"],
                "medico": phys["nome"],
                "condicoes": patient_data["diagnostico"],
                "sintomas": len(patient_data["sintomas"]),
                "evolucoes": 5,
                "exames": 5,
                "consultas": 5,
                "prescricoes": 3,
            })

            print(f"    [✓] Patient {patient_data['nome']} complete")

    # 4. Final report
    print(f"\n{'='*60}")
    print("DATASET GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Physicians created: {len(physicians_created)}")
    print(f"Patients created: {len(all_patients_summary)}")
    print(f"Total symptoms: {sum(p['sintomas'] for p in all_patients_summary)}")
    print(f"Total evolutions: {sum(p['evolucoes'] for p in all_patients_summary)}")
    print(f"Total exams: {sum(p['exames'] for p in all_patients_summary)}")
    print(f"Total consultations: {sum(p['consultas'] for p in all_patients_summary)}")
    print(f"Total prescriptions: {sum(p['prescricoes'] for p in all_patients_summary)}")
    print(f"\n{'='*60}")

    # Save report
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "physicians": physicians_created,
        "patients": all_patients_summary,
        "totals": {
            "physicians": len(physicians_created),
            "patients": len(all_patients_summary),
            "symptoms": sum(p["sintomas"] for p in all_patients_summary),
            "evolutions": sum(p["evolucoes"] for p in all_patients_summary),
            "exams": sum(p["exames"] for p in all_patients_summary),
            "consultations": sum(p["consultas"] for p in all_patients_summary),
            "prescriptions": sum(p["prescricoes"] for p in all_patients_summary),
        }
    }

    report_path = "/home/holzwarth/Projetos/Aracannabis_SO/Aracannabis_SIAP/scripts/homologation/dataset_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[OK] Report saved to: {report_path}")


if __name__ == "__main__":
    build_dataset()
