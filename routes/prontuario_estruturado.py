"""Prontuário estruturado — F1 (módulo base).

Sinais vitais, exame físico por sistema e diagnósticos (CID) como
entidades próprias. Convive com o SOAP legado em Evolucao.

Rotas (url_prefix /api/prontuario):
    GET    /paciente/<id>/sinais-vitais            lista medições
    POST   /paciente/<id>/sinais-vitais            cria medição (IMC calculado)
    PUT    /sinais-vitais/<id>                     atualiza
    DELETE /sinais-vitais/<id>                     remove
    GET    /paciente/<id>/exame-fisico             lista por sistema
    POST   /paciente/<id>/exame-fisico             cria registro (1+ sistemas)
    PUT    /exame-fisico/<id>                      atualiza
    DELETE /exame-fisico/<id>                      remove
    GET    /paciente/<id>/diagnosticos             lista
    POST   /paciente/<id>/diagnosticos             cria
    PUT    /diagnosticos/<id>                      atualiza
    DELETE /diagnosticos/<id>                      remove (soft delete: ativo=false)
    GET    /cids?q=prefixo                         autocomplete simples de CID
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Paciente, Profissional
from models import (
    EvolucaoSinaisVitais,
    EvolucaoExameFisico,
    Diagnostico,
    LogAtividade,
)
from datetime import datetime

prontuario_bp = Blueprint("prontuario_estruturado", __name__)


# ───────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────
def _calcular_imc(peso, altura):
    """IMC = peso(kg) / altura(m)². Retorna float ou None."""
    try:
        peso_f = float(peso)
        altura_f = float(altura)
        if peso_f <= 0 or altura_f <= 0:
            return None
        imc = peso_f / (altura_f * altura_f)
        return round(imc, 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _get_profissional():
    current_user_id = get_jwt_identity()
    return int(current_user_id)


def _clean_null(value):
    """Converte '' (string vazia do frontend) para None."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _clean_int(value):
    """Converte string vazia -> None; caso contrário tenta int()."""
    v = _clean_null(value)
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _clean_float(value):
    """Converte string vazia -> None; caso contrário tenta float()."""
    v = _clean_null(value)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _assoc_id():
    from flask import g
    assoc = getattr(g, "current_association", None)
    return getattr(assoc, "id", None)


def _paciente_existe(paciente_id):
    paciente = Paciente.query.get(paciente_id)
    return paciente


def _registrar_log(paciente_id, profissional_id, acao, detalhe=None):
    try:
        from flask import g
        assoc = getattr(g, "current_association", None)
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=getattr(assoc, "id", None),
            acao=acao,
            detalhes=detalhe or f"paciente_id={paciente_id}",
        )
        db.session.add(log)
    except Exception:
        pass


# ───────────────────────────────────────────────────────────
# Sinais Vitais
# ───────────────────────────────────────────────────────────
@prontuario_bp.route("/paciente/<int:paciente_id>/sinais-vitais", methods=["GET"])
@jwt_required()
def listar_sinais_vitais(paciente_id):
    profissional_id = _get_profissional()
    if not _paciente_existe(paciente_id):
        return jsonify({"error": "Paciente não encontrado"}), 404

    query = EvolucaoSinaisVitais.query.filter_by(paciente_id=paciente_id)
    limite = request.args.get("limite", type=int)
    if limite:
        query = query.order_by(EvolucaoSinaisVitais.data_medicao.desc()).limit(limite)
    else:
        query = query.order_by(EvolucaoSinaisVitais.data_medicao.asc())
    itens = query.all()
    return jsonify({"sinais_vitais": [v.to_dict() for v in itens]}), 200


@prontuario_bp.route("/paciente/<int:paciente_id>/sinais-vitais", methods=["POST"])
@jwt_required()
def criar_sinais_vitais(paciente_id):
    profissional_id = _get_profissional()
    if not _paciente_existe(paciente_id):
        return jsonify({"error": "Paciente não encontrado"}), 404

    data = request.get_json() or {}
    peso = _clean_float(data.get("peso"))
    altura = _clean_float(data.get("altura"))
    imc = _calcular_imc(peso, altura)

    medicoes = EvolucaoSinaisVitais(
        associacao_id=_assoc_id(),
        evolucao_id=data.get("evolucao_id"),
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        data_medicao=(
            datetime.fromisoformat(data["data_medicao"])
            if data.get("data_medicao")
            else datetime.utcnow()
        ),
        pa_sistolica=_clean_int(data.get("pa_sistolica")),
        pa_diastolica=_clean_int(data.get("pa_diastolica")),
        fc=_clean_int(data.get("fc")),
        fr=_clean_int(data.get("fr")),
        temperatura=_clean_float(data.get("temperatura")),
        spo2=_clean_int(data.get("spo2")),
        glicemia=_clean_float(data.get("glicemia")),
        peso=peso,
        altura=altura,
        imc=imc,
        observacoes=data.get("observacoes") or None,
    )
    db.session.add(medicoes)
    db.session.flush()
    _registrar_log(paciente_id, profissional_id, "sinais_vitais_registrados")
    db.session.commit()
    return jsonify({"sinais_vitais": medicoes.to_dict(), "imc_calculado": imc}), 201


