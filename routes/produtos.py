from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Produto, LogAtividade
from datetime import datetime

produtos_bp = Blueprint('produtos', __name__)

@produtos_bp.route('/produtos', methods=['GET'])
@jwt_required()
def listar_produtos():
    """Listar todos os produtos ativos"""
    try:
        produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
        return jsonify({'produtos': [p.to_dict() for p in produtos]}), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao listar produtos: {str(e)}'}), 500

@produtos_bp.route('/produtos', methods=['POST'])
@jwt_required()
def criar_produto():
    """Criar novo produto"""
    data = request.get_json()
    if not data.get('nome'):
        return jsonify({'error': 'Nome do produto é obrigatório'}), 400

    try:
        novo_produto = Produto(
            nome=data['nome'],
            tipo=data.get('tipo', 'oleo'),
            concentracao_cbd=data.get('concentracao_cbd'),
            concentracao_thc=data.get('concentracao_thc'),
            concentracao_cbg=data.get('concentracao_cbg'),
            concentracao_cbn=data.get('concentracao_cbn'),
            gotas_por_ml=data.get('gotas_por_ml'),
            volume_ml=data.get('volume_ml'),
            fabricante=data.get('fabricante'),
            descricao=data.get('descricao')
        )
        db.session.add(novo_produto)
        db.session.commit()
        return jsonify({'message': 'Produto criado com sucesso', 'produto': novo_produto.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar produto: {str(e)}'}), 500

@produtos_bp.route('/produtos/<int:produto_id>', methods=['PUT'])
@jwt_required()
def atualizar_produto(produto_id):
    """Atualizar produto existente"""
    produto = Produto.query.get(produto_id)
    if not produto:
        return jsonify({'error': 'Produto não encontrado'}), 404

    data = request.get_json()
    try:
        produto.nome = data.get('nome', produto.nome)
        produto.tipo = data.get('tipo', produto.tipo)
        produto.concentracao_cbd = data.get('concentracao_cbd', produto.concentracao_cbd)
        produto.concentracao_thc = data.get('concentracao_thc', produto.concentracao_thc)
        produto.concentracao_cbg = data.get('concentracao_cbg', produto.concentracao_cbg)
        produto.concentracao_cbn = data.get('concentracao_cbn', produto.concentracao_cbn)
        produto.gotas_por_ml = data.get('gotas_por_ml', produto.gotas_por_ml)
        produto.volume_ml = data.get('volume_ml', produto.volume_ml)
        produto.fabricante = data.get('fabricante', produto.fabricante)
        produto.descricao = data.get('descricao', produto.descricao)
        produto.ativo = data.get('ativo', produto.ativo)
        
        db.session.commit()
        return jsonify({'message': 'Produto atualizado com sucesso', 'produto': produto.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar produto: {str(e)}'}), 500

@produtos_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
@jwt_required()
def excluir_produto(produto_id):
    """Excluir produto (desativar)"""
    produto = Produto.query.get(produto_id)
    if not produto:
        return jsonify({'error': 'Produto não encontrado'}), 404

    try:
        produto.ativo = False
        db.session.commit()
        return jsonify({'message': 'Produto desativado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao desativar produto: {str(e)}'}), 500

@produtos_bp.route('/produtos/<int:produto_id>', methods=['GET'])
@jwt_required()
def obter_produto(produto_id):
    """Obter produto específico"""
    produto = Produto.query.get(produto_id)
    if not produto or not produto.ativo:
        return jsonify({'error': 'Produto não encontrado ou inativo'}), 404
    return jsonify({'produto': produto.to_dict()}), 200