from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, GAD7Teste, Paciente, LogAtividade, Evolucao
from security_config import sanitize_input
from datetime import datetime

gad7_bp = Blueprint('gad7', __name__)


def _assoc_id():
    """Resolve o associacao_id atual (tenant) via middleware (P0-12)."""
    assoc = getattr(g, 'current_association', None)
    return getattr(assoc, 'id', None)


@gad7_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_testes(paciente_id):
    """Listar todos os testes GAD-7 de um paciente"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    # Verificar se o profissional tem acesso ao paciente
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if paciente.profissional_responsavel_id != profissional_id:
        # Verificar se há compartilhamento ativo
        from routes.pacientes import verificar_acesso_paciente
        tem_acesso, _, _ = verificar_acesso_paciente(profissional_id, paciente_id)
        if not tem_acesso:
            return jsonify({'error': 'Acesso negado a este paciente'}), 403

    try:
        testes = GAD7Teste.query.filter_by(paciente_id=paciente_id).order_by(GAD7Teste.data_realizacao.desc()).all()
        
        return jsonify({
            'testes': [teste.to_dict() for teste in testes]
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao listar testes: {str(e)}'}), 500

@gad7_bp.route('/paciente/<int:paciente_id>', methods=['POST'])
@jwt_required()
def criar_teste(paciente_id):
    """Criar um novo teste GAD-7"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    # Verificar se o profissional tem acesso ao paciente
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if paciente.profissional_responsavel_id != profissional_id:
        # Verificar se há compartilhamento ativo com acesso de escrita
        from routes.pacientes import verificar_acesso_paciente
        tem_acesso, _, _ = verificar_acesso_paciente(profissional_id, paciente_id, 'escrita')
        if not tem_acesso:
            return jsonify({'error': 'Acesso negado para criar teste para este paciente'}), 403

    data = request.get_json()
    data = sanitize_input(data)

    # Validar dados obrigatórios
    required_fields = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Todos os campos de resposta são obrigatórios'}), 400

    # Validar valores (0-3)
    for i in range(1, 8):
        value = data.get(f'q{i}')
        if value not in [0, 1, 2, 3]:
            return jsonify({'error': f'Valor inválido para Q{i}. Use 0, 1, 2 ou 3.'}), 400

    try:
        # Criar novo teste
        novo_teste = GAD7Teste(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            q1=data['q1'],
            q2=data['q2'],
            q3=data['q3'],
            q4=data['q4'],
            q5=data['q5'],
            q6=data['q6'],
            q7=data['q7'],
            observacoes=data.get('observacoes', '')
        )

        if 'data_realizacao' in data and data['data_realizacao']:
            try:
                # Tenta converter string YYYY-MM-DD para datetime
                data_obj = datetime.strptime(data['data_realizacao'], '%Y-%m-%d')
                # Adiciona a hora atual para não ficar tudo meia-noite
                agora = datetime.now()
                novo_teste.data_realizacao = data_obj.replace(hour=agora.hour, minute=agora.minute, second=agora.second)
            except ValueError:
                # Se falhar, usa data atual (comportamento padrão do model)
                pass

        # Calcular resultados
        resultados = novo_teste.calcular_resultados()
        novo_teste.pontuacao_total = resultados['pontuacao_total']
        novo_teste.nivel_ansiedade = resultados['nivel_ansiedade']
        novo_teste.ansiedade_positiva = resultados['ansiedade_positiva']

        db.session.add(novo_teste)
        db.session.commit()

        # Criar registro de evolução com os resultados do teste
        data_formatada = novo_teste.data_realizacao.strftime('%d/%m/%Y')
        texto_evolucao = (
            f"TESTE GAD-7 REALIZADO EM {data_formatada}\n"
            f"Pontuação Total: {novo_teste.pontuacao_total}/21\n"
            f"Nível de Ansiedade: {novo_teste.nivel_ansiedade.replace('_', ' ').title()}\n"
            f"Ansiedade Positiva: {'Sim' if novo_teste.ansiedade_positiva else 'Não'}\n"
            f"Observações: {novo_teste.observacoes}"
        )

        nova_evolucao = Evolucao(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            data_evolucao=novo_teste.data_realizacao,
            nota_evolucao=texto_evolucao
        )
        db.session.add(nova_evolucao)
        db.session.commit()

        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            acao='Teste GAD-7',
            detalhes=f'Teste GAD-7 realizado para paciente {paciente.nome}. Pontuação: {novo_teste.pontuacao_total}.'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'message': 'Teste GAD-7 criado com sucesso',
            'teste': novo_teste.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar teste: {str(e)}'}), 500

@gad7_bp.route('/<int:teste_id>', methods=['GET'])
@jwt_required()
def obter_teste(teste_id):
    """Obter um teste GAD-7 específico"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    teste = GAD7Teste.query.get(teste_id)
    if not teste:
        return jsonify({'error': 'Teste não encontrado'}), 404

    # Verificar acesso ao paciente
    paciente = Paciente.query.get(teste.paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if paciente.profissional_responsavel_id != profissional_id:
        from routes.pacientes import verificar_acesso_paciente
        tem_acesso, _, _ = verificar_acesso_paciente(profissional_id, teste.paciente_id)
        if not tem_acesso:
            return jsonify({'error': 'Acesso negado a este teste'}), 403

    return jsonify({
        'teste': teste.to_dict()
    }), 200

@gad7_bp.route('/paciente/<int:paciente_id>/ultimo', methods=['GET'])
@jwt_required()
def obter_ultimo_teste(paciente_id):
    """Obter o último teste GAD-7 do paciente"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    # Verificar acesso ao paciente
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if paciente.profissional_responsavel_id != profissional_id:
        from routes.pacientes import verificar_acesso_paciente
        tem_acesso, _, _ = verificar_acesso_paciente(profissional_id, paciente_id)
        if not tem_acesso:
            return jsonify({'error': 'Acesso negado a este paciente'}), 403

    try:
        ultimo_teste = GAD7Teste.query.filter_by(paciente_id=paciente_id)\
            .order_by(GAD7Teste.data_realizacao.desc())\
            .first()

        if not ultimo_teste:
            return jsonify({'error': 'Nenhum teste GAD-7 encontrado para este paciente'}), 404

        return jsonify({
            'teste': ultimo_teste.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao obter último teste: {str(e)}'}), 500

@gad7_bp.route('/<int:teste_id>', methods=['DELETE'])
@jwt_required()
def excluir_teste(teste_id):
    """Excluir um teste GAD-7"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    teste = GAD7Teste.query.get(teste_id)
    if not teste:
        return jsonify({'error': 'Teste não encontrado'}), 404

    # Verificar se é o profissional responsável
    paciente = Paciente.query.get(teste.paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if paciente.profissional_responsavel_id != profissional_id:
        return jsonify({'error': 'Apenas o profissional responsável pode excluir testes'}), 403

    try:
        # Registrar atividade antes da exclusão
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            acao='Exclusão Teste GAD-7',
            detalhes=f'Teste GAD-7 excluído para paciente {paciente.nome}. Pontuação: {teste.pontuacao_total}'
        )
        db.session.add(log)

        db.session.delete(teste)
        db.session.commit()

        return jsonify({
            'message': 'Teste GAD-7 excluído com sucesso'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir teste: {str(e)}'}), 500