@prontuario_bp.route("/sinais-vitais/<int:sinais_id>", methods=["PUT"])
@jwt_required()
def atualizar_sinais_vitais(sinais_id):
    profissional_id = _get_profissional()
    medicoes = EvolucaoSinaisVitais.query.get(sinais_id)
    if not medicoes:
        return jsonify({"error": "Medição não encontrada"}), 404

    data = request.get_json() or {}
    if "peso" in data:
        medicoes.peso = _clean_float(data["peso"])
    if "altura" in data:
        medicoes.altura = _clean_float(data["altura"])
    if "peso" in data or "altura" in data:
        medicoes.imc = _calcular_imc(medicoes.peso, medicoes.altura)
    campos_int = ("pa_sistolica", "pa_diastolica", "fc", "fr", "spo2")
    for campo in campos_int:
        if campo in data:
            setattr(medicoes, campo, _clean_int(data[campo]))
    campos_float = ("temperatura", "glicemia")
    for campo in campos_float:
        if campo in data:
            setattr(medicoes, campo, _clean_float(data[campo]))
    if "observacoes" in data:
        medicoes.observacoes = data["observacoes"] or None
    if "evolucao_id" in data:
        medicoes.evolucao_id = _clean_int(data["evolucao_id"]) or None
    if data.get("data_medicao"):
        medicoes.data_medicao = datetime.fromisoformat(data["data_medicao"])
    _registrar_log(medicoes.paciente_id, profissional_id, "sinais_vitais_atualizados")
    db.session.commit()
    return jsonify({"sinais_vitais": medicoes.to_dict()}), 200


@prontuario_bp.route("/sinais-vitais/<int:sinais_id>", methods=["DELETE"])
@jwt_required()
def excluir_sinais_vitais(sinais_id):
    profissional_id = _get_profissional()
    medicoes = EvolucaoSinaisVitais.query.get(sinais_id)
    if not medicoes:
        return jsonify({"error": "Medição não encontrada"}), 404
    paciente_id = medicoes.paciente_id
    db.session.delete(medicoes)
    _registrar_log(paciente_id, profissional_id, "sinais_vitais_excluidos")
    db.session.commit()
    return jsonify({"message": "Medição removida"}), 200


# ───────────────────────────────────────────────────────────
# Exame Físico (por sistema)
# ───────────────────────────────────────────────────────────
SISTEMAS_VALIDOS = {
    "geral", "cardiovascular", "respiratorio", "abdominal",
    "neurologico", "pele", "osteomuscular", "cabeca_pescoco",
    "geniturinario", "outros",
}


@prontuario_bp.route("/paciente/<int:paciente_id>/exame-fisico", methods=["GET"])
@jwt_required()
def listar_exame_fisico(paciente_id):
    profissional_id = _get_profissional()
    if not _paciente_existe(paciente_id):
        return jsonify({"error": "Paciente não encontrado"}), 404

    query = EvolucaoExameFisico.query.filter_by(paciente_id=paciente_id)
    limite = request.args.get("limite", type=int)
    if limite:
        query = query.order_by(EvolucaoExameFisico.data_exame.desc()).limit(limite)
    else:
        query = query.order_by(EvolucaoExameFisico.data_exame.asc())
    itens = query.all()
    return jsonify({"exame_fisico": [e.to_dict() for e in itens]}), 200


@prontuario_bp.route("/paciente/<int:paciente_id>/exame-fisico", methods=["POST"])
@jwt_required()
def criar_exame_fisico(paciente_id):
    profissional_id = _get_profissional()
    if not _paciente_existe(paciente_id):
        return jsonify({"error": "Paciente não encontrado"}), 404

    data = request.get_json() or {}
    registros = data.get("sistemas") or []
    # Aceita também payload único: {sistema, achados}
    if not registros and data.get("sistema"):
        registros = [data]

    if not registros:
        return jsonify({"error": "Informe ao menos um sistema com achados"}), 400

    criados = []
    for reg in registros:
        sistema = (reg.get("sistema") or "").strip().lower()
        if sistema not in SISTEMAS_VALIDOS:
            return jsonify({
                "error": f"Sistema inválido: {sistema}",
                "sistemas_validos": sorted(SISTEMAS_VALIDOS),
            }), 400
        item = EvolucaoExameFisico(
            associacao_id=_assoc_id(),
            evolucao_id=data.get("evolucao_id") or reg.get("evolucao_id"),
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            sistema=sistema,
            achados=reg.get("achados"),
            data_exame=(
                datetime.fromisoformat(reg["data_exame"])
                if reg.get("data_exame")
                else datetime.utcnow()
            ),
        )
        db.session.add(item)
        criados.append(item)
    db.session.flush()
    _registrar_log(paciente_id, profissional_id, "exame_fisico_registrado",
                   f"{len(criados)} sistemas")
    db.session.commit()
    return jsonify({"exame_fisico": [e.to_dict() for e in criados]}), 201


