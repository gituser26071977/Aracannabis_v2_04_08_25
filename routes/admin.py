"""
Rotas administrativas do sistema Aracannabis.
Acesso restrito a usuários com role 'admin'.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import desc
import datetime
import os

from models import db, Profissional, LogAtividade, Paciente, Exame, Consulta, Evolucao
from security_config import sanitize_input, mask_sensitive_data

admin_bp = Blueprint('admin', __name__)

# Middleware para verificar permissões de admin
def admin_required(f):
    """Decorator para verificar se o usuário é administrador"""
    from functools import wraps

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        """Verifica permissão de admin usando claims do token e fallback no banco.

        Isso evita falsos negativos quando o usuário existe e tem role 'admin',
        mas há algum descompasso entre ambiente/token/banco.
        """
        try:
            claims = get_jwt()
        except Exception:
            claims = {}

        role_token = claims.get('role')
        current_user_id = get_jwt_identity()

        profissional = None
        role_db = None
        try:
            if current_user_id is not None:
                profissional = Profissional.query.get(int(current_user_id))
                if profissional:
                    role_db = profissional.role
        except Exception:
            # Em caso de erro de banco, mantemos role_db = None
            profissional = None

        # Regra de decisão:
        # 1) Se o token declara role=admin, confia nisso.
        # 2) Caso contrário, usa o papel salvo no banco.
        effective_role = role_token or role_db

        if effective_role != 'admin':
            return jsonify({'error': 'Acesso negado. Permissão de administrador necessária.'}), 403

        return f(*args, **kwargs)

    return decorated_function

@admin_bp.route('/dashboard-stats', methods=['GET'])
@admin_required
def dashboard_stats():
    """Retorna estatísticas do sistema para o dashboard administrativo"""
    try:
        # Contagem de usuários
        total_profissionais = Profissional.query.count()
        admin_count = Profissional.query.filter_by(role='admin').count()
        profissional_count = Profissional.query.filter_by(role='profissional').count()
        
        # Contagem de pacientes
        total_pacientes = Paciente.query.count()
        pacientes_em_tratamento = Paciente.query.filter_by(em_tratamento=True).count()
        
        # Contagem de dados clínicos
        total_exames = Exame.query.count()
        total_consultas = Consulta.query.count()
        total_evolucoes = Evolucao.query.count()
        
        # Últimos 7 dias
        sete_dias_atras = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        
        # Atividade recente
        novos_pacientes_7dias = Paciente.query.filter(
            Paciente.created_at >= sete_dias_atras
        ).count()
        
        novas_consultas_7dias = Consulta.query.filter(
            Consulta.created_at >= sete_dias_atras
        ).count()
        
        return jsonify({
            'stats': {
                'usuarios': {
                    'total': total_profissionais,
                    'admins': admin_count,
                    'profissionais': profissional_count
                },
                'pacientes': {
                    'total': total_pacientes,
                    'em_tratamento': pacientes_em_tratamento
                },
                'clinicos': {
                    'exames': total_exames,
                    'consultas': total_consultas,
                    'evolucoes': total_evolucoes
                },
                'atividade_recente': {
                    'novos_pacientes_7dias': novos_pacientes_7dias,
                    'novas_consultas_7dias': novas_consultas_7dias
                }
            },
            'updated_at': datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter estatísticas: {str(e)}'}), 500

@admin_bp.route('/usuarios', methods=['GET'])
@admin_required
def listar_usuarios():
    """Lista todos os usuários do sistema"""
    try:
        usuarios = Profissional.query.order_by(Profissional.created_at.desc()).all()
        
        usuarios_list = []
        for user in usuarios:
            user_data = user.to_dict()
            # Mascarar informações sensíveis
            user_data['usuario_mascarado'] = mask_sensitive_data(user.usuario, 'email')
            user_data['crm_mascarado'] = mask_sensitive_data(user.crm, 'cpf')
            
            # Contagem de atividades do usuário
            user_data['total_pacientes'] = len([p for p in user.pacientes_responsavel])
            user_data['total_consultas'] = len(user.consultas)
            user_data['total_exames'] = len(user.exames)
            
            # --- NOVAS INFORMAÇÕES PARA DASHBOARD ---
            
            # Buscar assinatura
            # Importar aqui para evitar circular imports se necessário, ou garantir que estão no topo
            from models import Assinatura
            
            assinatura = Assinatura.query.filter_by(profissional_id=user.id).order_by(Assinatura.created_at.desc()).first()
            if assinatura and assinatura.plano:
                user_data['plano'] = assinatura.plano.nome
                user_data['status_assinatura'] = assinatura.status
            else:
                user_data['plano'] = 'Trial/Gratuito'
                user_data['status_assinatura'] = 'trial'

            # Buscar último acesso (Log mais recente)
            ultimo_log = LogAtividade.query.filter_by(profissional_id=user.id).order_by(LogAtividade.data_hora.desc()).first()
            user_data['ultimo_acesso'] = ultimo_log.data_hora.isoformat() if ultimo_log else None
            
            # Dias de cadastro
            if user.created_at:
                dias = (datetime.datetime.utcnow() - user.created_at).days
                user_data['dias_cadastro'] = dias
            else:
                user_data['dias_cadastro'] = 0
            
            usuarios_list.append(user_data)
        
        return jsonify({
            'usuarios': usuarios_list,
            'total': len(usuarios_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar usuários: {str(e)}'}), 500

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
@admin_required
def obter_usuario(usuario_id):
    """Obtém detalhes de um usuário específico"""
    try:
        usuario = Profissional.query.get(usuario_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        user_data = usuario.to_dict()
        
        # Adicionar informações adicionais
        user_data['pacientes_responsavel'] = [
            {'id': p.id, 'nome': p.nome} 
            for p in usuario.pacientes_responsavel[:10]  # Limitar a 10
        ]
        
        # Logs de atividade recentes
        logs_recentes = LogAtividade.query.filter_by(
            profissional_id=usuario_id
        ).order_by(desc(LogAtividade.data_hora)).limit(10).all()
        
        user_data['logs_recentes'] = [
            {'acao': log.acao, 'data_hora': log.data_hora.isoformat(), 'detalhes': log.detalhes}
            for log in logs_recentes
        ]
        
        return jsonify({'usuario': user_data}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter usuário: {str(e)}'}), 500

@admin_bp.route('/usuarios/<int:usuario_id>/role', methods=['PUT'])
@admin_required
def atualizar_role_usuario(usuario_id):
    """Atualiza a role de um usuário"""
    try:
        data = request.get_json()
        if 'role' not in data:
            return jsonify({'error': 'Campo role é obrigatório'}), 400
        
        role = data['role']
        if role not in ['admin', 'profissional', 'auxiliar']:
            return jsonify({'error': 'Role inválida. Valores permitidos: admin, profissional, auxiliar'}), 400
        
        # Não permitir alterar o próprio role
        current_user_id = int(get_jwt_identity())
        if usuario_id == current_user_id:
            return jsonify({'error': 'Não é permitido alterar a própria role'}), 400
        
        usuario = Profissional.query.get(usuario_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        old_role = usuario.role
        usuario.role = role
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='ALTERAR_ROLE',
            detalhes=f'Role alterada de {old_role} para {role} para usuário {usuario.usuario} (ID: {usuario_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Role atualizada com sucesso',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar role: {str(e)}'}), 500

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
@admin_required
def deletar_usuario(usuario_id):
    """Remove um usuário do sistema"""
    try:
        # Não permitir deletar a si mesmo
        current_user_id = int(get_jwt_identity())
        if usuario_id == current_user_id:
            return jsonify({'error': 'Não é permitido remover o próprio usuário'}), 400
        
        usuario = Profissional.query.get(usuario_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Verificar se o usuário tem pacientes associados
        if usuario.pacientes_responsavel:
            return jsonify({
                'error': 'Não é possível remover usuário com pacientes associados',
                'total_pacientes': len(usuario.pacientes_responsavel)
            }), 400
        
        # Registrar log antes de deletar
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='REMOVER_USUARIO',
            detalhes=f'Usuário {usuario.usuario} (ID: {usuario_id}) removido do sistema'
        )
        db.session.add(log)
        
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário removido com sucesso',
            'usuario_id': usuario_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover usuário: {str(e)}'}), 500

@admin_bp.route('/logs-atividade', methods=['GET'])
@admin_required
def listar_logs_atividade():
    """Lista logs de atividade do sistema"""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Filtros
        profissional_id = request.args.get('profissional_id', type=int)
        acao = request.args.get('acao', type=str)
        
        query = LogAtividade.query
        
        if profissional_id:
            query = query.filter_by(profissional_id=profissional_id)
        if acao:
            query = query.filter_by(acao=acao)
        
        # Ordenar por data mais recente
        logs = query.order_by(desc(LogAtividade.data_hora)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs_list = []
        for log in logs.items:
            log_data = log.to_dict()
            if log.profissional:
                log_data['profissional'] = {
                    'id': log.profissional.id,
                    'nome': log.profissional.nome,
                    'usuario': mask_sensitive_data(log.profissional.usuario, 'email')
                }
            logs_list.append(log_data)
        
        return jsonify({
            'logs': logs_list,
            'pagination': {
                'page': logs.page,
                'per_page': logs.per_page,
                'total': logs.total,
                'pages': logs.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar logs: {str(e)}'}), 500

@admin_bp.route('/sistema/info', methods=['GET'])
@admin_required
def sistema_info():
    """Retorna informações do sistema"""
    try:
        import os
        import platform
        import psutil
        from datetime import datetime
        
        # Informações do sistema
        system_info = {
            'python_version': platform.python_version(),
            'sistema_operacional': f"{platform.system()} {platform.release()}",
            'processador': platform.processor(),
            'arquitetura': platform.architecture()[0],
            'diretorio_atual': os.getcwd(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Uso de recursos
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            system_info['recursos'] = {
                'memoria': {
                    'total': f"{memory.total / (1024**3):.2f} GB",
                    'disponivel': f"{memory.available / (1024**3):.2f} GB",
                    'percentual_uso': memory.percent
                },
                'disco': {
                    'total': f"{disk.total / (1024**3):.2f} GB",
                    'disponivel': f"{disk.free / (1024**3):.2f} GB",
                    'percentual_uso': disk.percent
                },
                'cpu_percentual': cpu_percent
            }
        except:
            system_info['recursos'] = {'error': 'Não foi possível obter informações de recursos'}
        
        # Configurações da aplicação
        app_config = {
            'debug': current_app.config.get('DEBUG', False),
            'cors_origins': current_app.config.get('CORS_ORIGINS', 'Não configurado'),
            'max_upload_size': current_app.config.get('MAX_CONTENT_LENGTH', 0),
            'upload_folder': current_app.config.get('UPLOAD_FOLDER_EXAMES', 'Não configurado')
        }
        
        return jsonify({
            'sistema': system_info,
            'configuracoes': app_config
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter informações do sistema: {str(e)}'}), 500

@admin_bp.route('/sistema/health', methods=['GET'])
@admin_required
def sistema_health():
    """Verifica a saúde do sistema"""
    try:
        # Testar conexão com banco de dados usando uma query simples
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_connected = True
        db_message = 'Conexão com banco de dados ok'
    except Exception as e:
        current_app.logger.error(f"Erro na conexão com banco de dados: {str(e)}")
        db_connected = False
        db_message = f'Erro na conexão com banco de dados: {str(e)}'
    
    # Verificar diretórios de upload
    upload_dir = current_app.config.get('UPLOAD_FOLDER_EXAMES')
    upload_dir_exists = os.path.exists(upload_dir) if upload_dir else False
    
    health_status = {
        'status': 'healthy' if db_connected else 'unhealthy',
        'checks': {
            'database': {
                'status': 'up' if db_connected else 'down',
                'message': db_message
            },
            'upload_directory': {
                'status': 'up' if upload_dir_exists else 'down',
                'message': f'Diretório de upload ok: {upload_dir}' if upload_dir_exists else 'Diretório de upload não encontrado',
                'path': upload_dir
            }
        },
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    
    return jsonify(health_status), 200
