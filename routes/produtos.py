from flask import g, Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Produto, LogAtividade
from datetime import datetime
import os
import tempfile

from services.product_intake import product_intake_service

produtos_bp = Blueprint('produtos', __name__)

def _assoc_id():
    """Resolve o associacao_id atual (tenant) via middleware (P0-12)."""
    from flask import g
    assoc = getattr(g, "current_association", None)
    return getattr(assoc, "id", None)



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
        
        if 'data_registro' in data and data['data_registro']:
            try:
                novo_produto.data_registro = datetime.strptime(data['data_registro'], '%Y-%m-%d').date()
            except ValueError:
                pass # Use default

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
        
        if 'data_registro' in data:
            if data['data_registro']:
                try:
                    produto.data_registro = datetime.strptime(data['data_registro'], '%Y-%m-%d').date()
                except ValueError:
                    pass
            else:
                produto.data_registro = None

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


@produtos_bp.route('/produtos/assistente', methods=['POST'])
@jwt_required()
def cadastrar_produto_com_ia():
    """Cadastra produto usando IA a partir de texto, áudio ou imagem."""
    current_user_id = int(get_jwt_identity())

    try:
        texto = request.form.get('texto') or (request.json or {}).get('texto') if request.is_json else None
        auto_criar_raw = request.form.get('auto_criar') or request.args.get('auto_criar')
        if auto_criar_raw is None and request.is_json:
            auto_criar_raw = (request.json or {}).get('auto_criar')
        auto_criar = str(auto_criar_raw).lower() in ['1', 'true', 'yes', 'sim']

        arquivo = request.files.get('arquivo') if 'arquivo' in request.files else None

        if not texto and not arquivo:
            return jsonify({'error': 'Envie um texto ou arquivo para processar'}), 400

        temp_file = None
        filename = None
        if arquivo:
            filename = arquivo.filename
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
            arquivo.save(temp_file.name)
            temp_file.flush()

        try:
            ia_result = product_intake_service.process_input(
                texto=texto,
                file_path=temp_file.name if temp_file else None,
                filename=filename
            )
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass

        produto_dados = ia_result.get('produto_sugerido', {})
        criado = False
        novo_produto_dict = None

        if auto_criar:
            if not produto_dados.get('nome'):
                return jsonify({'error': 'IA não identificou o nome do produto para cadastro automático'}), 400

            novo_produto = Produto(
                nome=produto_dados.get('nome'),
                tipo=produto_dados.get('tipo', 'oleo'),
                concentracao_cbd=produto_dados.get('concentracao_cbd'),
                concentracao_thc=produto_dados.get('concentracao_thc'),
                concentracao_cbg=produto_dados.get('concentracao_cbg'),
                concentracao_cbn=produto_dados.get('concentracao_cbn'),
                gotas_por_ml=produto_dados.get('gotas_por_ml', 30),
                volume_ml=produto_dados.get('volume_ml', 30),
                fabricante=produto_dados.get('fabricante'),
                descricao=produto_dados.get('descricao'),
                ativo=True
            )
            db.session.add(novo_produto)
            db.session.commit()
            criado = True
            novo_produto_dict = novo_produto.to_dict()

            # Registrar log
            log = LogAtividade(
                profissional_id=current_user_id,
                associacao_id=_assoc_id(),
                acao='CADASTRAR_PRODUTO_IA',
                detalhes=f"Produto criado via IA: {novo_produto.nome}"
            )
            db.session.add(log)
            db.session.commit()

        return jsonify({
            'message': 'Produto processado com sucesso',
            'produto_sugerido': produto_dados,
            'produto_criado': criado,
            'produto': novo_produto_dict,
            'fonte': ia_result.get('fonte'),
            'texto_processado': ia_result.get('texto_processado'),
            'meta': ia_result.get('meta'),
            'timestamp': ia_result.get('timestamp')
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erro no assistente de produtos: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Erro ao processar produto com IA: {str(e)}'}), 500
