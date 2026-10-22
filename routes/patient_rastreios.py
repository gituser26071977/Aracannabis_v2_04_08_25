"""Rastreios autoaplicáveis de adulto no Portal do Paciente.

PHQ-9, GAD-7 e Beck (BDI-II) respondidos pelo próprio paciente autenticado.
Os textos dos itens e das opções são copiados literalmente dos componentes
frontend/src/components/{PHQ9Test,GAD7Test,BeckDepressionTest}.js.
"""

import logging
import os
from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import (
    db,
    Paciente,
    PHQ9Teste,
    GAD7Teste,
    BeckDepressionTeste,
    SnapIVTeste,
    Evolucao,
)
from routes.patient_portal import require_patient

patient_rastreios_bp = Blueprint('patient_rastreios', __name__)

logger = logging.getLogger(__name__)

_ORIGEM = "Preenchido pelo paciente no portal"
_ORIGEM_SNAP = "Preenchido pelo responsavel no portal"

_OPCOES_PHQ9 = [
    {"valor": 0, "label": "Nunca"},
    {"valor": 1, "label": "Vários dias"},
    {"valor": 2, "label": "Mais da metade"},
    {"valor": 3, "label": "Quase todos"},
]

_OPCOES_GAD7 = [
    {"valor": 0, "label": "Nenhuma vez"},
    {"valor": 1, "label": "Vários dias"},
    {"valor": 2, "label": "Mais da metade dos dias"},
    {"valor": 3, "label": "Quase todos os dias"},
]

_OPCOES_BECK = [
    {"valor": 0, "label": "Não"},
    {"valor": 1, "label": "Levemente"},
    {"valor": 2, "label": "Moderadamente"},
    {"valor": 3, "label": "Gravemente"},
]

_PERGUNTAS_PHQ9 = [
    "Pouco interesse ou pouco prazer em fazer as coisas",
    "Sentir-se para baixo, deprimido ou sem esperanças",
    "Dificuldade para pegar no sono ou permanecer dormindo, ou dormir demais",
    "Sentir-se cansado ou com pouca energia",
    "Falta de apetite ou comer demais",
    "Sentir-se mal consigo mesmo – ou achar que é um fracasso ou que decepcionou a família ou você mesmo",
    "Dificuldade de concentração nas atividades (ex.: ler jornal, ver TV)",
    "Lentidão para se movimentar ou falar, a ponto de outras pessoas perceberem; ou o oposto, agitação ou inquietação excessiva",
    "Pensamentos de que seria melhor estar morto ou de se ferir de alguma maneira",
]

_PERGUNTAS_GAD7 = [
    "Sentindo-se nervoso(a), ansioso(a) ou muito tenso(a)",
    "Não sendo capaz de impedir ou de controlar as preocupações",
    "Preocupando-se muito com diversas coisas",
    "Tendo dificuldade para relaxar",
    "Ficando tão agitado(a) que se torna difícil permanecer sentado(a)",
    "Ficando facilmente aborrecido(a) ou irritado(a)",
    "Sentindo medo como se algo horrível fosse acontecer",
]

_PERGUNTAS_BECK = [
    "Tristeza: Sinto-me triste.",
    "Pessimismo: Sinto-me tão desanimado(a) com o futuro que não espero que as coisas melhorem.",
    "Fracasso passado: Sinto que sou um fracasso.",
    "Perda de prazer: Não tenho prazer nas coisas que antes me davam prazer.",
    "Sentimentos de culpa: Sinto-me culpado(a) a maior parte do tempo.",
    "Sentimentos de punição: Sinto que estou sendo punido(a).",
    "Autoaversão: Sinto aversão por mim mesmo(a).",
    "Autocrítica: Critico-me a mim mesmo(a) por minhas fraquezas ou erros.",
    "Pensamentos suicidas: Tenho pensamentos de me matar, mas não os executaria.",
    "Choro: Choro mais do que o habitual.",
    "Agitação: Sinto-me mais irritado(a) do que o habitual.",
    "Perda de interesse: Perdi o interesse pelas outras pessoas.",
    "Indecisão: Tenho dificuldade em tomar decisões.",
    "Desvalia: Sinto-me sem valor.",
    "Perda de energia: Não tenho energia suficiente para fazer as coisas.",
    "Mudanças no sono: Meu padrão de sono mudou (durmo mais ou durmo menos do que o habitual).",
    "Irritabilidade: Sinto-me irritado(a) facilmente.",
    "Mudanças no apetite: Meu apetite mudou (como mais ou como menos do que o habitual).",
    "Dificuldade de concentração: Tenho dificuldade em me concentrar.",
    "Cansaço/fadiga: Sinto-me cansado(a) o tempo todo.",
    "Perda de interesse sexual: Perdi o interesse pelo sexo.",
]

