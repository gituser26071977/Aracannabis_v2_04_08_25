from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Paciente, Dosagem, Evolucao, Profissional, PreConsulta, Consulta
from sqlalchemy import func, extract
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    current_user_id = get_jwt_identity()
    
    # Filtro base: Pacientes do profissional logado (Exceto superadmin que vê tudo)
    user = Profissional.query.get(current_user_id)
    if user and user.role == 'superadmin':
        base_query = Paciente.query
    else:
        base_query = Paciente.query.filter_by(profissional_responsavel_id=current_user_id)
    
    # 1. Total de Pacientes
    total_pacientes = base_query.count()
    if total_pacientes == 0:
        return jsonify({
            'total_pacientes': 0,
            'em_tratamento_pct': 0,
            'melhora_pct': 0,
            'dose_estavel_pct': 0,
            'principais_condicoes': []
        }), 200

    # 2. Pacientes em Tratamento
    em_tratamento_count = base_query.filter_by(em_tratamento=True).count()
    em_tratamento_pct = (em_tratamento_count / total_pacientes) * 100

    # 3. Medicação com Dose Estável > 3 meses
    # Lógica: Pacientes em tratamento cuja última dosagem foi registrada há mais de 90 dias
    # Isso assume que se não houve nova dosagem, a dose se manteve.
    data_limite_estabilidade = datetime.utcnow() - timedelta(days=90)
    
    pacientes_em_tratamento = base_query.filter_by(em_tratamento=True).all()
    pacientes_estaveis = 0
    
    for paciente in pacientes_em_tratamento:
        ultima_dosagem = Dosagem.query.filter_by(paciente_id=paciente.id).order_by(Dosagem.data.desc()).first()
        if ultima_dosagem:
            # Se a última dosagem é antiga, consideramos estável
            if ultima_dosagem.created_at < data_limite_estabilidade:
                pacientes_estaveis += 1
            # Ou se a data da dosagem é antiga
            elif ultima_dosagem.data and ultima_dosagem.data < data_limite_estabilidade.date():
                pacientes_estaveis += 1
                
    dose_estavel_pct = (pacientes_estaveis / em_tratamento_count * 100) if em_tratamento_count > 0 else 0

    # 4. Melhora Registrada (Heurística simples por palavras-chave na evolução)
    # Idealmente usaria scores de testes
    keywords_melhora = ['melhor', 'melhora', 'estável', 'bom', 'positiv', 'redução', 'evolução']
    pacientes_melhora = 0
    
    for paciente in pacientes_em_tratamento:
        # Pega as últimas 3 evoluções
        evolucoes = Evolucao.query.filter_by(paciente_id=paciente.id).order_by(Evolucao.data_evolucao.desc()).limit(3).all()
        if evolucoes:
            texto_combinado = " ".join([e.nota_evolucao.lower() for e in evolucoes])
            if any(k in texto_combinado for k in keywords_melhora):
                pacientes_melhora += 1
    
    melhora_pct = (pacientes_melhora / em_tratamento_count * 100) if em_tratamento_count > 0 else 0

    # 5. Principais Condições (Top 5)
    # Agrupar por 'condicao_medica'
    top_condicoes_query = db.session.query(
        Paciente.condicao_medica, 
        func.count(Paciente.id).label('total')
    ).filter(
        Paciente.condicao_medica != None,
        Paciente.condicao_medica != ''
    )
    
    if not (user and user.role == 'superadmin'):
        top_condicoes_query = top_condicoes_query.filter(Paciente.profissional_responsavel_id == current_user_id)
        
    top_condicoes = top_condicoes_query.group_by(Paciente.condicao_medica).order_by(func.count(Paciente.id).desc()).limit(5).all()
    
    condicoes_data = [{'name': c[0], 'value': c[1]} for c in top_condicoes]

    return jsonify({
        'total_pacientes': total_pacientes,
        'em_tratamento_pct': round(em_tratamento_pct, 1),
        'melhora_pct': round(melhora_pct, 1),
        'dose_estavel_pct': round(dose_estavel_pct, 1),
        'principais_condicoes': condicoes_data
    }), 200


@dashboard_bp.route('/pacientes-do-dia', methods=['GET'])
@jwt_required()
def pacientes_do_dia():
    """Daily Board do profissional: consultas de hoje + queixa/status da pré-consulta.

    Retorna os atendimentos do dia do usuário logado (não cancelados), com
    dados do paciente e a pré-consulta mais recente (se houver).
    """
    from models import Consulta

    current_user_id = get_jwt_identity()
    hoje = datetime.utcnow().date()
    inicio = datetime.combine(hoje, datetime.min.time())
    fim = datetime.combine(hoje, datetime.max.time())

    consultas = (
        Consulta.query.filter(
            Consulta.profissional_id == current_user_id,
            Consulta.data_hora >= inicio,
            Consulta.data_hora <= fim,
            Consulta.status != 'cancelada',
        )
        .order_by(Consulta.data_hora.asc())
        .all()
    )

    itens = []
    for c in consultas:
        pre = (
            PreConsulta.query.filter_by(paciente_id=c.paciente_id)
            .order_by(PreConsulta.data_pre_consulta.desc())
            .first()
        )
        itens.append({
            'consulta_id': c.id,
            'hora': c.data_hora.strftime('%H:%M') if c.data_hora else None,
            'status': c.status,
            'tipo': c.tipo_consulta,
            'paciente_id': c.paciente_id,
            'paciente_nome': c.paciente.nome if c.paciente else None,
            'telefone': c.paciente.telefone if c.paciente else None,
            'pre_consulta': {
                'feita': pre is not None,
                'queixa_principal': pre.queixa_principal if pre else None,
                'intensidade': pre.intensidade if pre else None,
                'canal': pre.canal if pre else None,
                'status': pre.status if pre else None,
            } if pre else {'feita': False},
        })

    return jsonify({'data': hoje.isoformat(), 'total': len(itens), 'pacientes': itens}), 200


