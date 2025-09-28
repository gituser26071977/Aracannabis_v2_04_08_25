"""
Rotas para cadastro de profissionais
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
import sqlite3
import os
import re
import secrets
import string
from datetime import datetime, timedelta
from services.email_service import email_service

cadastro_profissionais_bp = Blueprint('cadastro_profissionais', __name__)

def get_db_connection():
    """Conectar ao banco de dados SQLite"""
    db_path = os.path.join('instance', 'aracannabis.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def validar_crm(crm, uf):
    """Validar formato do CRM"""
    if not crm or not uf:
        return False
    
    # Remover espaços e caracteres especiais
    crm_clean = re.sub(r'[^\d]', '', crm)
    
    # CRM deve ter entre 4 e 6 dígitos
    if len(crm_clean) < 4 or len(crm_clean) > 6:
        return False
    
    # UF deve ter 2 caracteres
    if len(uf) != 2:
        return False
    
    return True

def validar_email(email):
    """Validar formato do email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def gerar_senha_temporaria():
    """Gerar senha temporária segura"""
    # Gerar senha com 12 caracteres: letras maiúsculas, minúsculas e números
    alphabet = string.ascii_letters + string.digits
    senha = ''.join(secrets.choice(alphabet) for _ in range(12))
    return senha

@cadastro_profissionais_bp.route('/solicitar-cadastro', methods=['POST'])
def solicitar_cadastro():
    """Solicitar cadastro de novo profissional"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['nome', 'email', 'crm', 'uf_crm']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400
        
        nome = data['nome'].strip()
        email = data['email'].strip().lower()
        crm = data['crm'].strip()
        uf_crm = data['uf_crm'].strip().upper()
        telefone = data.get('telefone', '').strip()
        especialidade = data.get('especialidade', '').strip()
        instituicao = data.get('instituicao', '').strip()
        
        # Validações
        if len(nome) < 2:
            return jsonify({
                'success': False,
                'error': 'Nome deve ter pelo menos 2 caracteres'
            }), 400
        
        if not validar_email(email):
            return jsonify({
                'success': False,
                'error': 'Email inválido'
            }), 400
        
        if not validar_crm(crm, uf_crm):
            return jsonify({
                'success': False,
                'error': 'CRM ou UF inválidos'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Verificar se email já existe
            cursor.execute(
                'SELECT id FROM solicitacoes_cadastro WHERE email = ?',
                (email,)
            )
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Email já cadastrado'
                }), 400
            
            # Verificar se CRM já existe
            cursor.execute(
                'SELECT id FROM solicitacoes_cadastro WHERE crm = ? AND uf_crm = ?',
                (crm, uf_crm)
            )
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'CRM já cadastrado'
                }), 400
            
            # Verificar se já existe na tabela de profissionais
            cursor.execute(
                'SELECT id FROM profissionais WHERE crm = ? AND uf_crm = ?',
                (crm, uf_crm)
            )
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'CRM já cadastrado no sistema'
                }), 400
            
            # Inserir solicitação
            cursor.execute('''
                INSERT INTO solicitacoes_cadastro 
                (nome, email, crm, uf_crm, telefone, especialidade, instituicao, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pendente')
            ''', (nome, email, crm, uf_crm, telefone, especialidade, instituicao))
            
            solicitacao_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Solicitação de cadastro enviada com sucesso',
                'solicitacao_id': solicitacao_id
            })
            
        finally:
            conn.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro ao solicitar cadastro: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@cadastro_profissionais_bp.route('/listar-solicitacoes', methods=['GET'])
def listar_solicitacoes():
    """Listar solicitações de cadastro (apenas para admins)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                s.*,
                p.nome as aprovado_por_nome
            FROM solicitacoes_cadastro s
            LEFT JOIN profissionais p ON s.aprovado_por = p.id
            ORDER BY s.data_solicitacao DESC
        ''')
        
        solicitacoes = []
        for row in cursor.fetchall():
            solicitacoes.append({
                'id': row['id'],
                'nome': row['nome'],
                'email': row['email'],
                'crm': row['crm'],
                'uf_crm': row['uf_crm'],
                'telefone': row['telefone'],
                'especialidade': row['especialidade'],
                'instituicao': row['instituicao'],
                'status': row['status'],
                'data_solicitacao': row['data_solicitacao'],
                'data_aprovacao': row['data_aprovacao'],
                'observacoes': row['observacoes'],
                'aprovado_por_nome': row['aprovado_por_nome']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'solicitacoes': solicitacoes
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar solicitações: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@cadastro_profissionais_bp.route('/aprovar-solicitacao/<int:solicitacao_id>', methods=['POST'])
def aprovar_solicitacao(solicitacao_id):
    """Aprovar solicitação e criar conta temporária"""
    try:
        data = request.get_json()
        observacoes = data.get('observacoes', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Buscar solicitação
            cursor.execute(
                'SELECT * FROM solicitacoes_cadastro WHERE id = ? AND status = "pendente"',
                (solicitacao_id,)
            )
            solicitacao = cursor.fetchone()
            
            if not solicitacao:
                return jsonify({
                    'success': False,
                    'error': 'Solicitação não encontrada ou já processada'
                }), 404
            
            # Gerar senha temporária
            senha_temporaria = gerar_senha_temporaria()
            senha_hash = generate_password_hash(senha_temporaria)
            
            # Gerar nome de usuário único
            usuario_base = solicitacao['email'].split('@')[0]
            usuario = usuario_base
            contador = 1
            
            while True:
                cursor.execute('SELECT id FROM profissionais WHERE usuario = ?', (usuario,))
                if not cursor.fetchone():
                    break
                usuario = f"{usuario_base}{contador}"
                contador += 1
            
            data_expiracao = datetime.now() + timedelta(days=7)
            
            # Criar profissional
            cursor.execute('''
                INSERT INTO profissionais 
                (nome, crm, uf_crm, usuario, senha, email, telefone, especialidade, instituicao, 
                 ativo, tipo_conta, data_expiracao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'temporaria', ?)
            ''', (
                solicitacao['nome'],
                solicitacao['crm'],
                solicitacao['uf_crm'],
                usuario,
                senha_hash,
                solicitacao['email'],
                solicitacao['telefone'],
                solicitacao['especialidade'],
                solicitacao['instituicao'],
                data_expiracao.isoformat()
            ))
            
            profissional_id = cursor.lastrowid
            
            # Criar registro de senha temporária
            cursor.execute('''
                INSERT INTO senhas_temporarias 
                (usuario_id, senha_hash, data_expiracao, usado)
                VALUES (?, ?, ?, 0)
            ''', (
                profissional_id,
                senha_hash,
                data_expiracao.isoformat()
            ))
            
            # Atualizar solicitação
            cursor.execute('''
                UPDATE solicitacoes_cadastro 
                SET status = 'aprovada', data_aprovacao = ?, observacoes = ?, aprovado_por = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), observacoes, 1, solicitacao_id))  # TODO: usar ID do admin logado
            
            conn.commit()
            
            # Enviar email real
            email_enviado = email_service.send_approval_email(
                solicitacao['email'], 
                solicitacao['nome'], 
                usuario, 
                senha_temporaria, 
                data_expiracao
            )
            
            if not email_enviado:
                current_app.logger.warning(f"Falha ao enviar email para {solicitacao['email']}")
                # Continuar mesmo se o email falhar
            
            return jsonify({
                'success': True,
                'message': 'Solicitação aprovada e conta criada com sucesso',
                'profissional_id': profissional_id,
                'usuario': usuario,
                'email_enviado': email_enviado,
                'data_expiracao': data_expiracao.isoformat()
            })
            
        finally:
            conn.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro ao aprovar solicitação: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@cadastro_profissionais_bp.route('/rejeitar-solicitacao/<int:solicitacao_id>', methods=['POST'])