_OPCOES_SNAP = [
    {"valor": 0, "label": "Nunca"},
    {"valor": 1, "label": "Pouco"},
    {"valor": 2, "label": "Bastante"},
    {"valor": 3, "label": "Demais"},
]

# Enunciados literais de frontend/src/components/SnapIVTest.js (sem o número inicial).
_PERGUNTAS_SNAP = [
    "Não presta atenção em detalhes ou comete erros por descuido.",
    "Tem dificuldade de manter a atenção em tarefas ou atividades lúdicas.",
    "Parece não ouvir quando se fala diretamente com ele(a).",
    "Não segue instruções e não termina deveres ou tarefas.",
    "Tem dificuldade para organizar tarefas e atividades.",
    "Evita, não gosta ou reluta em se envolver em tarefas que exijam esforço mental prolongado.",
    "Perde coisas necessárias para tarefas ou atividades.",
    "É facilmente distraído(a) por estímulos externos.",
    "É esquecido(a) em atividades diárias.",
    "Agita as mãos ou os pés ou se remexe na cadeira.",
    "Levanta-se da cadeira em situações em que se espera que permaneça sentado.",
    "Corre ou sobe nas coisas em situações em que isso é inapropriado.",
    "É incapaz de brincar ou se envolver em atividades de lazer calmamente.",
    "Está frequentemente 'a todo vapor', agindo como se estivesse 'ligado na tomada'.",
    "Fala demais.",
    "Deixa escapar uma resposta antes que a pergunta tenha sido concluída.",
    "Tem dificuldade de esperar a sua vez.",
    "Interrompe ou se intromete em conversas ou brincadeiras dos outros.",
]

# SNAP-IV usa dois prefixos: itens 1-9 = desatencao_N, itens 10-18 = hiperatividade_N.
_CAMPOS_SNAP = [f"desatencao_{i}" for i in range(1, 10)] + [
    f"hiperatividade_{i}" for i in range(10, 19)
]

