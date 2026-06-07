from flask import Blueprint, request, jsonify, send_from_directory, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Paciente, LogAtividade, Profissional, CompartilhamentoPaciente
from security_config import sanitize_input
from datetime import datetime
import os
from werkzeug.utils import secure_filename

pacientes_bp = Blueprint('pacientes', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'uploads/pacientes'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def salvar_foto_paciente(foto_file, paciente_id):
    """Salva a foto do paciente e retorna os metadados"""
    if not foto_file or foto_file.filename == '':
        return None

    if not allowed_file(foto_file.filename):
        raise ValueError('Tipo de arquivo não permitido. Use PNG, JPG, JPEG ou GIF.')

    # Criar nome único para o arquivo
    filename = secure_filename(foto_file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"paciente_{paciente_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{ext}"

    # Caminho completo
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

    # Salvar arquivo
    foto_file.save(filepath)

    # Retornar metadados
    return {
        'nome': unique_filename,
        'caminho': filepath,
        'tipo': foto_file.content_type,
        'tamanho': os.path.getsize(filepath)
    }

def verificar_acesso_paciente(profissional_id, paciente_id, nivel_necessario='leitura'):
    """
    Verifica se o profissional tem acesso ao paciente
    
    Args:
        profissional_id: ID do profissional
        paciente_id: ID do paciente
        nivel_necessario: 'leitura', 'escrita' ou 'completo'
    
    Returns:
        tuple: (tem_acesso, eh_responsavel, nivel_acesso)
    """
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return False, False, None
    
    # Se for admin ou superadmin, acesso completo
    user = Profissional.query.get(profissional_id)
    if user and user.role in ['admin', 'superadmin']:
        return True, False, 'completo'

    
    # Verificar se é o profissional responsável
    if paciente.profissional_responsavel_id == profissional_id:
        return True, True, 'completo'
    
    # Verificar compartilhamentos ativos
    compartilhamento = CompartilhamentoPaciente.query.filter_by(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        ativo=True
    ).first()
    
    if compartilhamento:
        # Verificar se o nível de acesso é suficiente
        niveis = {'leitura': 1, 'escrita': 2, 'completo': 3}
        nivel_atual = niveis.get(compartilhamento.nivel_acesso, 0)
        nivel_req = niveis.get(nivel_necessario, 0)
        
        if nivel_atual >= nivel_req:
            return True, False, compartilhamento.nivel_acesso
    
    return False, False, None

def obter_pacientes_acessiveis(profissional_id):
    """
    Retorna query com pacientes que o profissional pode acessar
    """
    user = Profissional.query.get(profissional_id)
    
    # Se for admin ou superadmin, vê tudo (bypass tenant filter)
    if user and user.role in ['admin', 'superadmin']:
        # Usa skip_tenant para contornar o filtro multi-tenant
        return Paciente.query.execution_options(skip_tenant=True)

    # Pacientes onde é responsável - também bypass tenant filter para ver todos os seus pacientes
    # independente da associação (um profissional pode ter pacientes em várias associações)
    pacientes_responsavel = Paciente.query.execution_options(skip_tenant=True).filter_by(profissional_responsavel_id=profissional_id)
    
    # Pacientes compartilhados ativos
    compartilhamentos_ativos = CompartilhamentoPaciente.query.filter_by(
        profissional_id=profissional_id,
        ativo=True
    ).all()
    
    pacientes_compartilhados_ids = [c.paciente_id for c in compartilhamentos_ativos]
    
    if pacientes_compartilhados_ids:
        agora = datetime.utcnow()
        # Apenas retorna o paciente compartilhado se o dono (responsável) possuir assinatura ativa
        # Usa skip_tenant para contornar o filtro multi-tenant
        pacientes_compartilhados = Paciente.query.execution_options(skip_tenant=True).join(
            Profissional, Paciente.profissional_responsavel_id == Profissional.id
        ).filter(
            Paciente.id.in_(pacientes_compartilhados_ids),
            db.or_(
                Profissional.data_expiracao.is_(None),
                Profissional.data_expiracao >= agora
            )
        )
        # Unir as duas queries
        return pacientes_responsavel.union(pacientes_compartilhados)
    else:
        return pacientes_responsavel

@pacientes_bp.route('/', methods=['GET'])
@jwt_required()
def listar_pacientes():
    try:
        current_user_id = get_jwt_identity()
        profissional_id = int(current_user_id)
        
        # Parâmetros de filtro
        nome_filtro = request.args.get('nome', '')
        associacao_filtro = request.args.get('associacao', '')
        periodo_filtro = request.args.get('periodo_cadastro', '')
        
        # Parâmetros de paginação (opcional, backward-compatible)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 0, type=int)  # 0 = sem paginação (legado)
        
        # Obter apenas pacientes acessíveis ao profissional
        query = obter_pacientes_acessiveis(profissional_id)
        
        # Aplicar filtro por nome
        if nome_filtro:
            query = query.filter(Paciente.nome.ilike(f'%{nome_filtro}%'))

        # Aplicar filtro por associação
        if associacao_filtro:
            query = query.filter(Paciente.associacao.ilike(f'%{associacao_filtro}%'))

        # Aplicar filtro por período de cadastro
        if periodo_filtro:
            hoje = datetime.utcnow().date()
            if periodo_filtro == 'hoje':
                query = query.filter(db.func.date(Paciente.created_at) == hoje)
            elif periodo_filtro == 'ontem':
                ontem = hoje - datetime.timedelta(days=1)
                query = query.filter(db.func.date(Paciente.created_at) == ontem)
            elif periodo_filtro == '7dias':
                data_inicio = hoje - datetime.timedelta(days=7)
                query = query.filter(db.func.date(Paciente.created_at) >= data_inicio)
            elif periodo_filtro == '30dias':
                data_inicio = hoje - datetime.timedelta(days=30)
                query = query.filter(db.func.date(Paciente.created_at) >= data_inicio)
            elif periodo_filtro == 'mes_atual':
                query = query.filter(db.extract('month', Paciente.created_at) == hoje.month)
                query = query.filter(db.extract('year', Paciente.created_at) == hoje.year)
        
        # Ordenar por data de cadastro desc (mais recentes primeiro) se houver filtro de tempo, ou nome
        if periodo_filtro:
             query = query.order_by(Paciente.created_at.desc())
        else:
             query = query.order_by(Paciente.nome)
        
        # Paginação
        total = query.count()
        if per_page > 0:
            paginated = query.offset((page - 1) * per_page).limit(per_page).all()
            pacientes = paginated
            has_more = total > page * per_page
        else:
            # Modo legado: retorna todos
            pacientes = query.all()
            has_more = False
        
        # Adicionar informações de acesso para cada paciente
        pacientes_com_acesso = []
        for paciente in pacientes:
            paciente_dict = paciente.to_dict()
            
            # Verificar tipo de acesso
            tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
                profissional_id, paciente.id
            )
            
            # Adicionar campo associacao no retorno (to_dict pode nao ter)
            paciente_dict['associacao'] = paciente.associacao.nome if paciente.associacao else None
            paciente_dict['eh_responsavel'] = eh_responsavel
            paciente_dict['nivel_acesso'] = nivel_acesso
            pacientes_com_acesso.append(paciente_dict)
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Consulta',
            detalhes=f'Listagem de pacientes - {len(pacientes)} encontrados (total: {total})'
        )
        db.session.add(log)
        db.session.commit()
        
        response = {
            'pacientes': pacientes_com_acesso,
            'total': total,
        }
        
        # Incluir metadados de paginação apenas quando paginado
        if per_page > 0:
            response['pagination'] = {
                'page': page,
                'per_page': per_page,
                'has_more': has_more,
            }
        
        return jsonify(response), 200
    except Exception as e:
        print(f"Erro ao listar pacientes: {str(e)}")
        return jsonify({'error': f'Erro ao listar pacientes: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>', methods=['GET'])
@jwt_required()
def obter_paciente(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar acesso
    tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
        profissional_id, paciente_id
    )
    
    if not tem_acesso:
        return jsonify({'error': 'Acesso negado a este paciente'}), 403
    
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Adicionar informações de acesso
    paciente_dict = paciente.to_dict()
    paciente_dict['eh_responsavel'] = eh_responsavel
    paciente_dict['nivel_acesso'] = nivel_acesso
    
    # Se for responsável, incluir informações de compartilhamento
    if eh_responsavel:
        compartilhamentos = CompartilhamentoPaciente.query.filter_by(
            paciente_id=paciente_id,
            ativo=True
        ).all()
        paciente_dict['compartilhamentos'] = [c.to_dict() for c in compartilhamentos]
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Visualização do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'paciente': paciente_dict
    }), 200

