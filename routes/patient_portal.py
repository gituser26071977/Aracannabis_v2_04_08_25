"""
Rotas do Portal do Paciente

APIs para pacientes autenticados visualizarem seus próprios dados
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Paciente, Consulta, Prescricao, Exame, Evolucao
from datetime import datetime
from sqlalchemy import desc, text

patient_portal_bp = Blueprint('patient_portal', __name__)

def require_patient():
    """Helper para verificar se é um paciente autenticado"""
    claims = get_jwt()
    if claims.get('user_type') != 'patient':
        return jsonify({'error': 'Acesso restrito a pacientes'}), 403
    return None

@patient_portal_bp.route('/me', methods=['GET'])
@jwt_required()
def get_patient_profile():
    """Retorna dados do paciente logado"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    return jsonify(paciente.to_dict()), 200


@patient_portal_bp.route('/me/prontuario', methods=['GET'])
@jwt_required()
def get_my_medical_records():
    """Retorna prontuário completo do paciente"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    # TODO: Verificar se existe tabela de prontuários específica
    # Por enquanto, retornar dados do paciente + histórico de consultas
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Buscar consultas para montar histórico
    consultas = Consulta.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Consulta.data_hora)).all()
    
    prescricoes = Prescricao.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Prescricao.data_emissao)).all()

    evolucoes = Evolucao.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Evolucao.data_evolucao)).all()

    return jsonify({
        'paciente': paciente.to_dict(),
        'historico_consultas': [c.to_dict() for c in consultas],
        'total_consultas': len(consultas),
        'prescricoes': [_prescricao_paciente(p) for p in prescricoes],
        'evolucoes': [_evolucao_curada(e) for e in evolucoes],
        'total_evolucoes': len(evolucoes)
    }), 200


@patient_portal_bp.route('/me/consultas', methods=['GET'])
@jwt_required()
def get_my_consultations():
    """Histórico de consultas do paciente"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    # Parâmetros opcionais de filtro
    limit = request.args.get('limit', type=int, default=50)
    offset = request.args.get('offset', type=int, default=0)
    
    consultas_query = Consulta.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Consulta.data_hora))
    
    total = consultas_query.count()
    consultas = consultas_query.limit(limit).offset(offset).all()
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'consultas': [c.to_dict() for c in consultas]
    }), 200


def _prescricao_paciente(prescricao):
    """Prescrição no formato do portal: inclui os medicamentos do snapshot JSON.

    `arquivo_path` (caminho físico) nunca é exposto ao paciente; o PDF é
    obtido pela rota de download com validação de posse.
    """
    dados = prescricao.to_dict()
    dados.pop('arquivo_path', None)
    dados['data'] = dados.get('data_emissao')
    dados['tem_arquivo'] = bool(prescricao.arquivo_path)
    conteudo = prescricao.conteudo_json or {}
    medicamentos = conteudo.get('medicamentos') if isinstance(conteudo, dict) else None
    dados['medicamentos'] = medicamentos or []
    return dados


@patient_portal_bp.route('/me/prescricoes', methods=['GET'])
@jwt_required()
def get_my_prescriptions():
    """Prescrições (medicações) do paciente, com os medicamentos do snapshot."""
    error = require_patient()
    if error: return error

    paciente_id = get_jwt_identity()

    prescricoes = Prescricao.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Prescricao.data_emissao)).all()

    return jsonify({
        'total': len(prescricoes),
        'prescricoes': [_prescricao_paciente(p) for p in prescricoes]
    }), 200


def _exame_paciente(exame):
    """Exame no formato do portal: inclui valores laboratoriais, imagens e laudos.

    O paciente só recebe metadados de arquivos (nunca o caminho físico); o
    download passa por rota própria com validação de posse.
    """
    dados = exame.to_dict()
    dados['imagens'] = [
        {
            'id': img.id,
            'arquivo_nome': img.arquivo_nome,
            'laudo': img.laudo,
            'created_at': img.created_at.isoformat() if img.created_at else None,
            'tem_arquivo': bool(img.arquivo_caminho),
        }
        for img in (exame.imagens or [])
    ]
    dados['resultados_lab'] = [
        r.to_dict() for r in (exame.resultados_lab or [])
    ]
    return dados


@patient_portal_bp.route('/me/exames', methods=['GET'])
@jwt_required()
def get_my_exams():
    """Exames realizados pelo paciente (valores, imagens e laudos)"""
    error = require_patient()
    if error: return error

    paciente_id = get_jwt_identity()

    exames = Exame.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Exame.data_exame)).all()

    return jsonify({
        'total': len(exames),
        'exames': [_exame_paciente(e) for e in exames]
    }), 200


