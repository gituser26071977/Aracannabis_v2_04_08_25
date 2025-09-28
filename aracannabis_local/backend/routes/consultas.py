from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Consulta, Paciente, Profissional, LogAtividade
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

consultas_bp = Blueprint('consultas', __name__)

@consultas_bp.route('/', methods=['GET'])
@jwt_required()
def listar_consultas():
    """Listar todas as consultas com filtros opcionais"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    paciente_id = request.args.get('paciente_id')
    status = request.args.get('status')
    
    query = Consulta.query
    
    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Consulta.data_hora >= data_inicio)
        except ValueError:
            return jsonify({'error': 'Formato de data_inicio inválido. Use YYYY-MM-DD'}), 400
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            # Adicionar 23:59:59 para incluir todo o dia
            data_fim = data_fim.replace(hour=23, minute=59, second=59)
            query = query.filter(Consulta.data_hora <= data_fim)
        except ValueError:
            return jsonify({'error': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    if paciente_id:
        query = query.filter(Consulta.paciente_id == paciente_id)
    
    if status:
        query = query.filter(Consulta.status == status)
    
    # Ordenar por data/hora
    consultas = query.order_by(Consulta.data_hora.asc()).all()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes='Listagem de consultas'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'consultas': [c.to_dict() for c in consultas]
    }), 200

@consultas_bp.route('/', methods=['POST'])
@jwt_required()
def agendar_consulta():
    """Agendar nova consulta"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if not all(k in data for k in ('paciente_id', 'data_hora')):
        return jsonify({'error': 'Paciente e data/hora são obrigatórios'}), 400
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(data['paciente_id'])
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    try:
        # Converter string de data/hora para objeto datetime
        data_hora = datetime.fromisoformat(data['data_hora'].replace('Z', '+00:00'))
        
        # Verificar se já existe consulta no mesmo horário
        consulta_existente = Consulta.query.filter(
            Consulta.data_hora == data_hora,
            Consulta.status.in_(['agendada', 'confirmada'])
        ).first()
        
        if consulta_existente:
            return jsonify({'error': 'Já existe uma consulta agendada para este horário'}), 400
        
        # Criar nova consulta
        nova_consulta = Consulta(
            paciente_id=data['paciente_id'],
            profissional_id=profissional_id,
            data_hora=data_hora,
            duracao_minutos=data.get('duracao_minutos', 60),
            tipo_consulta=data.get('tipo_consulta', 'presencial'),
            observacoes=data.get('observacoes', '')
        )
        
        db.session.add(nova_consulta)
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Agendamento',
            detalhes=f'Nova consulta agendada para {paciente.nome} em {data_hora.strftime("%d/%m/%Y %H:%M")}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Consulta agendada com sucesso',
            'consulta': nova_consulta.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Formato de data/hora inválido: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao agendar consulta: {str(e)}'}), 500

@consultas_bp.route('/<int:consulta_id>', methods=['PUT'])
@jwt_required()
def atualizar_consulta(consulta_id):
    """Atualizar consulta existente"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    consulta = Consulta.query.get(consulta_id)
    if not consulta:
        return jsonify({'error': 'Consulta não encontrada'}), 404
    
    data = request.get_json()
    
    try:
        # Atualizar campos se fornecidos
        if 'data_hora' in data:
            nova_data_hora = datetime.fromisoformat(data['data_hora'].replace('Z', '+00:00'))
            
            # Verificar conflitos apenas se a data/hora mudou
            if nova_data_hora != consulta.data_hora:
                consulta_existente = Consulta.query.filter(
                    Consulta.data_hora == nova_data_hora,
                    Consulta.status.in_(['agendada', 'confirmada']),
                    Consulta.id != consulta_id
                ).first()
                
                if consulta_existente:
                    return jsonify({'error': 'Já existe uma consulta agendada para este horário'}), 400
            
            consulta.data_hora = nova_data_hora
        
        if 'duracao_minutos' in data:
            consulta.duracao_minutos = data['duracao_minutos']
        
        if 'tipo_consulta' in data:
            consulta.tipo_consulta = data['tipo_consulta']
        
        if 'status' in data:
            consulta.status = data['status']
        
        if 'observacoes' in data:
            consulta.observacoes = data['observacoes']
        
        consulta.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Atualização',
            detalhes=f'Consulta ID {consulta_id} atualizada'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Consulta atualizada com sucesso',
            'consulta': consulta.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Formato de data/hora inválido: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar consulta: {str(e)}'}), 500

@consultas_bp.route('/<int:consulta_id>', methods=['DELETE'])
@jwt_required()
def cancelar_consulta(consulta_id):
    """Cancelar consulta"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    consulta = Consulta.query.get(consulta_id)
    if not consulta:
        return jsonify({'error': 'Consulta não encontrada'}), 404
    
    try:
        # Marcar como cancelada em vez de excluir
        consulta.status = 'cancelada'
        consulta.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Cancelamento',
            detalhes=f'Consulta ID {consulta_id} cancelada'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Consulta cancelada com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao cancelar consulta: {str(e)}'}), 500