@pacientes_bp.route('/', methods=['POST'])
@jwt_required()
def cadastrar_paciente():
    try:
        current_user_id = get_jwt_identity()
        profissional_id = int(current_user_id)
        
        # Verificar assinatura ativa para criar pacientes (exceto admin e superadmin)
        user = Profissional.query.get(profissional_id)
        if user and user.role not in ['admin', 'superadmin']:
            if user.data_expiracao and user.data_expiracao < datetime.utcnow():
                return jsonify({'error': 'Assinatura inativa ou perfil avulso sem permissão. Para cadastrar novos pacientes como titular, é necessário ter um plano ativo.'}), 403

        # Verificar se é multipart/form-data (com foto) ou JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Dados do formulário
            data = {}
            for key in request.form:
                data[key] = request.form[key]

            # Arquivo de foto
            foto_file = request.files.get('foto')
        else:
            # Dados JSON tradicionais
            data = request.get_json()
            foto_file = None

        data = sanitize_input(data)
        print(f"Dados recebidos: {data}")

        # Validar dados obrigatórios
        if not all(k in data for k in ('nome', 'data_nascimento')):
            return jsonify({'error': 'Nome e Data de Nascimento são obrigatórios'}), 400

        try:
            # Converter string de data para objeto date
            data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()

            novo_paciente = Paciente(
                profissional_responsavel_id=profissional_id,  # Definir responsável
                nome=data['nome'],
                data_nascimento=data_nascimento,
                cpf=data.get('cpf'),
                genero=data.get('genero'),
                telefone=data.get('telefone'),
                email=data.get('email'),
                endereco=data.get('endereco'),
                diagnostico=data.get('diagnostico'),
                observacoes=data.get('observacoes'),
                em_tratamento=data.get('em_tratamento', False),
                composicao=data.get('composicao'),
                dosagem=data.get('dosagem'),
                horarios=data.get('horarios')
            )

            # Tratar campo associação
            assoc_data = data.get('associacao')
            
            # Se o usuário tem uma associação ativa no contexto, usa ela por padrão
            if hasattr(g, 'current_association') and g.current_association:
                # Usa a associação do contexto (do tenant middleware)
                if hasattr(g.current_association, 'id'):
                    novo_paciente.associacao_id = g.current_association.id
                    print(f"Paciente vinculado automaticamente à associação: {g.current_association.id}")
            
            # Se foi passado associação específica nos dados, sobrescreve
            if assoc_data:
                try:
                    # Tenta converter para ID (inteiro)
                    novo_paciente.associacao_id = int(assoc_data)
                except (ValueError, TypeError):
                    # Se não for número, tenta buscar pelo nome
                    from association.models import Associacao
                    assoc = Associacao.query.filter_by(nome=assoc_data).first()
                    if assoc:
                        novo_paciente.associacao_id = assoc.id
                    else:
                        # Opcional: Criar associação automática ou apenas deixar null
                        # Por segurança, apenas deixamos nulo ou ignoramos se não for ID válido
                        pass

            db.session.add(novo_paciente)
            db.session.flush()  # Para obter o ID do paciente

            # Processar foto se fornecida
            if foto_file:
                try:
                    foto_metadata = salvar_foto_paciente(foto_file, novo_paciente.id)
                    if foto_metadata:
                        novo_paciente.foto_nome = foto_metadata['nome']
                        novo_paciente.foto_caminho = foto_metadata['caminho']
                        novo_paciente.foto_tipo = foto_metadata['tipo']
                        novo_paciente.foto_tamanho = foto_metadata['tamanho']
                except ValueError as e:
                    db.session.rollback()
                    return jsonify({'error': str(e)}), 400

            db.session.commit()

            # Registrar atividade
            log = LogAtividade(
                profissional_id=profissional_id,
                acao='Cadastro',
                detalhes=f'Novo paciente cadastrado: {novo_paciente.nome} (ID {novo_paciente.id})'
            )
            db.session.add(log)
            db.session.commit()
            
            # --- BILATERAL API SYNC START ---
            # Enviar dados do paciente recém-criado para o sistema de Associação
            try:
                from association.services.external_integration_service import ExternalAssociationService
                # Prepara dados para sync
                sync_data = {
                    'nome': novo_paciente.nome,
                    'cpf': novo_paciente.cpf,
                    'email': novo_paciente.email,
                    'telefone': novo_paciente.telefone,
                    'endereco': novo_paciente.endereco,
                    'data_nascimento': novo_paciente.data_nascimento
                }
                # Executa sync em background ou direto (aqui direto para simplicidade, ideal seria background task)
                ExternalAssociationService.sync_patient_to_association(sync_data)
                print(f"Sync attempt for patient {novo_paciente.id} to external association initiated.")
            except Exception as e_sync:
                print(f"Error syncing new patient to external association: {e_sync}")
            # --- BILATERAL API SYNC END ---

            print(f"Paciente cadastrado com sucesso: {novo_paciente.to_dict()}")

            return jsonify({
                'message': 'Paciente cadastrado com sucesso',
                'paciente': novo_paciente.to_dict()
            }), 201

        except ValueError as e:
            print(f"Erro de formato de data: {str(e)}")
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao cadastrar paciente: {str(e)}")
            return jsonify({'error': f'Erro ao cadastrar paciente: {str(e)}'}), 500
    except Exception as e:
        print(f"Erro ao processar requisição: {str(e)}")
        return jsonify({'error': f'Erro ao processar requisição: {str(e)}'}), 400