INSTRUMENTOS = {
    "phq9": {
        "chave": "phq9",
        "nome": "PHQ-9 — Questionário de Saúde do Paciente",
        "descricao": "Rastreio de sintomas depressivos nas últimas duas semanas.",
        "instrucoes": "Nas últimas duas semanas, com que frequência você foi incomodado por:",
        "prefixo": "q",
        "campos": [f"q{i}" for i in range(1, 10)],
        "perguntas": _PERGUNTAS_PHQ9,
        "opcoes": _OPCOES_PHQ9,
        "maximo": 27,
        "publico": "paciente",
        "somente_menor": False,
    },
    "gad7": {
        "chave": "gad7",
        "nome": "GAD-7 — Transtorno de Ansiedade Generalizada",
        "descricao": "Rastreio de sintomas ansiosos nas últimas duas semanas.",
        "instrucoes": "Nas últimas 2 semanas, com que frequência você foi incomodado(a) pelos problemas abaixo?",
        "prefixo": "q",
        "campos": [f"q{i}" for i in range(1, 8)],
        "perguntas": _PERGUNTAS_GAD7,
        "opcoes": _OPCOES_GAD7,
        "maximo": 21,
        "publico": "paciente",
        "somente_menor": False,
    },
    "beck": {
        "chave": "beck",
        "nome": "Inventário de Depressão de Beck (BDI-II)",
        "descricao": "Rastreio de sintomas depressivos na última semana.",
        "instrucoes": "Avalie cada afirmação de acordo com como você se sentiu na última semana, incluindo hoje.",
        "prefixo": "item_",
        "campos": [f"item_{i}" for i in range(1, 22)],
        "perguntas": _PERGUNTAS_BECK,
        "opcoes": _OPCOES_BECK,
        "maximo": 63,
        "publico": "paciente",
        "somente_menor": False,
    },
    "snap": {
        "chave": "snap",
        "nome": "SNAP-IV — Triagem de TDAH (para o responsável responder)",
        "descricao": "Triagem de sintomas de desatenção e hiperatividade/impulsividade em crianças e adolescentes.",
        "instrucoes": "Avalie a frequência de cada comportamento nas últimas semanas:",
        "campos": _CAMPOS_SNAP,
        "perguntas": _PERGUNTAS_SNAP,
        "opcoes": _OPCOES_SNAP,
        "maximo": 18,
        "publico": "responsavel",
        "somente_menor": True,
        "aviso": "Este questionário deve ser respondido pelo pai/mãe/responsável, pensando na criança.",
    },
}

_NIVEL_LABEL = {
    "minima": "Mínima",
    "leve": "Leve",
    "moderada": "Moderada",
    "moderadamente_grave": "Moderadamente grave",
    "grave": "Grave",
}


def _campos(inst):
    """Nomes dos campos de resposta, na ordem das perguntas.

    Usa a chave ``campos`` quando definida (ex.: SNAP-IV, com dois prefixos)
    e mantém retrocompatibilidade com ``prefixo`` para os demais instrumentos.
    """
    campos = inst.get("campos")
    if campos:
        return list(campos)
    return [f"{inst['prefixo']}{i}" for i in range(1, len(inst["perguntas"]) + 1)]


def _instrumento_publico(chave):
    inst = INSTRUMENTOS[chave]
    campos = _campos(inst)
    perguntas = [
        {"campo": campo, "numero": i, "texto": texto}
        for i, (campo, texto) in enumerate(zip(campos, inst["perguntas"]), start=1)
    ]
    return {
        "chave": chave,
        "nome": inst["nome"],
        "descricao": inst["descricao"],
        "instrucoes": inst["instrucoes"],
        "n_itens": len(perguntas),
        "perguntas": perguntas,
        "opcoes": inst["opcoes"],
        "pontuacao_maxima": inst["maximo"],
        "publico": inst.get("publico", "paciente"),
        "somente_menor": bool(inst.get("somente_menor", False)),
        "aviso": inst.get("aviso"),
    }


def _nivel_label(nivel):
    return _NIVEL_LABEL.get(nivel, nivel or "")


def _idade_paciente(paciente):
    """Idade em anos a partir de data_nascimento, ou None se não informada."""
    if not paciente.data_nascimento:
        return None
    hoje = date.today()
    nasc = paciente.data_nascimento
    return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))


def _bloqueio_snap(paciente):
    """403 quando o SNAP-IV não é aplicável ao paciente (regra de idade)."""
    if not paciente.data_nascimento:
        return jsonify({
            'error': 'Este questionario e respondido pelo responsavel e exige a data de nascimento do paciente.'
        }), 403
    idade = _idade_paciente(paciente)
    if idade is None or idade >= 18:
        return jsonify({
            'error': 'O SNAP-IV e destinado a pacientes menores de 18 anos.'
        }), 403
    return None


def _instrumento_disponivel(chave, paciente):
    """Instrumentos restritos a menores só aparecem com idade compatível."""
    inst = INSTRUMENTOS[chave]
    if inst.get("somente_menor"):
        idade = _idade_paciente(paciente)
        if idade is None or idade >= 18:
            return False
    return True


