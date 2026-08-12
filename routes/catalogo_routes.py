"""
Rotas da API para catálogo de produtos de cannabis
"""
import os
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from functools import wraps

# Blueprint
catalogo_bp = Blueprint('catalogo', __name__, url_prefix='/api/catalogo')

# Importa serviços
from services.catalogo_agent_service import catalogo_service
from services.catalogo_document_processor import document_processor
from models import db
from models_produto import ProdutoCannabis, CatalogoImportacao, SugestaoPrescricao


def jwt_required_custom(f):
    """Decorator simplificado para verificar JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        try:
            verify_jwt_in_request()
            g.current_user_id = get_jwt_identity()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
    return decorated_function


def get_current_profissional_id():
    """Obtém ID do profissional logado"""
    from flask_jwt_extended import get_jwt_identity
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            return identity.get('profissional_id')
        return identity
    except:
        return None


# ============================================================================
# ROTAS DE UPLOAD E IMPORTAÇÃO
# ============================================================================

@catalogo_bp.route('/upload', methods=['POST'])
@jwt_required_custom
def upload_catalogo():
    """
    Faz upload de arquivo de catálogo (PDF, XLSX, CSV, DOCX, TXT)
    
    Form-data:
    - arquivo: arquivo a ser enviado
    - empresa_origem (opcional): nome da empresa/fabricante
    """
    if 'arquivo' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['arquivo']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    # Verifica extensão
    if not document_processor.allowed_file(file.filename):
        return jsonify({
            'error': 'Formato não suportado. Use: PDF, XLSX, CSV, DOCX, TXT'
        }), 400
    
    # Salva arquivo temporariamente
    filename = secure_filename(file.filename)
    upload_dir = '/tmp/catalogo_uploads'
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    # Obtém parâmetros
    empresa_origem = request.form.get('empresa_origem')
    profissional_id = get_current_profissional_id()
    
    # Processa o catálogo
    resultado = catalogo_service.processar_catalogo(
        arquivo_path=filepath,
        filename=filename,
        profissional_id=profissional_id,
        empresa_origem=empresa_origem
    )
    
    # Remove arquivo temporário
    try:
        os.remove(filepath)
    except:
        pass
    
    if resultado.get('success'):
        return jsonify(resultado), 201
    else:
        return jsonify(resultado), 400


@catalogo_bp.route('/importacoes', methods=['GET'])
@jwt_required_custom
def listar_importacoes():
    """Lista histórico de importações de catálogos"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = CatalogoImportacao.query.order_by(
        CatalogoImportacao.created_at.desc()
    )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'importacoes': [imp.to_dict() for imp in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@catalogo_bp.route('/importacoes/<int:importacao_id>', methods=['GET'])
@jwt_required_custom
def obter_importacao(importacao_id):
    """Obtém detalhes de uma importação específica"""
    importacao = CatalogoImportacao.query.get_or_404(importacao_id)
    return jsonify(importacao.to_dict())


# ============================================================================
# ROTAS DE PRODUTOS
# ============================================================================

@catalogo_bp.route('/produtos', methods=['GET'])
@jwt_required_custom
def listar_produtos():
    """
    Lista produtos com filtros avançados
    
    Query params:
    - nome: busca por nome/marca
    - categoria: filtro por categoria
    - cbd_min, cbd_max: range de CBD
    - thc_min, thc_max: range de THC
    - quimiotipo: Tipo I, II, III, IV
    - via_administracao: sublingual, oral, etc
    - indicacao: busca em indicações
    - marca: filtro por marca
    - disponivel: true/false
    - limit: limite de resultados (default: 100)
    """
    filtros = {
        'nome': request.args.get('nome'),
        'categoria': request.args.get('categoria'),
        'cbd_min': request.args.get('cbd_min', type=float),
        'cbd_max': request.args.get('cbd_max', type=float),
        'thc_min': request.args.get('thc_min', type=float),
        'thc_max': request.args.get('thc_max', type=float),
        'quimiotipo': request.args.get('quimiotipo'),
        'via_administracao': request.args.get('via_administracao'),
        'indicacao': request.args.get('indicacao'),
        'marca': request.args.get('marca'),
        'disponivel': request.args.get('disponivel', type=lambda x: x.lower() == 'true' if x else None),
        'limit': request.args.get('limit', 100, type=int)
    }
    
    # Remove filtros vazios
    filtros = {k: v for k, v in filtros.items() if v is not None}
    
    produtos = catalogo_service.buscar_produtos(filtros)
    
    return jsonify({
        'produtos': produtos,
        'total': len(produtos),
        'filtros_aplicados': filtros
    })


@catalogo_bp.route('/produtos/<int:produto_id>', methods=['GET'])
@jwt_required_custom
def obter_produto(produto_id):
    """Obtém detalhes de um produto específico"""
    produto = ProdutoCannabis.query.get_or_404(produto_id)
    return jsonify(produto.to_dict())


@catalogo_bp.route('/produtos', methods=['POST'])
@jwt_required_custom
def criar_produto():
    """
    Cria um novo produto manualmente
    
    Body (JSON):
    {
        "nome": "...",
        "marca": "...",
        "cbd_total_mg": ...,
        "thc_total_mg": ...,
        ...
    }
    """
    data = request.get_json()
    
    if not data or not data.get('nome') or not data.get('marca'):
        return jsonify({'error': 'Nome e marca são obrigatórios'}), 400
    
    profissional_id = get_current_profissional_id()
    
    try:
        produto = ProdutoCannabis(
            nome=data.get('nome'),
            nome_comercial=data.get('nome_comercial'),
            marca=data.get('marca'),
            laboratorio=data.get('laboratorio'),
            categoria=data.get('categoria'),
            cbd_total_mg=data.get('cbd_total_mg'),
            thc_total_mg=data.get('thc_total_mg'),
            cbg_mg=data.get('cbg_mg'),
            quimiotipo=data.get('quimiotipo'),
            razao_cbd_thc=data.get('razao_cbd_thc'),
            espectro=data.get('espectro'),
            via_administracao=data.get('via_administracao'),
            volume_ml=data.get('volume_ml'),
            quantidade_cps=data.get('quantidade_cps'),
            indicacoes=data.get('indicacoes'),
            contraindicacoes=data.get('contraindicacoes'),
            posologia_inicial=data.get('posologia_inicial'),
            registro_anvisa=data.get('registro_anvisa'),
            preco_referencia=data.get('preco_referencia'),
            created_by=profissional_id,
            fonte_dados='Manual',
            associacao_id=getattr(getattr(g, 'current_association', None), 'id', None)
        )
        
        from models import db
        db.session.add(produto)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produto criado com sucesso',
            'produto': produto.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@catalogo_bp.route('/produtos/<int:produto_id>', methods=['PUT'])
@jwt_required_custom
def atualizar_produto(produto_id):
    """Atualiza um produto existente"""
    produto = ProdutoCannabis.query.get_or_404(produto_id)
    data = request.get_json()
    
    # Atualiza campos permitidos
    campos_atualizaveis = [
        'nome', 'nome_comercial', 'marca', 'laboratorio', 'categoria',
        'cbd_total_mg', 'thc_total_mg', 'cbg_mg', 'quimiotipo',
        'razao_cbd_thc', 'espectro', 'via_administracao', 'volume_ml',
        'quantidade_cps', 'indicacoes', 'contraindicacoes', 'interacoes',
        'posologia_inicial', 'posologia_manutencao', 'posologia_maxima',
        'registro_anvisa', 'preco_referencia', 'disponivel_brasil',
        'necessita_receita', 'ativo'
    ]
    
    for campo in campos_atualizaveis:
        if campo in data:
            setattr(produto, campo, data[campo])
    
    from models import db
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Produto atualizado',
        'produto': produto.to_dict()
    })