@consultas_bp.route('/calendario/<int:ano>/<int:mes>', methods=['GET'])
@jwt_required()
def obter_calendario(ano, mes):
    """Obter consultas para visualização em calendário"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    try:
        # Definir início e fim do mês
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1) - timedelta(seconds=1)
        else:
            data_fim = datetime(ano, mes + 1, 1) - timedelta(seconds=1)
        
        # Buscar consultas do mês
        consultas = Consulta.query.filter(
            Consulta.data_hora >= data_inicio,
            Consulta.data_hora <= data_fim
        ).order_by(Consulta.data_hora.asc()).all()
        
        # Formatar para o calendário
        eventos = []
        for consulta in consultas:
            eventos.append({
                'id': consulta.id,
                'title': f"{consulta.paciente.nome if consulta.paciente else 'Paciente'} - {consulta.tipo_consulta}",
                'start': consulta.data_hora.isoformat(),
                'end': (consulta.data_hora + timedelta(minutes=consulta.duracao_minutos)).isoformat(),
                'backgroundColor': get_status_color(consulta.status),
                'borderColor': get_status_color(consulta.status),
                'extendedProps': {
                    'paciente_id': consulta.paciente_id,
                    'paciente_nome': consulta.paciente.nome if consulta.paciente else None,
                    'status': consulta.status,
                    'tipo_consulta': consulta.tipo_consulta,
                    'observacoes': consulta.observacoes
                }
            })
        
        return jsonify({
            'eventos': eventos
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter calendário: {str(e)}'}), 500

@consultas_bp.route('/lembretes/enviar', methods=['POST'])
@jwt_required()
def enviar_lembretes():
    """Enviar lembretes de consultas"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    try:
        # Buscar consultas para as próximas 24 horas que ainda não tiveram lembrete enviado
        agora = datetime.utcnow()
        limite = agora + timedelta(hours=24)
        
        consultas = Consulta.query.filter(
            Consulta.data_hora >= agora,
            Consulta.data_hora <= limite,
            Consulta.status.in_(['agendada', 'confirmada']),
            Consulta.lembrete_email_enviado == False
        ).all()
        
        lembretes_enviados = 0
        
        for consulta in consultas:
            if consulta.paciente and consulta.paciente.email:
                # Enviar lembrete por email
                if enviar_email_lembrete(consulta):
                    consulta.lembrete_email_enviado = True
                    lembretes_enviados += 1
            
            if consulta.paciente and consulta.paciente.telefone:
                # Enviar lembrete por WhatsApp (implementação básica)
                if enviar_whatsapp_lembrete(consulta):
                    consulta.lembrete_whatsapp_enviado = True
        
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Lembretes',
            detalhes=f'{lembretes_enviados} lembretes enviados'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': f'{lembretes_enviados} lembretes enviados com sucesso'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao enviar lembretes: {str(e)}'}), 500

def get_status_color(status):
    """Retorna cor baseada no status da consulta"""
    colors = {
        'agendada': '#2196F3',    # Azul
        'confirmada': '#4CAF50',  # Verde
        'realizada': '#9E9E9E',   # Cinza
        'cancelada': '#F44336'    # Vermelho
    }
    return colors.get(status, '#2196F3')

def enviar_email_lembrete(consulta):
    """Enviar lembrete por email com suporte SSL para Hostinger"""
    try:
        # Configurações do email (devem estar no .env)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.hostinger.com')
        smtp_port = int(os.getenv('SMTP_PORT', '465'))
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if not email_user or not email_password:
            print("Configurações de email não encontradas")
            return False
        
        print(f"Configurações de email encontradas: {smtp_server}:{smtp_port}")
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = consulta.paciente.email
        msg['Subject'] = 'Lembrete de Consulta - Aracannabis'
        
        # Corpo do email
        data_formatada = consulta.data_hora.strftime('%d/%m/%Y às %H:%M')
        corpo = f"""
Olá {consulta.paciente.nome},

Este é um lembrete da sua consulta agendada para {data_formatada}.

Tipo: {consulta.tipo_consulta.title()}
Duração: {consulta.duracao_minutos} minutos

{f"Observações: {consulta.observacoes}" if consulta.observacoes else ""}

Em caso de dúvidas ou necessidade de reagendamento, entre em contato conosco.

Atenciosamente,
Equipe Aracannabis
        """
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        # Enviar email com SSL (porta 465) ou STARTTLS (porta 587)
        if smtp_port == 465:
            # SSL direto (Hostinger)
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            # STARTTLS (Gmail, Outlook)
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, consulta.paciente.email, text)
        server.quit()
        
        print(f"Lembrete enviado para: {consulta.paciente.email}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

def enviar_whatsapp_lembrete(consulta):
    """Enviar lembrete por WhatsApp (implementação básica)"""
    try:
        # Esta é uma implementação básica
        # Para produção, você precisaria integrar com uma API como Twilio, WhatsApp Business API, etc.
        
        whatsapp_api_url = os.getenv('WHATSAPP_API_URL')
        whatsapp_token = os.getenv('WHATSAPP_TOKEN')
        
        if not whatsapp_api_url or not whatsapp_token:
            print("Configurações do WhatsApp não encontradas")
            return False
        
        data_formatada = consulta.data_hora.strftime('%d/%m/%Y às %H:%M')
        mensagem = f"""
🏥 *Lembrete de Consulta - Aracannabis*

Olá {consulta.paciente.nome}!

Você tem uma consulta agendada para *{data_formatada}*.

📋 Tipo: {consulta.tipo_consulta.title()}
⏰ Duração: {consulta.duracao_minutos} minutos

{f"📝 Observações: {consulta.observacoes}" if consulta.observacoes else ""}

Em caso de dúvidas, entre em contato conosco.
        """
        
        # Exemplo de payload para API do WhatsApp
        payload = {
            'phone': consulta.paciente.telefone,
            'message': mensagem
        }
        
        headers = {
            'Authorization': f'Bearer {whatsapp_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(whatsapp_api_url, json=payload, headers=headers)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Erro ao enviar WhatsApp: {e}")
        return False