def _snap_nivel_code(resultados):
    if resultados['sugestivo_desatencao'] and resultados['sugestivo_hiperatividade']:
        return "sugestivo_combinado"
    if resultados['sugestivo_desatencao']:
        return "sugestivo_desatencao"
    if resultados['sugestivo_hiperatividade']:
        return "sugestivo_hiperatividade"
    return "sem_indicacao"


def _snap_nivel_label(resultados):
    if resultados['sugestivo_desatencao'] and resultados['sugestivo_hiperatividade']:
        return "Sugestivo para desatenção e hiperatividade/impulsividade"
    if resultados['sugestivo_desatencao']:
        return "Sugestivo para desatenção"
    if resultados['sugestivo_hiperatividade']:
        return "Sugestivo para hiperatividade/impulsividade"
    return "Sem indicação clínica"


def _historico(paciente_id):
    registros = []

    for teste in PHQ9Teste.query.filter_by(paciente_id=paciente_id).all():
        registros.append({
            "id": teste.id,
            "tipo": "phq9",
            "nome": INSTRUMENTOS["phq9"]["nome"],
            "data_realizacao": teste.data_realizacao.isoformat() if teste.data_realizacao else None,
            "pontuacao_total": teste.pontuacao_total,
            "pontuacao_maxima": INSTRUMENTOS["phq9"]["maximo"],
            "nivel": teste.nivel_depressao,
            "nivel_label": _nivel_label(teste.nivel_depressao),
        })

    for teste in GAD7Teste.query.filter_by(paciente_id=paciente_id).all():
        registros.append({
            "id": teste.id,
            "tipo": "gad7",
            "nome": INSTRUMENTOS["gad7"]["nome"],
            "data_realizacao": teste.data_realizacao.isoformat() if teste.data_realizacao else None,
            "pontuacao_total": teste.pontuacao_total,
            "pontuacao_maxima": INSTRUMENTOS["gad7"]["maximo"],
            "nivel": teste.nivel_ansiedade,
            "nivel_label": _nivel_label(teste.nivel_ansiedade),
        })

    for teste in BeckDepressionTeste.query.filter_by(paciente_id=paciente_id).all():
        registros.append({
            "id": teste.id,
            "tipo": "beck",
            "nome": INSTRUMENTOS["beck"]["nome"],
            "data_realizacao": teste.data_realizacao.isoformat() if teste.data_realizacao else None,
            "pontuacao_total": teste.pontuacao_total,
            "pontuacao_maxima": INSTRUMENTOS["beck"]["maximo"],
            "nivel": teste.nivel_depressao,
            "nivel_label": _nivel_label(teste.nivel_depressao),
        })

    for teste in SnapIVTeste.query.filter_by(paciente_id=paciente_id).all():
        resultados = {
            "sugestivo_desatencao": teste.sugestivo_desatencao,
            "sugestivo_hiperatividade": teste.sugestivo_hiperatividade,
        }
        registros.append({
            "id": teste.id,
            "tipo": "snap",
            "nome": INSTRUMENTOS["snap"]["nome"],
            "data_realizacao": teste.data_realizacao.isoformat() if teste.data_realizacao else None,
            "pontuacao_total": None,
            "pontuacao_maxima": INSTRUMENTOS["snap"]["maximo"],
            "pontos_desatencao": teste.pontos_desatencao,
            "pontos_hiperatividade": teste.pontos_hiperatividade,
            "nivel": _snap_nivel_code(resultados),
            "nivel_label": _snap_nivel_label(resultados),
        })

    registros.sort(key=lambda r: r["data_realizacao"] or "", reverse=True)
    return registros


def _validar_respostas(inst, data):
    respostas = {}
    for campo in _campos(inst):
        valor = data.get(campo)
        if type(valor) is not int or valor < 0 or valor > 3:
            return None, f"Campo {campo} é obrigatório e deve ser um inteiro entre 0 e 3"
        respostas[campo] = valor
    return respostas, None


