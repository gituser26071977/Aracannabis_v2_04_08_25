"""
Rotas administrativas do sistema AraOS.
Acesso restrito a usuários com role 'admin'.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import desc
import datetime
import os

from models import db, Profissional, LogAtividade, Paciente, Exame, Consulta, Evolucao, Assinatura, SolicitacoesCadastro
from models_extra import UsuarioAssociacao
from security_config import mask_sensitive_data

admin_bp = Blueprint('admin', __name__)

# Middleware para verificar permissões de admin
def admin_required(f):
    """Decorator para verificar se o usuário é administrador"""
    from functools import wraps

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        """Verifica permissão de admin usando context multi-tenant e fallback.
        Prioridades:
        1. g.user_role (definido pelo TenantMiddleware baseado na associação atual)
        2. claims do token (fallback)
        3. Role global no banco
        """
        from flask import g
        
        # 1. Verificar role na associação atual (Setado pelo middleware)
        effective_role = getattr(g, 'user_role', None)

        if not effective_role:
            # 2. Fallback para token claims
            try:
                claims = get_jwt()
                effective_role = claims.get('role')
            except Exception:
                pass

        if not effective_role:
            # 3. Fallback para banco (Global)
            current_user_id = get_jwt_identity()
            try:
                if current_user_id is not None:
                    profissional = Profissional.query.get(int(current_user_id))
                    if profissional:
                        effective_role = profissional.role
            except Exception:
                pass

        if effective_role not in ['admin', 'superadmin']:
            return jsonify({'error': 'Acesso negado. Permissão de administrador ou superadministrador necessária.'}), 403

        return f(*args, **kwargs)

    return decorated_function

@admin_bp.route('/dashboard-stats', methods=['GET'])
@admin_required
def dashboard_stats():
    """Retorna estatísticas do sistema para o dashboard administrativo"""
    try:
        from flask import g
        
        # Filtro base: se estiver em associação, restringir dados
        assoc_id = g.current_association.id if hasattr(g, 'current_association') and g.current_association else None

        if assoc_id:
            # CASO 1: Estatísticas da Associação (Multi-tenant)
            total_pacientes = Paciente.query.filter_by(associacao_id=assoc_id).count()
            pacientes_em_tratamento = Paciente.query.filter_by(associacao_id=assoc_id, em_tratamento=True).count()
            
            # Profissionais vinculados
            vinc_links = UsuarioAssociacao.query.filter_by(associacao_id=assoc_id).all()
            total_profissionais = len(vinc_links)
            admin_count = len([l for l in vinc_links if l.role == 'admin'])
            profissional_count = len([l for l in vinc_links if l.role == 'profissional'])
            
            # Dados clínicos filtrados pela associação
            total_exames = Exame.query.filter_by(associacao_id=assoc_id).count()
            total_consultas = Consulta.query.filter_by(associacao_id=assoc_id).count()
            total_evolucoes = Evolucao.query.filter_by(associacao_id=assoc_id).count()
            
            s_d_a = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            novos_pacientes_7dias = Paciente.query.filter(Paciente.associacao_id == assoc_id, Paciente.created_at >= s_d_a).count()
            novas_consultas_7dias = Consulta.query.filter(Consulta.associacao_id == assoc_id, Consulta.created_at >= s_d_a).count()
            
            # Usuários ativos nos últimos 15 min (desta associação)
            s_15m = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
            logged_in_users = db.session.query(db.func.count(db.func.distinct(LogAtividade.profissional_id))).filter(
                LogAtividade.associacao_id == assoc_id,
                LogAtividade.data_hora >= s_15m
            ).scalar() or 0
        else:
            # CASO 2: Estatísticas Globais (Superadmin)
            total_profissionais = Profissional.query.count()
            admin_count = Profissional.query.filter_by(role='admin').count()
            profissional_count = Profissional.query.filter_by(role='profissional').count()
            
            total_pacientes = Paciente.query.count()
            pacientes_em_tratamento = Paciente.query.filter_by(em_tratamento=True).count()
            
            total_exames = Exame.query.count()
            total_consultas = Consulta.query.count()
            total_evolucoes = Evolucao.query.count()
            
            s_d_a = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            novos_pacientes_7dias = Paciente.query.filter(Paciente.created_at >= s_d_a).count()
            novas_consultas_7dias = Consulta.query.filter(Consulta.created_at >= s_d_a).count()
            
            # Usuários ativos nos últimos 15 min (global)
            s_15m = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
            logged_in_users = db.session.query(db.func.count(db.func.distinct(LogAtividade.profissional_id))).filter(
                LogAtividade.data_hora >= s_15m
            ).scalar() or 0
        
        return jsonify({
            'stats': {
                'usuarios': {
                    'total': total_profissionais,
                    'admins': admin_count,
                    'profissionais': profissional_count,
                    'logados': logged_in_users
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
            'logged_in_users': logged_in_users, # Fallback top-level para legado
            'context': 'association' if assoc_id else 'global',
            'updated_at': datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter estatísticas: {str(e)}'}), 500

@admin_bp.route('/usuarios', methods=['GET'])
@admin_required
def listar_usuarios():
    """
    Lista os usuários do sistema.
    Se g.current_association estiver presente, lista apenas usuários vinculados à associação.
    Caso contrário (Global Admin), lista todos os profissionais.
    """
    try:
        from flask import g
        
        # CASO 1: Contexto de Associação
        if hasattr(g, 'current_association') and g.current_association:
            assoc_id = g.current_association.id
            links = UsuarioAssociacao.query.filter_by(associacao_id=assoc_id).all()
            usuarios_ids = [l.profissional_id for l in links]
            usuarios = Profissional.query.filter(Profissional.id.in_(usuarios_ids)).order_by(Profissional.created_at.desc()).all()
        else:
            # CASO 2: Global Admin
            usuarios = Profissional.query.order_by(Profissional.created_at.desc()).all()
        
        usuarios_list = []
        for user in usuarios:
            user_data = user.to_dict()
            # Se estamos em uma associação, adicionar o papel específico
            if hasattr(g, 'current_association') and g.current_association:
                link = next((l for l in links if l.profissional_id == user.id), None)
                if link:
                    user_data['role_naver_associacao'] = link.role
                    user_data['status_na_associacao'] = link.status

            # Mascarar informações sensíveis
            user_data['usuario_mascarado'] = mask_sensitive_data(user.usuario, 'email')
            user_data['crm_mascarado'] = mask_sensitive_data(user.crm, 'cpf')
            
            # Contagem de atividades do usuário (Filtrar por associação se possível)
            if hasattr(g, 'current_association') and g.current_association:
                assoc_id = g.current_association.id
                user_data['total_pacientes'] = Paciente.query.filter_by(profissional_responsavel_id=user.id, associacao_id=assoc_id).count()
                user_data['total_consultas'] = Consulta.query.filter_by(profissional_id=user.id).count() # Fallback se ainda não migrado
            else:
                user_data['total_pacientes'] = Paciente.query.filter_by(profissional_responsavel_id=user.id).count()
                user_data['total_consultas'] = Consulta.query.filter_by(profissional_id=user.id).count()
            
            user_data['total_exames'] = Exame.query.filter_by(profissional_id=user.id).count()
            
            # Buscar assinatura (Sempre via Profissional, pois é quem paga)
            assinatura = Assinatura.query.filter_by(profissional_id=user.id).order_by(Assinatura.created_at.desc()).first()
            if assinatura and assinatura.plano:
                user_data['plano'] = assinatura.plano.nome
                user_data['status_assinatura'] = assinatura.status
            else:
                user_data['plano'] = 'Trial/Gratuito'
                user_data['status_assinatura'] = 'trial'

            # Buscar último acesso
            ultimo_log = LogAtividade.query.filter_by(profissional_id=user.id).order_by(LogAtividade.data_hora.desc()).first()
            user_data['ultimo_acesso'] = ultimo_log.data_hora.isoformat() if ultimo_log else None
            
            if user.created_at:
                dias = (datetime.datetime.utcnow() - user.created_at).days
                user_data['dias_cadastro'] = dias
            else:
                user_data['dias_cadastro'] = 0
            
            usuarios_list.append(user_data)
        
        return jsonify({
            'usuarios': usuarios_list,
            'total': len(usuarios_list),
            'context_association': g.current_association.nome if hasattr(g, 'current_association') and g.current_association else "Global"
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar usuários: {str(e)}'}), 500

@admin_bp.route('/usuarios', methods=['POST'])
@admin_required
def criar_usuario():
    """Cria um novo usuário no sistema"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['nome', 'email', 'crm', 'uf_crm', 'senha']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se usuário/email já existe
        if Profissional.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email já cadastrado'}), 400
            
        # Verificar se CRM já existe
        if Profissional.query.filter_by(crm=data['crm'], uf_crm=data['uf_crm']).first():
            return jsonify({'error': 'CRM já cadastrado para este UF'}), 400
            
        from werkzeug.security import generate_password_hash
        
        novo_usuario = Profissional(
            nome=data['nome'],
            email=data['email'],
            usuario=data['email'], # Usa email como usuário
            senha=generate_password_hash(data['senha']),
            crm=data['crm'],
            uf_crm=data['uf_crm'],
            role=data.get('role', 'profissional'),
            status_cadastro='aprovado', # Admin cria já aprovado
            aprovado_por=str(get_jwt_identity()),
            data_aprovacao=datetime.datetime.utcnow()
        )
        
        db.session.add(novo_usuario)
        db.session.flush() # Para obter ID do novo usuário

        from flask import g
        current_user_id = int(get_jwt_identity())
        
        # Se estiver em contexto de associação, criar o vínculo automaticamente
        if hasattr(g, 'current_association') and g.current_association:
            assoc_id = g.current_association.id
            link = UsuarioAssociacao(
                profissional_id=novo_usuario.id,
                associacao_id=assoc_id,
                role=data.get('role', 'profissional'),
                status='active'
            )
            db.session.add(link)
            
        # Log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            associacao_id=g.current_association.id if hasattr(g, 'current_association') and g.current_association else None,
            acao='CRIAR_USUARIO',
            detalhes=f'Usuário {novo_usuario.email} criado por admin'
        )
        db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'usuario': novo_usuario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar usuário: {str(e)}'}), 500