@prontuario_bp.route("/exame-fisico/<int:exame_fisico_id>", methods=["PUT"])
@jwt_required()
def atualizar_exame_fisico(exame_fisico_id):
    profissional_id = _get_profissional()
    item = EvolucaoExameFisico.query.get(exame_fisico_id)
    if not item:
        return jsonify({"error": "Registro não encontrado"}), 404

    data = request.get_json() or {}
    if "sistema" in data:
        sistema = (data["sistema"] or "").strip().lower()
        if sistema not in SISTEMAS_VALIDOS:
            return jsonify({"error": f"Sistema inválido: {sistema}"}), 400
        item.sistema = sistema
    if "achados" in data:
        item.achados = data["achados"]
    if "data_exame" in data:
        item.data_exame = datetime.fromisoformat(data["data_exame"])
    if "evolucao_id" in data:
        item.evolucao_id = data["evolucao_id"]
    _registrar_log(item.paciente_id, profissional_id, "exame_fisico_atualizado")
    db.session.commit()
    return jsonify({"exame_fisico": item.to_dict()}), 200


@prontuario_bp.route("/exame-fisico/<int:exame_fisico_id>", methods=["DELETE"])
@jwt_required()
def excluir_exame_fisico(exame_fisico_id):
    profissional_id = _get_profissional()
    item = EvolucaoExameFisico.query.get(exame_fisico_id)
    if not item:
        return jsonify({"error": "Registro não encontrado"}), 404
    paciente_id = item.paciente_id
    db.session.delete(item)
    _registrar_log(paciente_id, profissional_id, "exame_fisico_excluido")
    db.session.commit()
    return jsonify({"message": "Registro removido"}), 200


# ───────────────────────────────────────────────────────────
# Diagnósticos (CID)
# ───────────────────────────────────────────────────────────
@prontuario_bp.route("/paciente/<int:paciente_id>/diagnosticos", methods=["GET"])
@jwt_required()
def listar_diagnosticos(paciente_id):
    profissional_id = _get_profissional()
    if not _paciente_existe(paciente_id):
        return jsonify({"error": "Paciente não encontrado"}), 404

    incluir_inativos = request.args.get("incluir_inativos") == "true"
    query = Diagnostico.query.filter_by(paciente_id=paciente_id)
    if not incluir_inativos:
        query = query.filter_by(ativo=True)
    query = query.order_by(Diagnostico.data_diagnostico.asc())
    return jsonify({"diagnosticos": [d.to_dict() for d in query.all()]}), 200


@prontuario_bp.route("/paciente/<int:paciente_id>/diagnosticos", methods=["POST"])
@jwt_required()
def criar_diagnostico(paciente_id):
    profissional_id = _get_profissional()
    if not _paciente_existe(paciente_id):
        return jsonify({"error": "Paciente não encontrado"}), 404

    data = request.get_json() or {}
    descricao = (data.get("descricao") or "").strip()
    if not descricao:
        return jsonify({"error": "Descrição do diagnóstico é obrigatória"}), 400

    tipo = data.get("tipo") or "hipotese"
    if tipo not in ("hipotese", "definitivo"):
        return jsonify({"error": "tipo deve ser 'hipotese' ou 'definitivo'"}), 400

    diagnostico = Diagnostico(
        associacao_id=_assoc_id(),
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        cid=(data.get("cid") or "").strip().upper() or None,
        descricao=descricao,
        tipo=tipo,
        data_diagnostico=(
            datetime.fromisoformat(data["data_diagnostico"])
            if data.get("data_diagnostico")
            else datetime.utcnow()
        ),
        ativo=data.get("ativo", True),
    )
    db.session.add(diagnostico)
    db.session.flush()
    _registrar_log(paciente_id, profissional_id, "diagnostico_registrado", descricao)
    db.session.commit()
    return jsonify({"diagnostico": diagnostico.to_dict()}), 201