def _criar_evolucao(paciente, teste, nome, pontuacao, nivel):
    data_formatada = teste.data_realizacao.strftime('%d/%m/%Y')
    texto = (
        f"TESTE {nome} REALIZADO EM {data_formatada}\n"
        f"Pontuação Total: {pontuacao}\n"
        f"Nível: {_nivel_label(nivel)}\n"
        f"Observações: {teste.observacoes}"
    )
    db.session.add(Evolucao(
        paciente_id=paciente.id,
        profissional_id=paciente.profissional_responsavel_id,
        associacao_id=paciente.associacao_id,
        data_evolucao=teste.data_realizacao,
        nota_evolucao=texto,
    ))


def _criar_evolucao_snap(paciente, teste, resultados):
    data_formatada = teste.data_realizacao.strftime('%d/%m/%Y')
    if resultados['tdah_positivo']:
        if resultados['sugestivo_desatencao'] and resultados['sugestivo_hiperatividade']:
            conclusao = "Resultado sugere apresentacao COMBINADA de TDAH."
        elif resultados['sugestivo_desatencao']:
            conclusao = "Resultado sugere apresentacao PREDOMINANTEMENTE DESATENTA de TDAH."
        else:
            conclusao = "Resultado sugere apresentacao PREDOMINANTEMENTE HIPERATIVA/IMPULSIVA de TDAH."
    else:
        conclusao = "Resultado NAO sugere TDAH com base nos criterios do SNAP-IV."
    texto = (
        f"TESTE {INSTRUMENTOS['snap']['nome']} REALIZADO EM {data_formatada}\n"
        f"Pontos Desatencao: {teste.pontos_desatencao}/9\n"
        f"Pontos Hiperatividade: {teste.pontos_hiperatividade}/9\n"
        f"Conclusao: {conclusao}\n"
        f"Observacoes: {teste.observacoes}"
    )
    db.session.add(Evolucao(
        paciente_id=paciente.id,
        profissional_id=paciente.profissional_responsavel_id,
        associacao_id=paciente.associacao_id,
        data_evolucao=teste.data_realizacao,
        nota_evolucao=texto,
    ))