@pacientes_bp.route('/<int:paciente_id>', methods=['PUT'])
@jwt_required()
def atualizar_paciente(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    # Verificar acesso de escrita
    tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
        profissional_id, paciente_id, 'escrita'
    )

    if not tem_acesso:
        return jsonify({'error': 'Acesso negado para editar este paciente'}), 403

    paciente = Paciente.query.get(paciente_id)

    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    # Verificar se é multipart/form-data (com foto) ou JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Dados do formulário
        data = {}
        for key in request.form:
            data[key] = request.form[key]

        # Arquivo de foto
        foto_file = request.files.get('foto')
    else:
        # Dados JSON tradicionais
        data = request.get_json()
        foto_file = None

    data = sanitize_input(data)

    try:
        # Atualizar campos se fornecidos
        if 'nome' in data:
            paciente.nome = data['nome']

        if 'data_nascimento' in data:
            paciente.data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()

        if 'cpf' in data:
            paciente.cpf = data['cpf']

        if 'genero' in data:
            paciente.genero = data['genero']

        if 'telefone' in data:
            paciente.telefone = data['telefone']

        if 'email' in data:
            paciente.email = data['email']

        if 'endereco' in data:
            paciente.endereco = data['endereco']

        if 'diagnostico' in data:
            paciente.diagnostico = data['diagnostico']

        if 'observacoes' in data:
            paciente.observacoes = data['observacoes']

        if 'em_tratamento' in data:
            paciente.em_tratamento = data['em_tratamento']

        if 'composicao' in data:
            paciente.composicao = data['composicao']

        if 'dosagem' in data:
            paciente.dosagem = data['dosagem']

        if 'horarios' in data:
            paciente.horarios = data['horarios']
            
        if 'associacao' in data:
            assoc_data = data['associacao']
            if not assoc_data:
                paciente.associacao_id = None
            else:
                try:
                    paciente.associacao_id = int(assoc_data)
                except (ValueError, TypeError):
                    # Se for string (nome), buscar a associação
                    from association.models import Associacao
                    assoc = Associacao.query.filter_by(nome=assoc_data).first()
                    if assoc:
                        paciente.associacao_id = assoc.id
                    else:
                        # Se não encontrar por nome, talvez seja melhor manter o ID atual 
                        # ou definir como None? Para evitar erros, se enviou algo 
                        # que não existe, apenas não alteramos ou deixamos null se for ""
                        pass

        # Processar foto se fornecida
        if foto_file:
            try:
                foto_metadata = salvar_foto_paciente(foto_file, paciente.id)
                if foto_metadata:
                    paciente.foto_nome = foto_metadata['nome']
                    paciente.foto_caminho = foto_metadata['caminho']
                    paciente.foto_tipo = foto_metadata['tipo']
                    paciente.foto_tamanho = foto_metadata['tamanho']
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

        # Atualizar timestamp
        paciente.updated_at = datetime.utcnow()

        db.session.commit()

        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Atualização',
            detalhes=f'Paciente atualizado: ID {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        # --- BILATERAL API SYNC START (UPDATE) ---
        try:
            from association.services.external_integration_service import ExternalAssociationService
            sync_data = {
                'nome': paciente.nome,
                'cpf': paciente.cpf,
                'email': paciente.email,
                'telefone': paciente.telefone,
                'endereco': paciente.endereco,
                'data_nascimento': paciente.data_nascimento
            }
            ExternalAssociationService.sync_patient_to_association(sync_data)
            print(f"Sync attempt for updated patient {paciente.id} to external association initiated.")
        except Exception as e_sync:
            print(f"Error syncing updated patient to external association: {e_sync}")
        # --- BILATERAL API SYNC END ---

        return jsonify({
            'message': 'Paciente atualizado com sucesso',
            'paciente': paciente.to_dict()
        }), 200

    except ValueError:
        return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar paciente: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>', methods=['DELETE'])