def rejeitar_solicitacao(solicitacao_id):
    """Rejeitar solicitação de cadastro"""
    try:
        data = request.get_json()
        observacoes = data.get('observacoes', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Buscar solicitação
            cursor.execute(
                'SELECT * FROM solicitacoes_cadastro WHERE id = ? AND status = "pendente"',
                (solicitacao_id,)
            )
            solicitacao = cursor.fetchone()
            
            if not solicitacao:
                return jsonify({
                    'success': False,
                    'error': 'Solicitação não encontrada ou já processada'
                }), 404
            
            # Atualizar solicitação
            cursor.execute('''
                UPDATE solicitacoes_cadastro 
                SET status = 'rejeitada', observacoes = ?, aprovado_por = ?
                WHERE id = ?
            ''', (observacoes, 1, solicitacao_id))  # TODO: usar ID do admin logado
            
            conn.commit()
            
            # Enviar email de rejeição
            email_enviado = email_service.send_rejection_email(
                solicitacao['email'], 
                solicitacao['nome'], 
                observacoes
            )
            
            if not email_enviado:
                current_app.logger.warning(f"Falha ao enviar email de rejeição para {solicitacao['email']}")
            
            return jsonify({
                'success': True,
                'message': 'Solicitação rejeitada com sucesso',
                'email_enviado': email_enviado
            })
            
        finally:
            conn.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro ao rejeitar solicitação: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@cadastro_profissionais_bp.route('/status-solicitacao/<email>', methods=['GET'])
def status_solicitacao(email):
    """Verificar status de solicitação por email"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT status, data_solicitacao, data_aprovacao, observacoes FROM solicitacoes_cadastro WHERE email = ?',
            (email.lower(),)
        )
        
        solicitacao = cursor.fetchone()
        conn.close()
        
        if not solicitacao:
            return jsonify({
                'success': False,
                'error': 'Solicitação não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'status': solicitacao['status'],
            'data_solicitacao': solicitacao['data_solicitacao'],
            'data_aprovacao': solicitacao['data_aprovacao'],
            'observacoes': solicitacao['observacoes']
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar status: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@cadastro_profissionais_bp.route('/testar-email', methods=['POST'])
def testar_email():
    """Testar configuração de email"""
    try:
        success, message = email_service.test_connection()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao testar email: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500