def _alertar_risco(paciente, tipo, teste, nivel):
    """Alerta o profissional quando um rastreio indica risco (ideação suicida).

    Chamado uma única vez por POST, após o commit da resposta do paciente.
    Nunca deve quebrar o fluxo do paciente: tudo fica sob try/except amplo.
    """
    try:
        if tipo == "phq9":
            if not getattr(teste, "risco_suicida", False):
                return
            escala = INSTRUMENTOS["phq9"]["nome"]
            destaque = (
                "Resposta positiva no item 9 do PHQ-9 "
                "(pensamentos de morte ou de se ferir)."
            )
        elif tipo == "beck":
            item9 = getattr(teste, "item_9", 0) or 0
            if item9 < 1:
                return
            escala = INSTRUMENTOS["beck"]["nome"]
            destaque = (
                "Resposta positiva no item 9 do Beck (BDI-II) "
                "(pensamentos suicidas)."
            )
        else:
            return

        destino = os.environ.get("ALERTA_RASTREIO_EMAIL")
        if not destino:
            prof = getattr(paciente, "profissional_responsavel", None)
            destino = getattr(prof, "email", None) if prof else None

        if not destino:
            logger.warning(
                "Alerta de risco (%s/%s): nenhum destinatario configurado "
                "(ALERTA_RASTREIO_EMAIL vazio e profissional sem email).",
                tipo, paciente.id,
            )
            return

        pontuacao = getattr(teste, "pontuacao_total", None)
        if getattr(teste, "data_realizacao", None):
            data_hora = teste.data_realizacao.strftime("%d/%m/%Y %H:%M")
        else:
            data_hora = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        telefone = paciente.telefone or "nao informado"

        assunto = f"ALERTA: rastreio positivo para risco - {paciente.nome}"
        html_body = (
            "<h2 style='color:#a11'>Alerta de risco em rastreio</h2>"
            f"<p><strong>Paciente:</strong> {paciente.nome}</p>"
            f"<p><strong>Escala:</strong> {escala}</p>"
            f"<p><strong>Pontuacao:</strong> {pontuacao}</p>"
            f"<p><strong>Nivel:</strong> {_nivel_label(nivel)}</p>"
            f"<p><strong>Telefone do paciente:</strong> {telefone}</p>"
            f"<p><strong>Data/hora:</strong> {data_hora}</p>"
            f"<p style='color:#a11'><strong>ATENCAO:</strong> {destaque}</p>"
        )
        text_body = (
            f"ALERTA DE RISCO - {paciente.nome}\n"
            f"Escala: {escala}\n"
            f"Pontuacao: {pontuacao}\n"
            f"Nivel: {_nivel_label(nivel)}\n"
            f"Telefone: {telefone}\n"
            f"Data/hora: {data_hora}\n\n"
            f"ATENCAO: {destaque}\n"
        )

        try:
            from services.email_service import EmailService
            email_service = EmailService()
            enviado = email_service.send_email(destino, assunto, html_body, text_body)
            if getattr(email_service, "development_mode", False):
                logger.warning(
                    "Alerta de risco: EmailService em modo desenvolvimento; "
                    "email NAO foi entregue de fato (destino=%s).", destino,
                )
            elif enviado:
                logger.info("Alerta de risco enviado por email para %s", destino)
            else:
                logger.warning(
                    "Alerta de risco: falha ao enviar email (destino=%s).", destino,
                )
        except Exception:
            logger.exception("Falha ao enviar alerta de risco por email")

        telefone_admin = os.environ.get("WHATSAPP_ADMIN_PHONE")
        if telefone_admin:
            try:
                from services.whatsapp_service import WhatsAppService
                WhatsAppService().send_message(telefone_admin, text_body)
            except Exception:
                logger.exception("Falha ao enviar alerta de risco por WhatsApp")
    except Exception:
        logger.exception("Erro inesperado ao processar alerta de risco de rastreio")


@patient_rastreios_bp.route('/me/rastreios', methods=['GET'])
@jwt_required()
def listar_rastreios():
    """Catálogo dos instrumentos autoaplicáveis + histórico do paciente logado."""
    error = require_patient()
    if error:
        return error

    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    catalogo = [
        {
            "chave": chave,
            "nome": inst["nome"],
            "descricao": inst["descricao"],
            "n_itens": len(_campos(inst)),
            "opcoes": inst["opcoes"],
            "pontuacao_maxima": inst["maximo"],
            "publico": inst.get("publico", "paciente"),
            "somente_menor": bool(inst.get("somente_menor", False)),
            "aviso": inst.get("aviso"),
        }
        for chave, inst in INSTRUMENTOS.items()
        if _instrumento_disponivel(chave, paciente)
    ]

    return jsonify({
        'catalogo': catalogo,
        'historico': _historico(paciente.id),
    }), 200


@patient_rastreios_bp.route('/me/rastreios/<tipo>', methods=['GET'])
@jwt_required()
def obter_rastreio(tipo):
    """Perguntas e opções de resposta do instrumento solicitado."""
    error = require_patient()
    if error:
        return error

    if tipo not in INSTRUMENTOS:
        return jsonify({'error': 'Tipo de rastreio desconhecido'}), 400

    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if tipo == "snap":
        bloqueio = _bloqueio_snap(paciente)
        if bloqueio:
            return bloqueio

    return jsonify(_instrumento_publico(tipo)), 200