def _evolucao_curada(ev):
    """Evolução clínica em versão curada para o paciente.

    Expõe o essencial para o acompanhamento (resumo/avaliação, plano e sinais
    vitais), sem despejar anotações internas cruas (anamnese/exame físico).
    """
    resumo = (ev.avaliacao or '').strip()
    if not resumo and ev.nota_evolucao:
        resumo = ev.nota_evolucao.strip()
    profissional = None
    try:
        profissional = ev.profissional.nome if ev.profissional else None
    except Exception:  # noqa: BLE001
        profissional = None
    return {
        'id': ev.id,
        'data_evolucao': ev.data_evolucao.isoformat() if ev.data_evolucao else None,
        'profissional_nome': profissional,
        'resumo': resumo or None,
        'plano': (ev.plano or '').strip() or None,
        'sinais_vitais': ev.sinais_vitais,
        'fonte_origem': ev.fonte_origem,
    }


@patient_portal_bp.route('/me/evolucoes', methods=['GET'])
@jwt_required()
def get_my_evolutions():
    """Evoluções médicas do paciente (resumo curado)"""
    error = require_patient()
    if error: return error

    paciente_id = get_jwt_identity()

    evolucoes = Evolucao.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Evolucao.data_evolucao)).all()

    return jsonify({
        'total': len(evolucoes),
        'evolucoes': [_evolucao_curada(e) for e in evolucoes]
    }), 200


@patient_portal_bp.route('/me/perfil', methods=['PUT'])
@jwt_required()
def update_patient_profile():
    """Atualiza dados do perfil do paciente (limitado)"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Campos que o paciente pode atualizar
    allowed_fields = ['telefone', 'endereco']
    
    for field in allowed_fields:
        if field in data:
            setattr(paciente, field, data[field])
    
    paciente.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'paciente': paciente.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar perfil: {str(e)}'}), 500


@patient_portal_bp.route('/me/stats', methods=['GET'])
@jwt_required()
def get_my_stats():
    """Estatísticas do paciente (dashboard)"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    # Contar registros
    total_consultas = Consulta.query.filter_by(paciente_id=paciente_id).count()
    total_prescricoes = Prescricao.query.filter_by(paciente_id=paciente_id).count()
    # O modelo Prescricao não possui flag `ativo`; consideramos emitidas.
    prescricoes_ativas = total_prescricoes
    total_exames = Exame.query.filter_by(paciente_id=paciente_id).count()
    
    # Última consulta
    ultima_consulta = Consulta.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Consulta.data_hora)).first()
    
    # Próxima consulta (futura)
    proxima_consulta = Consulta.query.filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data_hora > datetime.utcnow()
    ).order_by(Consulta.data_hora).first()
    
    return jsonify({
        'total_consultas': total_consultas,
        'total_prescricoes': total_prescricoes,
        'prescricoes_ativas': prescricoes_ativas,
        'total_exames': total_exames,
        'ultima_consulta': ultima_consulta.to_dict() if ultima_consulta else None,
        'proxima_consulta': proxima_consulta.to_dict() if proxima_consulta else None
    }), 200


@patient_portal_bp.route('/me/alterar-senha', methods=['POST'])
@jwt_required()
def change_password():
    """Permite paciente alterar sua própria senha"""
    error = require_patient()
    if error: return error
    
    from werkzeug.security import generate_password_hash, check_password_hash
    
    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    senha_atual = data.get('senha_atual')
    senha_nova = data.get('senha_nova')
    
    if not senha_atual or not senha_nova:
        return jsonify({'error': 'Senha atual e nova são obrigatórias'}), 400
    
    # Verificar senha atual
    if not check_password_hash(paciente.senha_hash, senha_atual):
        return jsonify({'error': 'Senha atual incorreta'}), 401
    
    # Validar nova senha
    if len(senha_nova) < 6:
        return jsonify({'error': 'Nova senha deve ter no mínimo 6 caracteres'}), 400
    
    # Atualizar senha
    paciente.senha_hash = generate_password_hash(senha_nova)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Senha alterada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao alterar senha: {str(e)}'}), 500