@jwt_required()
def excluir_paciente(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar acesso completo (apenas responsável pode excluir)
    tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
        profissional_id, paciente_id, 'completo'
    )
    
    if not tem_acesso or not eh_responsavel:
        return jsonify({'error': 'Apenas o profissional responsável pode excluir pacientes'}), 403
    
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    try:
        nome_paciente = paciente.nome
        
        db.session.delete(paciente)
        
        # Registrar atividade antes de confirmar a exclusão
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Exclusão',
            detalhes=f'Paciente excluído: {nome_paciente} (ID {paciente_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Paciente excluído com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir paciente: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>/compartilhar', methods=['POST'])
@jwt_required()
def compartilhar_paciente(paciente_id):
    """Compartilhar paciente com outro profissional"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se é o responsável pelo paciente
    tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
        profissional_id, paciente_id, 'completo'
    )
    
    if not tem_acesso or not eh_responsavel:
        return jsonify({'error': 'Apenas o profissional responsável pode compartilhar pacientes'}), 403
    
    data = request.get_json()
    data = sanitize_input(data)

    if not data.get('profissional_id') or not data.get('nivel_acesso'):
        return jsonify({'error': 'profissional_id e nivel_acesso são obrigatórios'}), 400
    
    profissional_destino_id = data['profissional_id']
    nivel_acesso_novo = data['nivel_acesso']
    
    # Validar nível de acesso
    if nivel_acesso_novo not in ['leitura', 'escrita', 'completo']:
        return jsonify({'error': 'Nível de acesso inválido'}), 400
    
    # Verificar se o profissional destino existe
    profissional_destino = Profissional.query.get(profissional_destino_id)
    if not profissional_destino:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    # Não permitir compartilhar consigo mesmo
    if profissional_destino_id == profissional_id:
        return jsonify({'error': 'Não é possível compartilhar consigo mesmo'}), 400
    
    try:
        # Verificar se já existe compartilhamento
        compartilhamento_existente = CompartilhamentoPaciente.query.filter_by(
            paciente_id=paciente_id,
            profissional_id=profissional_destino_id
        ).first()
        
        if compartilhamento_existente:
            # Atualizar compartilhamento existente
            compartilhamento_existente.nivel_acesso = nivel_acesso_novo
            compartilhamento_existente.ativo = True
            compartilhamento_existente.data_compartilhamento = datetime.utcnow()
            compartilhamento_existente.compartilhado_por = profissional_id
        else:
            # Criar novo compartilhamento
            novo_compartilhamento = CompartilhamentoPaciente(
                paciente_id=paciente_id,
                profissional_id=profissional_destino_id,
                nivel_acesso=nivel_acesso_novo,
                compartilhado_por=profissional_id
            )
            db.session.add(novo_compartilhamento)
        
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Compartilhamento',
            detalhes=f'Paciente ID {paciente_id} compartilhado com {profissional_destino.nome} (nível: {nivel_acesso_novo})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': f'Paciente compartilhado com sucesso com {profissional_destino.nome}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao compartilhar paciente: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>/compartilhamentos', methods=['GET'])
@jwt_required()
def listar_compartilhamentos(paciente_id):
    """Listar compartilhamentos de um paciente"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se é o responsável pelo paciente
    tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
        profissional_id, paciente_id
    )
    
    if not tem_acesso or not eh_responsavel:
        return jsonify({'error': 'Apenas o profissional responsável pode ver compartilhamentos'}), 403
    
    compartilhamentos = CompartilhamentoPaciente.query.filter_by(
        paciente_id=paciente_id,
        ativo=True
    ).all()
    
    return jsonify({
        'compartilhamentos': [c.to_dict() for c in compartilhamentos]
    }), 200