@prontuario_bp.route("/diagnosticos/<int:diagnostico_id>", methods=["PUT"])
@jwt_required()
def atualizar_diagnostico(diagnostico_id):
    profissional_id = _get_profissional()
    diagnostico = Diagnostico.query.get(diagnostico_id)
    if not diagnostico:
        return jsonify({"error": "Diagnóstico não encontrado"}), 404

    data = request.get_json() or {}
    if "descricao" in data:
        descricao = (data["descricao"] or "").strip()
        if not descricao:
            return jsonify({"error": "Descrição não pode ser vazia"}), 400
        diagnostico.descricao = descricao
    if "cid" in data:
        diagnostico.cid = (data["cid"] or "").strip().upper() or None
    if "tipo" in data:
        if data["tipo"] not in ("hipotese", "definitivo"):
            return jsonify({"error": "tipo deve ser 'hipotese' ou 'definitivo'"}), 400
        diagnostico.tipo = data["tipo"]
    if "ativo" in data:
        diagnostico.ativo = bool(data["ativo"])
    if "data_diagnostico" in data:
        diagnostico.data_diagnostico = datetime.fromisoformat(data["data_diagnostico"])
    _registrar_log(diagnostico.paciente_id, profissional_id, "diagnostico_atualizado")
    db.session.commit()
    return jsonify({"diagnostico": diagnostico.to_dict()}), 200


@prontuario_bp.route("/diagnosticos/<int:diagnostico_id>", methods=["DELETE"])
@jwt_required()
def excluir_diagnostico(diagnostico_id):
    profissional_id = _get_profissional()
    diagnostico = Diagnostico.query.get(diagnostico_id)
    if not diagnostico:
        return jsonify({"error": "Diagnóstico não encontrado"}), 404
    # Soft delete: preserva histórico clínico
    diagnostico.ativo = False
    _registrar_log(diagnostico.paciente_id, profissional_id, "diagnostico_excluido")
    db.session.commit()
    return jsonify({"message": "Diagnóstico desativado"}), 200


# ───────────────────────────────────────────────────────────
# Autocomplete CID
# ───────────────────────────────────────────────────────────
_CID_PREFIXOS = {
    "A": "Algumas doenças infecciosas e parasitárias",
    "B": "Algumas doenças infecciosas e parasitárias",
    "C": "Neoplasias (tumores)",
    "D": "Neoplasias; doenças do sangue e órgãos hematopoéticos",
    "E": "Doenças endócrinas, nutricionais e metabólicas",
    "F": "Transtornos mentais e comportamentais",
    "G": "Doenças do sistema nervoso",
    "H": "Doenças do olho e anexos; ouvido e apófise mastoide",
    "I": "Doenças do aparelho circulatório",
    "J": "Doenças do aparelho respiratório",
    "K": "Doenças do aparelho digestivo",
    "L": "Doenças da pele e tecido subcutâneo",
    "M": "Doenças do sistema osteomuscular e tecido conjuntivo",
    "N": "Doenças do aparelho geniturinário",
    "O": "Gravidez, parto e puerpério",
    "P": "Algumas afecções originadas no período perinatal",
    "Q": "Malformações congênitas, deformidades e anomalias cromossômicas",
    "R": "Sintomas, sinais e achados anormais",
    "S": "Lesões, envenenamentos e outras consequências de causas externas",
    "T": "Lesões, envenenamentos e outras consequências de causas externas",
    "U": "Códigos para propósitos especiais",
    "V": "Causas externas de morbidade e mortalidade",
    "W": "Causas externas de morbidade e mortalidade",
    "X": "Causas externas de morbidade e mortalidade",
    "Y": "Causas externas de morbidade e mortalidade",
    "Z": "Fatores que influenciam o estado de saúde",
}


@prontuario_bp.route("/cids", methods=["GET"])
@jwt_required()
def autocomplete_cid():
    q = (request.args.get("q") or "").strip().upper()
    if not q:
        return jsonify({"cids": []}), 200
    # Sugestões: letra do capítulo + prefixos alfanuméricos comuns
    letra = q[0]
    capitulo = _CID_PREFIXOS.get(letra, "Capítulo CID-10")
    sugestoes = []
    if len(q) <= 3:
        # Gera prefixos plausíveis: letra + dígitos
        base = letra
        for d1 in "0123456789":
            sugestoes.append({
                "cid": f"{base}{d1}",
                "descricao": f"Capítulo {letra} — {capitulo} (categoria {base}{d1}...)",
            })
    # Filtra pela query
    sugestoes = [s for s in sugestoes if s["cid"].startswith(q)]
    # Busca por CID já registrado no sistema (mais preciso)
    existentes = (
        Diagnostico.query.filter(Diagnostico.cid.like(f"{q}%"))
        .with_entities(Diagnostico.cid, Diagnostico.descricao)
        .distinct()
        .limit(10)
        .all()
    )
    for cid, desc in existentes:
        if all(s["cid"] != cid for s in sugestoes):
            sugestoes.append({"cid": cid, "descricao": desc})
    return jsonify({"cids": sugestoes[:15]}), 200
