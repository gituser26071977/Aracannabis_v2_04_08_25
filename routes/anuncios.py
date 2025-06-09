from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import sqlite3
import json
from datetime import datetime, timedelta
import os

anuncios_bp = Blueprint('anuncios', __name__)

def get_db_connection():
    """Conecta ao banco de dados"""
    try:
        conn = sqlite3.connect('instance/aracannabis.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        current_app.logger.error(f"Erro ao conectar ao banco: {e}")
        return None

def init_anuncios_table():
    """Inicializa a tabela de anúncios"""
    conn = get_db_connection()
    if conn:
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS anuncios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    imagem TEXT,
                    url TEXT NOT NULL,
                    empresa TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    preco TEXT,
                    destaque TEXT,
                    tipo TEXT NOT NULL,
                    ativo BOOLEAN DEFAULT 1,
                    data_inicio DATE,
                    data_fim DATE,
                    visualizacoes INTEGER DEFAULT 0,
                    cliques INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar tabela de analytics de anúncios
            conn.execute('''
                CREATE TABLE IF NOT EXISTS anuncios_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anuncio_id INTEGER,
                    tipo_evento TEXT NOT NULL, -- 'view' ou 'click'
                    user_agent TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (anuncio_id) REFERENCES anuncios (id)
                )
            ''')
            
            conn.commit()
            
            # Inserir anúncios de exemplo se a tabela estiver vazia
            cursor = conn.execute('SELECT COUNT(*) FROM anuncios')
            count = cursor.fetchone()[0]
            
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
                        'data_inicio': datetime.now().strftime('%Y-%m-%d'),
                        'data_fim': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
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
                        'data_inicio': datetime.now().strftime('%Y-%m-%d'),
                        'data_fim': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
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
                        'data_inicio': datetime.now().strftime('%Y-%m-%d'),
                        'data_fim': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
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
                        'data_inicio': datetime.now().strftime('%Y-%m-%d'),
                        'data_fim': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
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
                        'data_inicio': datetime.now().strftime('%Y-%m-%d'),
                        'data_fim': (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d')
                    }
                ]
                
                for anuncio in anuncios_exemplo:
                    conn.execute('''
                        INSERT INTO anuncios (titulo, descricao, imagem, url, empresa, categoria, preco, destaque, tipo, data_inicio, data_fim)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        anuncio['titulo'], anuncio['descricao'], anuncio['imagem'], anuncio['url'],
                        anuncio['empresa'], anuncio['categoria'], anuncio['preco'], anuncio['destaque'],
                        anuncio['tipo'], anuncio['data_inicio'], anuncio['data_fim']
                    ))
                
                conn.commit()
                current_app.logger.info("Anúncios de exemplo inseridos com sucesso")
            
        except Exception as e:
            current_app.logger.error(f"Erro ao inicializar tabela de anúncios: {e}")
        finally:
            conn.close()

@anuncios_bp.route('/api/anuncios', methods=['GET'])
@cross_origin()
def listar_anuncios():
    """Lista anúncios ativos"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco de dados'}), 500
        
        # Parâmetros de consulta
        limite = request.args.get('limite', 5, type=int)
        categoria = request.args.get('categoria')
        tipo = request.args.get('tipo')
        
        # Query base
        query = '''
            SELECT * FROM anuncios 
            WHERE ativo = 1 
            AND (data_inicio IS NULL OR data_inicio <= date('now'))
            AND (data_fim IS NULL OR data_fim >= date('now'))
        '''
        params = []
        
        # Filtros opcionais
        if categoria:
            query += ' AND categoria = ?'
            params.append(categoria)
        
        if tipo:
            query += ' AND tipo = ?'
            params.append(tipo)
        
        # Ordenação e limite
        query += ' ORDER BY RANDOM() LIMIT ?'
        params.append(limite)
        
        cursor = conn.execute(query, params)
        anuncios = []
        
        for row in cursor.fetchall():
            anuncio = {
                'id': row['id'],
                'title': row['titulo'],
                'description': row['descricao'],
                'image': row['imagem'],
                'url': row['url'],
                'company': row['empresa'],
                'category': row['categoria'],
                'price': row['preco'],
                'highlight': row['destaque'],
                'type': row['tipo'],
                'views': row['visualizacoes'],
                'clicks': row['cliques']
            }
            anuncios.append(anuncio)
        
        conn.close()
        return jsonify(anuncios)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar anúncios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@anuncios_bp.route('/api/anuncios/<int:anuncio_id>/view', methods=['POST'])
@cross_origin()
def registrar_visualizacao(anuncio_id):
    """Registra visualização de anúncio"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco de dados'}), 500
        
        # Incrementar contador de visualizações
        conn.execute('UPDATE anuncios SET visualizacoes = visualizacoes + 1 WHERE id = ?', (anuncio_id,))
        
        # Registrar analytics
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        
        conn.execute('''
            INSERT INTO anuncios_analytics (anuncio_id, tipo_evento, user_agent, ip_address)
            VALUES (?, 'view', ?, ?)
        ''', (anuncio_id, user_agent, ip_address))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Erro ao registrar visualização: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@anuncios_bp.route('/api/anuncios/<int:anuncio_id>/click', methods=['POST'])
@cross_origin()
def registrar_clique(anuncio_id):
    """Registra clique em anúncio"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco de dados'}), 500
        
        # Incrementar contador de cliques
        conn.execute('UPDATE anuncios SET cliques = cliques + 1 WHERE id = ?', (anuncio_id,))
        
        # Registrar analytics
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        
        conn.execute('''
            INSERT INTO anuncios_analytics (anuncio_id, tipo_evento, user_agent, ip_address)
            VALUES (?, 'click', ?, ?)
        ''', (anuncio_id, user_agent, ip_address))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Erro ao registrar clique: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@anuncios_bp.route('/api/anuncios/stats', methods=['GET'])
@cross_origin()
def estatisticas_anuncios():
    """Retorna estatísticas dos anúncios"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco de dados'}), 500
        
        # Estatísticas gerais
        cursor = conn.execute('''
            SELECT 
                COUNT(*) as total_anuncios,
                SUM(visualizacoes) as total_visualizacoes,
                SUM(cliques) as total_cliques,
                AVG(CAST(cliques AS FLOAT) / NULLIF(visualizacoes, 0)) as ctr_medio
            FROM anuncios 
            WHERE ativo = 1
        ''')
        stats_gerais = cursor.fetchone()
        
        # Top anúncios por cliques
        cursor = conn.execute('''
            SELECT titulo, empresa, cliques, visualizacoes
            FROM anuncios 
            WHERE ativo = 1
            ORDER BY cliques DESC
            LIMIT 5
        ''')
        top_anuncios = cursor.fetchall()
        
        # Estatísticas por categoria
        cursor = conn.execute('''
            SELECT categoria, COUNT(*) as quantidade, SUM(cliques) as cliques
            FROM anuncios 
            WHERE ativo = 1
            GROUP BY categoria
            ORDER BY cliques DESC
        ''')
        stats_categoria = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'geral': {
                'total_anuncios': stats_gerais['total_anuncios'],
                'total_visualizacoes': stats_gerais['total_visualizacoes'] or 0,
                'total_cliques': stats_gerais['total_cliques'] or 0,
                'ctr_medio': round(stats_gerais['ctr_medio'] or 0, 4)
            },
            'top_anuncios': [dict(row) for row in top_anuncios],
            'por_categoria': [dict(row) for row in stats_categoria]
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# A inicialização será feita no app.py após registrar o blueprint