@catalogo_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
@jwt_required_custom
def deletar_produto(produto_id):
    """Inativa um produto (soft delete)"""
    produto = ProdutoCannabis.query.get_or_404(produto_id)
    
    produto.ativo = False
    
    from models import db
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Produto inativado'
    })


# ============================================================================
# ROTAS DE SUGESTÃO E RECOMENDAÇÃO
# ============================================================================

@catalogo_bp.route('/sugerir', methods=['POST'])
@jwt_required_custom
def sugerir_produtos():
    """
    Solicita sugestões de produtos para um paciente
    
    Body (JSON):
    {
        "paciente_id": 123,
        "condicao": "Ansiedade Generalizada",
        "sintomas": "Ansiedade, insônia, tensão muscular",
        "preferencias": {
            "evitar_thc": false,
            "preferencia_cbd": true,
            "via_preferida": "sublingual"
        }
    }
    """
    data = request.get_json()
    
    paciente_id = data.get('paciente_id')
    condicao = data.get('condicao')
    sintomas = data.get('sintomas')
    preferencias = data.get('preferencias', {})
    
    if not paciente_id or not condicao:
        return jsonify({
            'error': 'paciente_id e condicao são obrigatórios'
        }), 400
    
    profissional_id = get_current_profissional_id()
    
    resultado = catalogo_service.sugerir_produtos_prescricao(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        condicao=condicao,
        sintomas=sintomas,
        preferencias=preferencias
    )
    
    if resultado.get('success'):
        return jsonify(resultado), 200
    else:
        return jsonify(resultado), 400