@dashboard_bp.route('/stats-detalhado', methods=['GET'])
@jwt_required()
def get_dashboard_stats_detalhado():
    """Estatísticas detalhadas: sexo, faixa etária, consultas, localização."""
    current_user_id = get_jwt_identity()
    user = Profissional.query.get(current_user_id)
    if user and user.role == 'superadmin':
        base = Paciente.query
    else:
        base = Paciente.query.filter_by(profissional_responsavel_id=current_user_id)

    pacientes = base.all()
    total = len(pacientes)
    if total == 0:
        return jsonify({"sexo": [], "faixa_etaria": [], "consultas_tipo": [], "cidades": [], "estados": []}), 200

    # 1. Sexo
    masc = sum(1 for p in pacientes if p.genero and p.genero.lower() in ("m", "masculino", "male"))
    fem = sum(1 for p in pacientes if p.genero and p.genero.lower() in ("f", "feminino", "female"))
    outros = total - masc - fem
    sexo = [
        {"name": "Masculino", "value": masc},
        {"name": "Feminino", "value": fem},
        {"name": "Não informado", "value": outros},
    ]

    # 2. Faixa etária
    hoje = datetime.utcnow().date()
    faixas = {"0-18": 0, "19-30": 0, "31-45": 0, "46-60": 0, "60+": 0}
    for p in pacientes:
        if p.data_nascimento:
            idade = hoje.year - p.data_nascimento.year - ((hoje.month, hoje.day) < (p.data_nascimento.month, p.data_nascimento.day))
            if idade <= 18: faixas["0-18"] += 1
            elif idade <= 30: faixas["19-30"] += 1
            elif idade <= 45: faixas["31-45"] += 1
            elif idade <= 60: faixas["46-60"] += 1
            else: faixas["60+"] += 1
        else:
            faixas["0-18"] += 1
    faixa_etaria = [{"name": k, "value": v} for k, v in faixas.items()]

    # 3. Cidades (parse do endereco)
    cidades = {}
    for p in pacientes:
        if p.endereco:
            partes = [x.strip() for x in p.endereco.replace(",", " ").split() if x.strip()]
            for parte in partes:
                if parte.endswith(","):
                    parte = parte[:-1]
            if len(partes) >= 3:
                cidade = partes[-2]
                cidades[cidade] = cidades.get(cidade, 0) + 1
    cidades_ordenadas = sorted(cidades.items(), key=lambda x: -x[1])[:10]
    cidades_data = [{"name": c, "value": v} for c, v in cidades_ordenadas]

    # 4. Estados (parse do endereco - ultima palavra)
    estados = {}
    for p in pacientes:
        if p.endereco:
            partes = p.endereco.replace(",", " ").split()
            uf = partes[-1].strip().upper() if partes else ""
            if len(uf) == 2 and uf.isalpha():
                estados[uf] = estados.get(uf, 0) + 1
    estados_data = [{"name": e, "value": v} for e, v in sorted(estados.items(), key=lambda x: -x[1])]

    # 5. Consultas por tipo (online vs presencial)
    if user and user.role == 'superadmin':
        consultas_base = Consulta.query
    else:
        consultas_base = Consulta.query.filter_by(profissional_id=current_user_id)

    total_consultas = consultas_base.count()
    presencial = consultas_base.filter(Consulta.tipo_consulta == "presencial").count()
    telemedicina = consultas_base.filter(Consulta.tipo_consulta == "telemedicina").count()
    consultas_tipo = [
        {"name": "Presencial", "value": presencial},
        {"name": "Telemedicina", "value": telemedicina},
    ]

    # 6. Consultas por mês (últimos 12 meses)
    hoje = datetime.utcnow()
    doze_meses = hoje - timedelta(days=365)
    consultas_por_mes = (
        db.session.query(
            extract("year", Consulta.data_hora).label("ano"),
            extract("month", Consulta.data_hora).label("mes"),
            func.count(Consulta.id).label("total"),
        )
        .filter(Consulta.data_hora >= doze_meses)
    )
    if not (user and user.role == "superadmin"):
        consultas_por_mes = consultas_por_mes.filter(Consulta.profissional_id == current_user_id)
    consultas_por_mes = consultas_por_mes.group_by("ano", "mes").order_by("ano", "mes").all()

    consultas_mensal = [
        {"name": f"{c.ano}-{str(c.mes).zfill(2)}", "value": c.total}
        for c in consultas_por_mes
    ]

    return jsonify({
        "sexo": [s for s in sexo if s["value"] > 0],
        "faixa_etaria": faixa_etaria,
        "cidades": cidades_data,
        "estados": estados_data,
        "consultas_tipo": consultas_tipo,
        "consultas_mensal": consultas_mensal,
        "total_pacientes": total,
        "total_consultas": total_consultas,
    }), 200