# ─── Registros informados PELO paciente (sintomas/diário) ──────────────────
def _ensure_registros_table():
    db.session.execute(text(
        """
        CREATE TABLE IF NOT EXISTS patient_registros (
            id SERIAL PRIMARY KEY,
            paciente_id INTEGER NOT NULL,
            data DATE NOT NULL DEFAULT CURRENT_DATE,
            sintoma VARCHAR(200),
            intensidade INTEGER,
            observacao TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    ))
    db.session.commit()


@patient_portal_bp.route('/me/registros', methods=['GET'])
@jwt_required()
def list_my_registros():
    error = require_patient()
    if error: return error
    _ensure_registros_table()
    paciente_id = get_jwt_identity()
    rows = db.session.execute(text(
        "SELECT id, data, sintoma, intensidade, observacao FROM patient_registros "
        "WHERE paciente_id=:p ORDER BY id DESC LIMIT 100"
    ), {"p": paciente_id}).mappings().all()
    return jsonify({'total': len(rows), 'registros': [dict(r) for r in rows]}), 200


@patient_portal_bp.route('/me/registro', methods=['POST'])
@jwt_required()
def add_my_registro():
    error = require_patient()
    if error: return error
    _ensure_registros_table()
    paciente_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    sintoma = (data.get('sintoma') or '').strip()[:200] or None
    observacao = (data.get('observacao') or '').strip() or None
    try:
        intensidade = int(data.get('intensidade')) if data.get('intensidade') is not None else None
    except (ValueError, TypeError):
        intensidade = None
    if not sintoma and not observacao:
        return jsonify({'error': 'Informe ao menos o sintoma ou uma observação.'}), 400
    db.session.execute(text(
        "INSERT INTO patient_registros (paciente_id, sintoma, intensidade, observacao) "
        "VALUES (:p, :s, :i, :o)"
    ), {"p": paciente_id, "s": sintoma, "i": intensidade, "o": observacao})
    db.session.commit()
    return jsonify({'status': 'ok', 'message': 'Registro salvo.'}), 201



# ─── Check-in do paciente: sintomas em 1 toque + observacao por audio ───────
def _http_transcrever(url, path):
    """POST multipart (stdlib) do audio para o servico local de transcricao."""
    import json as _json
    import os as _os
    import urllib.request as _url
    import uuid as _uuid
    boundary = "----hermes" + _uuid.uuid4().hex
    with open(path, "rb") as fh:
        conteudo = fh.read()
    nome = _os.path.basename(path)
    corpo = b""
    corpo += ("--%s\r\n" % boundary).encode()
    corpo += ('Content-Disposition: form-data; name="audio"; filename="%s"\r\n' % nome).encode()
    corpo += b"Content-Type: application/octet-stream\r\n\r\n"
    corpo += conteudo + b"\r\n"
    corpo += ("--%s--\r\n" % boundary).encode()
    req = _url.Request(url.rstrip("/") + "/transcrever", data=corpo,
                       headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
    with _url.urlopen(req, timeout=180) as r:
        return (_json.loads(r.read().decode("utf-8", "replace")).get("texto") or "").strip()


def _transcrever_local(path, modelo="small"):
    """Transcricao LOCAL (LGPD) — o audio e descartado logo apos.
    Retorna o texto, ou None se o motor de transcricao nao estiver disponivel."""
    import os as _os
    url = _os.environ.get("TRANSCRICAO_URL")
    if url:
        try:
            texto = _http_transcrever(url, path)
            return texto if texto else None
        except Exception:
            return None
    global _WHISPER_CACHE
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None
    try:
        if _WHISPER_CACHE is None:
            _WHISPER_CACHE = WhisperModel(modelo, device="cpu", compute_type="int8",
                                          download_root="models/whisper")
        segmentos, _info = _WHISPER_CACHE.transcribe(path, language="pt", vad_filter=True)
        return " ".join(seg.text.strip() for seg in segmentos).strip()
    except Exception:
        return None


_WHISPER_CACHE = None


@patient_portal_bp.route('/me/sintomas-catalogo', methods=['GET'])
@jwt_required()
def checkin_catalogo():
    error = require_patient()
    if error: return error
    padrao = ['Dor', 'Ansiedade', 'Insônia', 'Depressão']
    personalizados = []
    try:
        _ensure_registros_table()
        rows = db.session.execute(text(
            "SELECT nome FROM sintomas_personalizados ORDER BY nome"
        )).fetchall()
        personalizados = [r[0] for r in rows]
    except Exception:
        personalizados = []
    itens = []
    for nome in padrao + personalizados:
        if nome and nome not in itens:
            itens.append(nome)
    return jsonify({'sintomas': itens}), 200


@patient_portal_bp.route('/me/checkin', methods=['POST'])
@jwt_required()
def checkin_salvar():
    error = require_patient()
    if error: return error
    _ensure_registros_table()
    paciente_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    sintomas = data.get('sintomas') or []
    observacao = (data.get('observacao') or '').strip() or None
    dia = data.get('data')
    try:
        dia_obj = datetime.strptime(dia, '%Y-%m-%d').date() if dia else None
    except (ValueError, TypeError):
        dia_obj = None

    salvos = 0
    for item in sintomas:
        nome = str(item.get('nome') or '').strip()[:200]
        if not nome:
            continue
        try:
            intensidade = int(item.get('intensidade'))
        except (ValueError, TypeError):
            intensidade = None
        if intensidade is not None:
            intensidade = max(0, min(10, intensidade))
        if dia_obj:
            db.session.execute(text(
                "INSERT INTO patient_registros (paciente_id, data, sintoma, intensidade, observacao) "
                "VALUES (:p, :d, :s, :i, :o)"
            ), {"p": paciente_id, "d": dia_obj, "s": nome, "i": intensidade, "o": None})
        else:
            db.session.execute(text(
                "INSERT INTO patient_registros (paciente_id, sintoma, intensidade, observacao) "
                "VALUES (:p, :s, :i, :o)"
            ), {"p": paciente_id, "s": nome, "i": intensidade, "o": None})
        salvos += 1

    if observacao:
        if dia_obj:
            db.session.execute(text(
                "INSERT INTO patient_registros (paciente_id, data, sintoma, intensidade, observacao) "
                "VALUES (:p, :d, NULL, NULL, :o)"
            ), {"p": paciente_id, "d": dia_obj, "o": observacao})
        else:
            db.session.execute(text(
                "INSERT INTO patient_registros (paciente_id, sintoma, intensidade, observacao) "
                "VALUES (:p, NULL, NULL, :o)"
            ), {"p": paciente_id, "o": observacao})
        salvos += 1

    if salvos == 0:
        return jsonify({'error': 'Selecione ao menos um sintoma ou escreva uma observacao.'}), 400
    db.session.commit()
    return jsonify({'status': 'ok', 'salvos': salvos, 'message': 'Registrado. Obrigado!'}), 201


@patient_portal_bp.route('/me/checkin/resumo', methods=['GET'])
@jwt_required()
def checkin_resumo():
    error = require_patient()
    if error: return error
    _ensure_registros_table()
    paciente_id = get_jwt_identity()
    rows = db.session.execute(text(
        "SELECT id, data, sintoma, intensidade, observacao FROM patient_registros "
        "WHERE paciente_id=:p ORDER BY data DESC, id DESC LIMIT 30"
    ), {"p": paciente_id}).mappings().all()

    def _iso(v):
        if v is None:
            return None
        return v.isoformat() if hasattr(v, 'isoformat') else str(v)[:10]

    conj = set()
    for r in rows:
        iso = _iso(r['data'])
        if iso:
            conj.add(iso)
    streak = 0
    from datetime import timedelta
    cursor = datetime.utcnow().date()
    while cursor.isoformat() in conj:
        streak += 1
        cursor = cursor - timedelta(days=1)

    registros = []
    for r in rows:
        registros.append({
            'data': _iso(r['data']),
            'sintoma': r['sintoma'],
            'intensidade': r['intensidade'],
            'observacao': r['observacao'],
        })
    return jsonify({'streak': streak, 'registros': registros}), 200


@patient_portal_bp.route('/me/observacao-audio', methods=['POST'])
@jwt_required()
def checkin_observacao_audio():
    """Recebe um audio curto do paciente, transcreve LOCALMENTE e devolve o texto.
    O arquivo de audio e DESCARTADO logo apos a transcricao (LGPD)."""
    error = require_patient()
    if error: return error
    if 'audio' not in request.files:
        return jsonify({'error': 'Audio nao enviado.'}), 400
    f = request.files['audio']
    if not f or not f.filename:
        return jsonify({'error': 'Audio vazio.'}), 400
    import os as _os, tempfile as _tempfile
    sufixo = _os.path.splitext(f.filename)[1] or '.webm'
    tmp = _tempfile.NamedTemporaryFile(delete=False, suffix=sufixo)
    tmp_path = tmp.name
    tmp.close()
    f.save(tmp_path)
    try:
        texto = _transcrever_local(tmp_path)
    finally:
        try:
            _os.remove(tmp_path)
        except OSError:
            pass
    if texto is None:
        return jsonify({'error': 'Transcricao indisponivel no momento. Use o campo de texto.'}), 503
    return jsonify({'texto': texto}), 200