@pacientes_bp.route('/<int:paciente_id>/compartilhamentos/<int:compartilhamento_id>', methods=['DELETE'])
@jwt_required()
def remover_compartilhamento(paciente_id, compartilhamento_id):
    """Remover compartilhamento de paciente"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se é o responsável pelo paciente
    tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
        profissional_id, paciente_id, 'completo'
    )
    
    if not tem_acesso or not eh_responsavel:
        return jsonify({'error': 'Apenas o profissional responsável pode remover compartilhamentos'}), 403
    
    compartilhamento = CompartilhamentoPaciente.query.get(compartilhamento_id)
    
    if not compartilhamento or compartilhamento.paciente_id != paciente_id:
        return jsonify({'error': 'Compartilhamento não encontrado'}), 404
    
    try:
        # Desativar compartilhamento
        compartilhamento.ativo = False
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Remoção de Compartilhamento',
            detalhes=f'Compartilhamento removido: Paciente ID {paciente_id} com {compartilhamento.profissional.nome}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Compartilhamento removido com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover compartilhamento: {str(e)}'}), 500

@pacientes_bp.route('/profissionais', methods=['GET'])
@jwt_required()
def listar_profissionais():
    """Listar profissionais para compartilhamento"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    # Listar todos os profissionais exceto o atual
    profissionais = Profissional.query.filter(Profissional.id != profissional_id).all()

    return jsonify({
        'profissionais': [p.to_dict() for p in profissionais]
    }), 200

@pacientes_bp.route('/foto/<filename>')
@jwt_required()
def obter_foto_paciente(filename):
    """Servir foto do paciente com verificação de acesso"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    # Extrair ID do paciente do nome do arquivo (formato: paciente_{id}_{timestamp}.{ext})
    try:
        paciente_id_str = filename.split('_')[1]
        paciente_id = int(paciente_id_str)
    except (IndexError, ValueError):
        return jsonify({'error': 'Arquivo inválido'}), 400

    # Verificar acesso ao paciente
    tem_acesso, eh_responsavel, nivel_acesso = verificar_acesso_paciente(
        profissional_id, paciente_id
    )

    if not tem_acesso:
        return jsonify({'error': 'Acesso negado à foto do paciente'}), 403

    # Verificar se o arquivo existe
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Arquivo não encontrado'}), 404

    return send_from_directory(UPLOAD_FOLDER, filename)

@pacientes_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Endpoint para obter estatísticas para o dashboard"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Obter apenas pacientes acessíveis ao profissional
    pacientes_acessiveis = obter_pacientes_acessiveis(profissional_id).all()
    
    # Total de pacientes acessíveis
    total_pacientes = len(pacientes_acessiveis)
    
    # Pacientes em tratamento
    em_tratamento = len([p for p in pacientes_acessiveis if p.em_tratamento])
    
    # Pacientes onde é responsável
    responsavel_por = len([p for p in pacientes_acessiveis if p.profissional_responsavel_id == profissional_id])
    
    # Pacientes compartilhados comigo
    compartilhados_comigo = total_pacientes - responsavel_por
    
    # Taxa de tratamento
    taxa_tratamento = 0
    if total_pacientes > 0:
        taxa_tratamento = (em_tratamento / total_pacientes) * 100
    
    return jsonify({
        'total_pacientes': total_pacientes,
        'em_tratamento': em_tratamento,
        'responsavel_por': responsavel_por,
        'compartilhados_comigo': compartilhados_comigo,
        'taxa_tratamento': round(taxa_tratamento, 1)
    }), 200
