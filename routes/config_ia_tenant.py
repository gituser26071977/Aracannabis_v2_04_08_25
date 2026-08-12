from flask import g, Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ConfiguracaoIA, LogAtividade

config_ia_tenant_bp = Blueprint('config_ia_tenant', __name__)

def _assoc_id():
    """Resolve o associacao_id atual (tenant) via middleware (P0-12)."""
    from flask import g
    assoc = getattr(g, "current_association", None)
    return getattr(assoc, "id", None)



@config_ia_tenant_bp.route('/ia', methods=['GET'])
@jwt_required()
def obter_configuracao_ia():
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    config = ConfiguracaoIA.query.filter_by(profissional_id=profissional_id).first()
    
    if not config:
        # Se não existe, retorna um esqueleto vazio para o frontend preencher
        return jsonify({
            'nome_assistente': 'Assistente Virtual',
            'tom_de_voz': 'Empático e profissional',
            'valor_consulta': '',
            'regras_adicionais': '',
            'instance_name': '',
            'ativo': False
        }), 200
        
    return jsonify(config.to_dict()), 200

@config_ia_tenant_bp.route('/ia', methods=['POST', 'PUT'])
@jwt_required()
def salvar_configuracao_ia():
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    data = request.get_json()
    
    try:
        config = ConfiguracaoIA.query.filter_by(profissional_id=profissional_id).first()
        
        # Validar unicidade do instance_name se for fornecido e diferente do atual
        instance_name = data.get('instance_name')
        if instance_name:
            conflito = ConfiguracaoIA.query.filter(
                ConfiguracaoIA.instance_name == instance_name,
                ConfiguracaoIA.profissional_id != profissional_id
            ).first()
            if conflito:
                return jsonify({'error': 'Esta instância do WhatsApp já está vinculada a outro profissional.'}), 400

        if not config:
            config = ConfiguracaoIA(
                profissional_id=profissional_id,
                nome_assistente=data.get('nome_assistente', 'Assistente Virtual'),
                tom_de_voz=data.get('tom_de_voz', 'Empático e profissional'),
                valor_consulta=data.get('valor_consulta', ''),
                regras_adicionais=data.get('regras_adicionais', ''),
                instance_name=instance_name,
                ativo=data.get('ativo', True)
            )
            db.session.add(config)
            acao = 'Criação'
        else:
            config.nome_assistente = data.get('nome_assistente', config.nome_assistente)
            config.tom_de_voz = data.get('tom_de_voz', config.tom_de_voz)
            config.valor_consulta = data.get('valor_consulta', config.valor_consulta)
            config.regras_adicionais = data.get('regras_adicionais', config.regras_adicionais)
            config.instance_name = instance_name if 'instance_name' in data else config.instance_name
            config.ativo = data.get('ativo', config.ativo)
            acao = 'Atualização'
            
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            acao=f'{acao} Configuração IA SDR',
            detalhes=f'Configurações do assistente atualizadas. Status: {"Ativo" if config.ativo else "Inativo"}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Configurações de IA salvas com sucesso.',
            'config': config.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao salvar configurações de IA: {str(e)}'}), 500