@catalogo_bp.route('/produtos/<int:produto_id>/validar', methods=['POST'])
@jwt_required_custom
def validar_produto(produto_id):
    """
    Valida um produto com o agente farmacêutico
    """
    resultado = catalogo_service.validar_produto_com_farmaceutico(produto_id)
    
    if resultado.get('success'):
        return jsonify(resultado), 200
    else:
        return jsonify(resultado), 400


@catalogo_bp.route('/produtos/comparar', methods=['POST'])
@jwt_required_custom
def comparar_produtos():
    """
    Compara múltiplos produtos
    
    Body (JSON):
    {
        "produto_ids": [1, 2, 3]
    }
    """
    data = request.get_json()
    produto_ids = data.get('produto_ids', [])
    
    if len(produto_ids) < 2:
        return jsonify({
            'error': 'Selecione pelo menos 2 produtos para comparar'
        }), 400
    
    resultado = catalogo_service.comparar_produtos(produto_ids)
    
    if resultado.get('success'):
        return jsonify(resultado), 200
    else:
        return jsonify(resultado), 400


# ============================================================================
# ROTAS DE BUSCA WEB (ATUALIZAÇÕES)
# ============================================================================

@catalogo_bp.route('/atualizacoes-web', methods=['GET'])
@jwt_required_custom
def buscar_atualizacoes_web():
    """
    Busca atualizações de produtos na web
    """
    marca = request.args.get('marca')
    
    resultado = catalogo_service.buscar_atualizacoes_web(marca)
    return jsonify(resultado)


# ============================================================================
# ROTAS DE MARCAS E ESTATÍSTICAS
# ============================================================================

@catalogo_bp.route('/marcas', methods=['GET'])
@jwt_required_custom
def listar_marcas():
    """Lista todas as marcas/fabricantes disponíveis"""
    marcas = db.session.query(ProdutoCannabis.marca).distinct().filter(
        ProdutoCannabis.ativo == True
    ).all()
    
    return jsonify({
        'marcas': [m[0] for m in marcas if m[0]]
    })


@catalogo_bp.route('/categorias', methods=['GET'])
@jwt_required_custom
def listar_categorias():
    """Lista todas as categorias disponíveis"""
    categorias = db.session.query(ProdutoCannabis.categoria).distinct().filter(
        ProdutoCannabis.ativo == True
    ).all()
    
    return jsonify({
        'categorias': [c[0] for c in categorias if c[0]]
    })


@catalogo_bp.route('/estatisticas', methods=['GET'])
@jwt_required_custom
def estatisticas_catalogo():
    """Retorna estatísticas do catálogo"""
    from models import db
    
    total_produtos = ProdutoCannabis.query.filter_by(ativo=True).count()
    total_marcas = db.session.query(ProdutoCannabis.marca).distinct().count()
    total_categorias = db.session.query(ProdutoCannabis.categoria).distinct().count()
    
    # Produtos por quimiotipo
    quimiotipos = db.session.query(
        ProdutoCannabis.quimiotipo,
        db.func.count(ProdutoCannabis.id)
    ).filter_by(ativo=True).group_by(ProdutoCannabis.quimiotipo).all()
    
    # Produtos por marca (top 10)
    top_marcas = db.session.query(
        ProdutoCannabis.marca,
        db.func.count(ProdutoCannabis.id)
    ).filter_by(ativo=True).group_by(ProdutoCannabis.marca).order_by(
        db.func.count(ProdutoCannabis.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'total_produtos': total_produtos,
        'total_marcas': total_marcas,
        'total_categorias': total_categorias,
        'produtos_por_quimiotipo': [
            {'quimiotipo': q[0], 'quantidade': q[1]} for q in quimiotipos
        ],
        'top_marcas': [
            {'marca': m[0], 'quantidade': m[1]} for m in top_marcas
        ]
    })