@patient_rastreios_bp.route('/me/rastreios/<tipo>', methods=['POST'])
@jwt_required()
def responder_rastreio(tipo):
    """Recebe e grava as respostas do próprio paciente autenticado."""
    error = require_patient()
    if error:
        return error

    if tipo not in INSTRUMENTOS:
        return jsonify({'error': 'Tipo de rastreio desconhecido'}), 400

    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if tipo == "snap":
        bloqueio = _bloqueio_snap(paciente)
        if bloqueio:
            return bloqueio

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Payload inválido'}), 400

    inst = INSTRUMENTOS[tipo]
    respostas, erro = _validar_respostas(inst, data)
    if erro:
        return jsonify({'error': erro}), 400

    profissional_id = paciente.profissional_responsavel_id

    try:
        if tipo == "phq9":
            teste = PHQ9Teste(
                paciente_id=paciente.id,
                profissional_id=profissional_id,
                observacoes=_ORIGEM,
                **respostas,
            )
            resultados = teste.calcular_resultados()
            teste.pontuacao_total = resultados['pontuacao_total']
            teste.nivel_depressao = resultados['nivel_depressao']
            teste.depressao_positiva = resultados['depressao_positiva']
            teste.risco_suicida = resultados['risco_suicida']
            nivel = resultados['nivel_depressao']

        elif tipo == "gad7":
            teste = GAD7Teste(
                paciente_id=paciente.id,
                profissional_id=profissional_id,
                observacoes=_ORIGEM,
                **respostas,
            )
            resultados = teste.calcular_resultados()
            teste.pontuacao_total = resultados['pontuacao_total']
            teste.nivel_ansiedade = resultados['nivel_ansiedade']
            teste.ansiedade_positiva = resultados['ansiedade_positiva']
            nivel = resultados['nivel_ansiedade']

        elif tipo == "snap":
            teste = SnapIVTeste(
                paciente_id=paciente.id,
                profissional_id=paciente.profissional_responsavel_id,
                observacoes=_ORIGEM_SNAP,
                **respostas,
            )
            resultados = teste.calcular_resultados()
            teste.pontos_desatencao = resultados['pontos_desatencao']
            teste.pontos_hiperatividade = resultados['pontos_hiperatividade']
            teste.sugestivo_desatencao = resultados['sugestivo_desatencao']
            teste.sugestivo_hiperatividade = resultados['sugestivo_hiperatividade']
            teste.tdah_positivo = resultados['tdah_positivo']
            nivel = _snap_nivel_code(resultados)

        else:
            teste = BeckDepressionTeste(
                paciente_id=paciente.id,
                profissional_id=profissional_id,
                observacoes=_ORIGEM,
                **respostas,
            )
            resultados = teste.calcular_resultados()
            teste.pontuacao_total = resultados['pontuacao_total']
            teste.nivel_depressao = resultados['nivel_depressao']
            teste.depressao_positiva = resultados['depressao_positiva']
            nivel = resultados['nivel_depressao']

        db.session.add(teste)

        if tipo in ("phq9", "beck") and resultados['depressao_positiva']:
            paciente.depressao_positiva = True

        if tipo == "snap" and resultados['tdah_positivo']:
            paciente.tdah_positivo = True

        db.session.flush()

        if tipo == "snap":
            _criar_evolucao_snap(paciente, teste, resultados)
        else:
            _criar_evolucao(
                paciente, teste, inst["nome"], teste.pontuacao_total, nivel
            )

        db.session.commit()

        if tipo == "snap":
            resultado = {
                'pontos_desatencao': teste.pontos_desatencao,
                'pontos_hiperatividade': teste.pontos_hiperatividade,
                'pontuacao_maxima': inst["maximo"],
                'nivel': nivel,
                'nivel_label': _snap_nivel_label(resultados),
                'tdah_positivo': teste.tdah_positivo,
            }
        else:
            resultado = {
                'pontuacao_total': teste.pontuacao_total,
                'pontuacao_maxima': inst["maximo"],
                'nivel': nivel,
                'nivel_label': _nivel_label(nivel),
            }

        _alertar_risco(paciente, tipo, teste, nivel)

        return jsonify({
            'message': 'Rastreio registrado com sucesso',
            'teste': teste.to_dict(),
            'resultado': resultado,
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao registrar rastreio: {str(e)}'}), 500
