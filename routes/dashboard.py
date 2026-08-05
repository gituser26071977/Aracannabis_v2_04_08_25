from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Paciente, Dosagem, Evolucao, Profissional, PreConsulta
from sqlalchemy import func
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