# ============================================================================
# ROTAS DE SUGESTÕES HISTÓRICAS
# ============================================================================

@catalogo_bp.route('/sugestoes', methods=['GET'])
@jwt_required_custom
def listar_sugestoes():
    """Lista histórico de sugestões de prescrição"""
    paciente_id = request.args.get('paciente_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = SugestaoPrescricao.query.order_by(SugestaoPrescricao.created_at.desc())
    
    if paciente_id:
        query = query.filter_by(paciente_id=paciente_id)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'sugestoes': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

# ============================================================================
# ROTAS DE EXTRAÇÃO POR IA (SGA → SIAP) — Feature Flag: sga_catalog_extraction
# ============================================================================

from services.catalogo_extraction_service import extraction_service
from services.feature_flag_service import feature_required
from models_extra import CatalogoImportLog


@catalogo_bp.route('/extrair-ia', methods=['POST'])
@jwt_required_custom
@feature_required('sga_catalog_extraction')
def extrair_catalogo_ia():
    """
    Extrai produtos de um arquivo (PDF, PNG, JPG, XLSX) usando IA.
    
    Form-data:
    - arquivo: arquivo a ser enviado
    
    Retorna JSON: {detected_products: [...], count: N}
    Rate limit: 10 extrações/dia no trial.
    """
    if 'arquivo' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['arquivo']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.xlsx', '.xls'}
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed_extensions:
        return jsonify({
            'error': 'Formato não suportado. Use: PDF, PNG, JPG, XLSX'
        }), 400
    
    file_bytes = file.read()
    if len(file_bytes) > 20 * 1024 * 1024:  # 20MB max
        return jsonify({'error': 'Arquivo muito grande. Máximo 20MB.'}), 400
    
    user_id = get_current_profissional_id()
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    result = extraction_service.extract_from_file(
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=file.mimetype,
        user_id=int(user_id)
    )
    
    if result.get('error') and result.get('count') == 0:
        status_code = 429 if 'Limite diário' in result.get('message', '') else 400
        return jsonify(result), status_code
    
    return jsonify(result), 200


@catalogo_bp.route('/importar-selecionados', methods=['POST'])
@jwt_required_custom
@feature_required('sga_catalog_extraction')
def importar_produtos_selecionados():
    """
    Importa produtos selecionados para o estoque SIAP.
    
    Body (JSON):
    {
        "produtos": [
            {"nome": "...", "categoria": "...", "descricao": "...", "unidade": "...", ...},
            ...
        ]
    }
    """
    data = request.get_json()
    if not data or not isinstance(data.get('produtos'), list):
        return jsonify({'error': 'Envie um array de produtos em "produtos"'}), 400
    
    user_id = get_current_profissional_id()
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    result = extraction_service.import_products(
        products=data['produtos'],
        user_id=int(user_id)
    )
    
    if result.get('success'):
        return jsonify(result), 201
    return jsonify(result), 400


@catalogo_bp.route('/import-logs', methods=['GET'])
@jwt_required_custom
@feature_required('sga_catalog_extraction')
def listar_import_logs():
    """
    Lista logs de importação de catálogo (admin).
    
    Query params:
    - page: página (default 1)
    - per_page: itens por página (default 20)
    """
    from models import Profissional
    
    user_id = get_current_profissional_id()
    profissional = Profissional.query.get(user_id) if user_id else None
    
    # Apenas admin pode ver todos os logs; profissionais veem só os seus
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = CatalogoImportLog.query.order_by(CatalogoImportLog.created_at.desc())
    
    if not profissional or profissional.role != 'admin':
        query = query.filter_by(user_id=user_id)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })
