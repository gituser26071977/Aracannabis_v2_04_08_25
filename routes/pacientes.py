from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Paciente, LogAtividade
from datetime import datetime

pacientes_bp = Blueprint('pacientes', __name__)

@pacientes_bp.route('/', methods=['GET'])
@jwt_required()
def listar_pacientes():
    try:
        current_user = get_jwt_identity()
        profissional_id = current_user.get('id')
        
        # Parâmetros de filtro
        nome_filtro = request.args.get('nome', '')
        
        query = Paciente.query
        
        # Aplicar filtro por nome se fornecido
        if nome_filtro:
            query = query.filter(Paciente.nome.ilike(f'%{nome_filtro}%'))
        
        # Ordenar por nome
        pacientes = query.order_by(Paciente.nome).all()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Consulta',
            detalhes=f'Listagem de pacientes'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'pacientes': [p.to_dict() for p in pacientes]
        }), 200
    except Exception as e:
        print(f"Erro ao listar pacientes: {str(e)}")
        return jsonify({'error': f'Erro ao listar pacientes: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>', methods=['GET'])
@jwt_required()
def obter_paciente(paciente_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Visualização do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'paciente': paciente.to_dict()
    }), 200

@pacientes_bp.route('/test', methods=['GET'])
def test_route():
    """Rota de teste sem autenticação"""
    return jsonify({
        'message': 'Rota de teste funcionando corretamente'
    }), 200

@pacientes_bp.route('/', methods=['POST'])
def cadastrar_paciente():
    try:
        data = request.get_json()
        print(f"Dados recebidos: {data}")
        
        # Validar dados obrigatórios
        if not all(k in data for k in ('nome', 'data_nascimento')):
            return jsonify({'error': 'Nome e Data de Nascimento são obrigatórios'}), 400
        
        try:
            # Converter string de data para objeto date
            data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
            
            novo_paciente = Paciente(
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
            
            db.session.add(novo_paciente)
            db.session.commit()
            
            # Não registramos atividade pois não temos o profissional_id
            
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
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
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
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
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

@pacientes_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Endpoint para obter estatísticas para o dashboard"""
    
    # Total de pacientes
    total_pacientes = Paciente.query.count()
    
    # Pacientes em tratamento
    em_tratamento = Paciente.query.filter_by(em_tratamento=True).count()
    
    # Taxa de tratamento
    taxa_tratamento = 0
    if total_pacientes > 0:
        taxa_tratamento = (em_tratamento / total_pacientes) * 100
    
    return jsonify({
        'total_pacientes': total_pacientes,
        'em_tratamento': em_tratamento,
        'taxa_tratamento': round(taxa_tratamento, 1)
    }), 200
