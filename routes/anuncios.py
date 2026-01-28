from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from models import db
from datetime import datetime, timedelta
import os

anuncios_bp = Blueprint('anuncios', __name__)

# Modelo SQLAlchemy para anúncios
class Anuncio(db.Model):
    __tablename__ = 'anuncios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    imagem = db.Column(db.String(255))
    url = db.Column(db.String(500), nullable=False)
    empresa = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.String(100))
    destaque = db.Column(db.String(255))
    tipo = db.Column(db.String(50), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    visualizacoes = db.Column(db.Integer, default=0)
    cliques = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Modelo para analytics de anúncios
class AnuncioAnalytics(db.Model):
    __tablename__ = 'anuncios_analytics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    anuncio_id = db.Column(db.Integer, db.ForeignKey('anuncios.id'), nullable=False)
    tipo_evento = db.Column(db.String(20), nullable=False)  # 'view' ou 'click'
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    anuncio = db.relationship('Anuncio', backref=db.backref('analytics', lazy=True))

def init_anuncios_table():
    """Inicializa a tabela de anúncios com dados de exemplo"""
    try:
        # Verificar se já existem anúncios
        count = Anuncio.query.count()

        if count == 0:
            anuncios_exemplo = [
                {
                    'titulo': 'Cannabis Premium - Óleos Medicinais',
                    'descricao': 'Óleos de CBD e THC de alta qualidade para tratamentos terapêuticos. Certificados e testados em laboratório.',
                    'imagem': '/Oelo.png',
                    'url': 'https://example.com/cannabis-premium',
                    'empresa': 'Cannabis Premium Ltda',
                    'categoria': 'Produtos',
                    'preco': 'A partir de R$ 150,00',
                    'destaque': 'Entrega em todo Brasil',
                    'tipo': 'product',
                    'data_inicio': datetime.now().date(),
                    'data_fim': (datetime.now() + timedelta(days=30)).date()
                },
                {
                    'titulo': 'Curso de Cannabis Medicinal',
                    'descricao': 'Capacitação completa para profissionais de saúde. Certificado reconhecido pelo CFM.',
                    'imagem': '/Flor óleo.jpeg',
                    'url': 'https://example.com/curso-cannabis',
                    'empresa': 'Instituto Cannabis Brasil',
                    'categoria': 'Educação',
                    'preco': 'R$ 890,00',
                    'destaque': '100% Online',
                    'tipo': 'course',
                    'data_inicio': datetime.now().date(),
                    'data_fim': (datetime.now() + timedelta(days=60)).date()
                },
                {
                    'titulo': 'Laboratório de Análises Canábicas',
                    'descricao': 'Análises completas de potência, pesticidas e metais pesados. Laudos técnicos certificados.',
                    'imagem': '/Aracannabis.png',
                    'url': 'https://example.com/laboratorio',
                    'empresa': 'CannaLab Análises',
                    'categoria': 'Serviços',
                    'preco': 'Consulte preços',
                    'destaque': 'Resultados em 48h',
                    'tipo': 'service',
                    'data_inicio': datetime.now().date(),
                    'data_fim': (datetime.now() + timedelta(days=90)).date()
                },
                {
                    'titulo': 'Equipamentos para Cultivo',
                    'descricao': 'LED grow lights, estufas, sistemas de irrigação e todos os equipamentos para cultivo medicinal.',
                    'imagem': '/Aracannabis.png',
                    'url': 'https://example.com/equipamentos',
                    'empresa': 'GrowTech Brasil',
                    'categoria': 'Equipamentos',
                    'preco': 'Promoção 20% OFF',
                    'destaque': 'Frete Grátis',
                    'tipo': 'equipment',
                    'data_inicio': datetime.now().date(),
                    'data_fim': (datetime.now() + timedelta(days=45)).date()
                },
                {
                    'titulo': 'Consultoria Jurídica Cannabis',
                    'descricao': 'Assessoria jurídica especializada em cannabis medicinal. Habeas corpus e licenças.',
                    'imagem': '/Aracannabis.png',
                    'url': 'https://example.com/juridico',
                    'empresa': 'Cannabis Legal Advocacia',
                    'categoria': 'Jurídico',
                    'preco': 'Consulta gratuita',
                    'destaque': 'Especialistas em Cannabis',
                    'tipo': 'legal',
                    'data_inicio': datetime.now().date(),
                    'data_fim': (datetime.now() + timedelta(days=120)).date()
                }
            ]

            for anuncio_data in anuncios_exemplo:
                anuncio = Anuncio(**anuncio_data)
                db.session.add(anuncio)

            db.session.commit()
            current_app.logger.info("Anúncios de exemplo inseridos com sucesso")

    except Exception as e:
        current_app.logger.error(f"Erro ao inicializar tabela de anúncios: {e}")
        db.session.rollback()

@anuncios_bp.route('/anuncios', methods=['GET'])
@cross_origin()
def listar_anuncios():
    """Lista anúncios ativos"""
    try:
        # Parâmetros de consulta
        limite = request.args.get('limite', 5, type=int)
        categoria = request.args.get('categoria')
        tipo = request.args.get('tipo')

        # Query base usando SQLAlchemy
        query = Anuncio.query.filter(
            Anuncio.ativo == True,
            (Anuncio.data_inicio.is_(None) | (Anuncio.data_inicio <= datetime.now().date())),
            (Anuncio.data_fim.is_(None) | (Anuncio.data_fim >= datetime.now().date()))
        )

        # Filtros opcionais
        if categoria:
            query = query.filter(Anuncio.categoria == categoria)

        if tipo:
            query = query.filter(Anuncio.tipo == tipo)

        # Ordenação aleatória e limite
        anuncios_db = query.order_by(db.func.random()).limit(limite).all()

        anuncios = []
        for anuncio in anuncios_db:
            anuncios.append({
                'id': anuncio.id,
                'title': anuncio.titulo,
                'description': anuncio.descricao,
                'image': anuncio.imagem,
                'url': anuncio.url,
                'company': anuncio.empresa,
                'category': anuncio.categoria,
                'price': anuncio.preco,
                'highlight': anuncio.destaque,
                'type': anuncio.tipo,
                'views': anuncio.visualizacoes,
                'clicks': anuncio.cliques
            })

        return jsonify(anuncios)

    except Exception as e:
        current_app.logger.error(f"Erro ao listar anúncios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@anuncios_bp.route('/anuncios/<int:anuncio_id>/view', methods=['POST'])
@cross_origin()
def registrar_visualizacao(anuncio_id):
    """Registra visualização de anúncio"""
    try:
        # Buscar anúncio
        anuncio = Anuncio.query.get(anuncio_id)
        if not anuncio:
            return jsonify({'error': 'Anúncio não encontrado'}), 404

        # Incrementar contador de visualizações
        anuncio.visualizacoes += 1

        # Registrar analytics
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr

        analytics = AnuncioAnalytics(
            anuncio_id=anuncio_id,
            tipo_evento='view',
            user_agent=user_agent,
            ip_address=ip_address
        )

        db.session.add(analytics)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        current_app.logger.error(f"Erro ao registrar visualização: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@anuncios_bp.route('/anuncios/<int:anuncio_id>/click', methods=['POST'])
@cross_origin()
def registrar_clique(anuncio_id):
    """Registra clique em anúncio"""
    try:
        # Buscar anúncio
        anuncio = Anuncio.query.get(anuncio_id)
        if not anuncio:
            return jsonify({'error': 'Anúncio não encontrado'}), 404

        # Incrementar contador de cliques
        anuncio.cliques += 1

        # Registrar analytics
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr

        analytics = AnuncioAnalytics(
            anuncio_id=anuncio_id,
            tipo_evento='click',
            user_agent=user_agent,
            ip_address=ip_address
        )

        db.session.add(analytics)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        current_app.logger.error(f"Erro ao registrar clique: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@anuncios_bp.route('/anuncios/stats', methods=['GET'])
@cross_origin()
def estatisticas_anuncios():
    """Retorna estatísticas dos anúncios"""
    try:
        from sqlalchemy import func

        # Estatísticas gerais usando SQLAlchemy
        stats_query = db.session.query(
            func.count(Anuncio.id).label('total_anuncios'),
            func.sum(Anuncio.visualizacoes).label('total_visualizacoes'),
            func.sum(Anuncio.cliques).label('total_cliques'),
            func.avg(Anuncio.cliques.cast(db.Float) / func.nullif(Anuncio.visualizacoes, 0)).label('ctr_medio')
        ).filter(Anuncio.ativo == True)

        stats_gerais = stats_query.first()

        # Top anúncios por cliques
        top_anuncios = Anuncio.query.filter(Anuncio.ativo == True)\
            .order_by(Anuncio.cliques.desc())\
            .limit(5)\
            .with_entities(Anuncio.titulo, Anuncio.empresa, Anuncio.cliques, Anuncio.visualizacoes)\
            .all()

        # Estatísticas por categoria
        categoria_query = db.session.query(
            Anuncio.categoria,
            func.count(Anuncio.id).label('quantidade'),
            func.sum(Anuncio.cliques).label('cliques')
        ).filter(Anuncio.ativo == True)\
         .group_by(Anuncio.categoria)\
         .order_by(func.sum(Anuncio.cliques).desc())

        stats_categoria = categoria_query.all()

        return jsonify({
            'geral': {
                'total_anuncios': stats_gerais.total_anuncios,
                'total_visualizacoes': stats_gerais.total_visualizacoes or 0,
                'total_cliques': stats_gerais.total_cliques or 0,
                'ctr_medio': round(stats_gerais.ctr_medio or 0, 4)
            },
            'top_anuncios': [
                {
                    'titulo': anuncio.titulo,
                    'empresa': anuncio.empresa,
                    'cliques': anuncio.cliques,
                    'visualizacoes': anuncio.visualizacoes
                } for anuncio in top_anuncios
            ],
            'por_categoria': [
                {
                    'categoria': stat.categoria,
                    'quantidade': stat.quantidade,
                    'cliques': stat.cliques or 0
                } for stat in stats_categoria
            ]
        })

    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# A inicialização será feita no app.py após registrar o blueprint
