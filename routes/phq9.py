from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, PHQ9Teste, Paciente, LogAtividade, Evolucao
from security_config import sanitize_input
from datetime import datetime

phq9_bp = Blueprint('phq9', __name__)

@phq9_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_testes(paciente_id):
    """Listar todos os testes PHQ-9 de um paciente"""
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
        testes = PHQ9Teste.query.filter_by(paciente_id=paciente_id).order_by(PHQ9Teste.data_realizacao.desc()).all()
        
        return jsonify({
            'testes': [teste.to_dict() for teste in testes]
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao listar testes: {str(e)}'}), 500

@phq9_bp.route('/paciente/<int:paciente_id>', methods=['POST'])
@jwt_required()
def criar_teste(paciente_id):
    """Criar um novo teste PHQ-9"""
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
    required_fields = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Todos os campos de resposta são obrigatórios'}), 400

    # Validar valores (0-3)
    for i in range(1, 10):
        value = data.get(f'q{i}')
        if value not in [0, 1, 2, 3]:
            return jsonify({'error': f'Valor inválido para Q{i}. Use 0, 1, 2 ou 3.'}), 400

    try:
        # Criar novo teste
        novo_teste = PHQ9Teste(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            q1=data['q1'],
            q2=data['q2'],
            q3=data['q3'],
            q4=data['q4'],
            q5=data['q5'],
            q6=data['q6'],
            q7=data['q7'],
            q8=data['q8'],
            q9=data['q9'],
            observacoes=data.get('observacoes', '')
        )

        # Calcular resultados
        resultados = novo_teste.calcular_resultados()
        novo_teste.pontuacao_total = resultados['pontuacao_total']
        novo_teste.nivel_depressao = resultados['nivel_depressao']
        novo_teste.depressao_positiva = resultados['depressao_positiva']
        novo_teste.risco_suicida = resultados['risco_suicida']

        db.session.add(novo_teste)
        db.session.commit()

        # Atualizar campo depressao_positiva do paciente se for o responsável
        if paciente.profissional_responsavel_id == profissional_id:
            paciente.depressao_positiva = novo_teste.depressao_positiva
            db.session.commit()

        # Criar registro de evolução com os resultados do teste
        data_formatada = novo_teste.data_realizacao.strftime('%d/%m/%Y')
        texto_evolucao = (
            f"TESTE PHQ-9 REALIZADO EM {data_formatada}\n"
            f"Pontuação Total: {novo_teste.pontuacao_total}/27\n"
            f"Nível de Depressão: {novo_teste.nivel_depressao.replace('_', ' ').title()}\n"
            f"Risco Suicida: {'SIM' if novo_teste.risco_suicida else 'Não'}\n"
            f"Depressão Positiva: {'Sim' if novo_teste.depressao_positiva else 'Não'}\n"
            f"Observações: {novo_teste.observacoes}"
        )

        nova_evolucao = Evolucao(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            data_evolucao=novo_teste.data_realizacao,
            nota_evolucao=texto_evolucao
        )
        db.session.add(nova_evolucao)
        db.session.commit()

        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Teste PHQ-9',
            detalhes=f'Teste PHQ-9 realizado para paciente {paciente.nome}. Pontuação: {novo_teste.pontuacao_total}. Risco suicida: {"Sim" if novo_teste.risco_suicida else "Não"}'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'message': 'Teste PHQ-9 criado com sucesso',
            'teste': novo_teste.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar teste: {str(e)}'}), 500

@phq9_bp.route('/<int:teste_id>', methods=['GET'])
@jwt_required()
def obter_teste(teste_id):
    """Obter um teste PHQ-9 específico"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    teste = PHQ9Teste.query.get(teste_id)
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

@phq9_bp.route('/paciente/<int:paciente_id>/ultimo', methods=['GET'])
@jwt_required()
def obter_ultimo_teste(paciente_id):
    """Obter o último teste PHQ-9 do paciente"""
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
        ultimo_teste = PHQ9Teste.query.filter_by(paciente_id=paciente_id)\
            .order_by(PHQ9Teste.data_realizacao.desc())\
            .first()

        if not ultimo_teste:
            return jsonify({'error': 'Nenhum teste PHQ-9 encontrado para este paciente'}), 404

        return jsonify({
            'teste': ultimo_teste.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao obter último teste: {str(e)}'}), 500

@phq9_bp.route('/<int:teste_id>', methods=['DELETE'])
@jwt_required()
def excluir_teste(teste_id):
    """Excluir um teste PHQ-9"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    teste = PHQ9Teste.query.get(teste_id)
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
            acao='Exclusão Teste PHQ-9',
            detalhes=f'Teste PHQ-9 excluído para paciente {paciente.nome}. Pontuação: {teste.pontuacao_total}'
        )
        db.session.add(log)

        db.session.delete(teste)
        db.session.commit()

        return jsonify({
            'message': 'Teste PHQ-9 excluído com sucesso'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir teste: {str(e)}'}), 500
