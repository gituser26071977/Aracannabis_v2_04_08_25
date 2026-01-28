from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, BeckDepressionTeste, Paciente, Profissional
from datetime import datetime

beck_depression_bp = Blueprint('beck_depression', __name__)

@beck_depression_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_testes_paciente(paciente_id):
    """Lista todos os testes de depressão de um paciente"""
    try:
        testes = BeckDepressionTeste.query.filter_by(paciente_id=paciente_id).order_by(BeckDepressionTeste.data_realizacao.desc()).all()
        return jsonify([teste.to_dict() for teste in testes]), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao listar testes: {str(e)}'}), 500

@beck_depression_bp.route('/paciente/<int:paciente_id>', methods=['POST'])
@jwt_required()
def criar_teste(paciente_id):
    """Cria um novo teste de depressão para um paciente"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Verificar se paciente existe
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404

        # Validar dados obrigatórios (21 itens)
        for i in range(1, 22):
            field = f'item_{i}'
            if field not in data or not isinstance(data[field], int) or data[field] < 0 or data[field] > 3:
                return jsonify({'error': f'Campo {field} é obrigatório e deve ser um inteiro entre 0 e 3'}), 400

        # Criar teste
        teste = BeckDepressionTeste(
            paciente_id=paciente_id,
            profissional_id=int(current_user_id)
        )

        # Definir respostas
        for i in range(1, 22):
            setattr(teste, f'item_{i}', data[f'item_{i}'])

        # Calcular resultados
        resultados = teste.calcular_resultados()
        teste.pontuacao_total = resultados['pontuacao_total']
        teste.nivel_depressao = resultados['nivel_depressao']
        teste.depressao_positiva = resultados['depressao_positiva']

        # Adicionar observações se fornecidas
        if 'observacoes' in data:
            teste.observacoes = data['observacoes']

        # Salvar no banco
        db.session.add(teste)

        # Atualizar status depressão do paciente se positivo
        if teste.depressao_positiva:
            paciente.depressao_positiva = True

        db.session.commit()

        return jsonify({
            'message': 'Teste de depressão criado com sucesso',
            'teste': teste.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar teste: {str(e)}'}), 500

@beck_depression_bp.route('/<int:teste_id>', methods=['GET'])
@jwt_required()
def obter_teste(teste_id):
    """Obtém um teste de depressão específico"""
    try:
        teste = BeckDepressionTeste.query.get(teste_id)
        if not teste:
            return jsonify({'error': 'Teste não encontrado'}), 404

        return jsonify(teste.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao obter teste: {str(e)}'}), 500

@beck_depression_bp.route('/<int:teste_id>', methods=['PUT'])
@jwt_required()
def atualizar_teste(teste_id):
    """Atualiza um teste de depressão (apenas observações)"""
    try:
        teste = BeckDepressionTeste.query.get(teste_id)
        if not teste:
            return jsonify({'error': 'Teste não encontrado'}), 404

        data = request.get_json()
        if 'observacoes' in data:
            teste.observacoes = data['observacoes']
            db.session.commit()

        return jsonify({
            'message': 'Teste atualizado com sucesso',
            'teste': teste.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar teste: {str(e)}'}), 500

@beck_depression_bp.route('/<int:teste_id>', methods=['DELETE'])
@jwt_required()
def excluir_teste(teste_id):
    """Exclui um teste de depressão"""
    try:
        teste = BeckDepressionTeste.query.get(teste_id)
        if not teste:
            return jsonify({'error': 'Teste não encontrado'}), 404

        paciente_id = teste.paciente_id

        db.session.delete(teste)

        # Verificar se ainda há outros testes positivos para este paciente
        outros_testes = BeckDepressionTeste.query.filter_by(paciente_id=paciente_id, depressao_positiva=True).all()
        if not outros_testes:
            paciente = Paciente.query.get(paciente_id)
            if paciente:
                paciente.depressao_positiva = False

        db.session.commit()

        return jsonify({'message': 'Teste excluído com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir teste: {str(e)}'}), 500

@beck_depression_bp.route('/paciente/<int:paciente_id>/ultimo', methods=['GET'])
@jwt_required()
def obter_ultimo_teste(paciente_id):
    """Obtém o último teste de depressão de um paciente"""
    try:
        teste = BeckDepressionTeste.query.filter_by(paciente_id=paciente_id).order_by(BeckDepressionTeste.data_realizacao.desc()).first()
        if not teste:
            return jsonify({'message': 'Nenhum teste encontrado para este paciente'}), 404

        return jsonify(teste.to_dict()), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao obter último teste: {str(e)}'}), 500