@admin_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
@admin_required
def obter_usuario(usuario_id):
    """Obtém detalhes de um usuário específico"""
    try:
        usuario = Profissional.query.get(usuario_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        user_data = usuario.to_dict()
        
        from flask import g
        assoc_id = g.current_association.id if hasattr(g, 'current_association') and g.current_association else None

        # Adicionar informações adicionais filtradas por associação se necessário
        if assoc_id:
            user_data['pacientes_responsavel'] = [
                {'id': p.id, 'nome': p.nome} 
                for p in usuario.pacientes_responsavel if p.associacao_id == assoc_id
            ][:10]
            
            logs_recentes = LogAtividade.query.filter_by(
                profissional_id=usuario_id,
                associacao_id=assoc_id
            ).order_by(desc(LogAtividade.data_hora)).limit(10).all()
        else:
            user_data['pacientes_responsavel'] = [
                {'id': p.id, 'nome': p.nome} 
                for p in usuario.pacientes_responsavel[:10]
            ]
            
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
    """
    Remove um usuário. 
    Se houver g.current_association, remove apenas o vínculo com esta associação.
    Se não houver (superadmin global), remove o usuário permanentemente do sistema.
    """
    try:
        from flask import g
        current_user_id = int(get_jwt_identity())
        
        # Não permitir deletar a si mesmo
        if usuario_id == current_user_id:
            return jsonify({'error': 'Não é permitido remover o próprio acesso'}), 400
        
        usuario = Profissional.query.get(usuario_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        # CASO 1: Contexto de Associação (Multi-tenant)
        if hasattr(g, 'current_association') and g.current_association:
            assoc_id = g.current_association.id
            
            # Buscar vínculo
            vinc_extra = UsuarioAssociacao.query.filter_by(
                profissional_id=usuario_id, 
                associacao_id=assoc_id
            ).first()
            
            if not vinc_extra:
                return jsonify({'error': 'Usuário não pertence a esta associação'}), 404
            
            # Verificar se o usuário tem pacientes nesta associação
            pacientes_na_assoc = Paciente.query.filter_by(
                profissional_responsavel_id=usuario_id,
                associacao_id=assoc_id
            ).first()
            
            if pacientes_na_assoc:
                return jsonify({
                    'error': 'Não é possível remover vínculo: usuário tem pacientes sob sua responsabilidade nesta associação',
                }), 400

            # Registrar log
            log = LogAtividade(
                profissional_id=current_user_id,
                associacao_id=assoc_id,
                acao='REMOVER_USUARIO_ASSOC',
                detalhes=f'Vínculo do usuário {usuario.usuario} removido da associação {g.current_association.nome}'
            )
            db.session.add(log)
            db.session.delete(vinc_extra)
            db.session.commit()
            
            return jsonify({'message': 'Usuário desvinculado da associação com sucesso'}), 200

        # CASO 2: Superadmin Global (Sem contexto de associação)
        # Verificar se o usuário tem pacientes associados em QUALQUER associação
        if usuario.pacientes_responsavel:
            return jsonify({
                'error': 'Não é possível remover usuário permanentemente: existem pacientes vinculados em alguma associação',
                'total_pacientes': len(usuario.pacientes_responsavel)
            }), 400
        
        # Registrar log antes de deletar globalmente
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='REMOVER_USUARIO_GLOBAL',
            detalhes=f'Usuário {usuario.usuario} (ID: {usuario_id}) removido permanentemente do sistema'
        )
        db.session.add(log)
        
        # Também remover da tabela de solicitações para permitir novo cadastro se necessário
        SolicitacoesCadastro.query.filter_by(email=usuario.email).delete()
        SolicitacoesCadastro.query.filter_by(crm=usuario.crm, uf_crm=usuario.uf_crm).delete()
        
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário removido globalmente com sucesso',
            'usuario_id': usuario_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover usuário: {str(e)}")
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
