"""Rastreios autoaplicáveis de adulto no Portal do Paciente.

PHQ-9, GAD-7 e Beck (BDI-II) respondidos pelo próprio paciente autenticado.
Os textos dos itens e das opções são copiados literalmente dos componentes
frontend/src/components/{PHQ9Test,GAD7Test,BeckDepressionTest}.js.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Paciente, PHQ9Teste, GAD7Teste, BeckDepressionTeste, Evolucao
from routes.patient_portal import require_patient

patient_rastreios_bp = Blueprint('patient_rastreios', __name__)

_ORIGEM = "Preenchido pelo paciente no portal"

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

INSTRUMENTOS = {
    "phq9": {
        "chave": "phq9",
        "nome": "PHQ-9 — Questionário de Saúde do Paciente",
        "descricao": "Rastreio de sintomas depressivos nas últimas duas semanas.",
        "instrucoes": "Nas últimas duas semanas, com que frequência você foi incomodado por:",
        "prefixo": "q",
        "perguntas": _PERGUNTAS_PHQ9,
        "opcoes": _OPCOES_PHQ9,
        "maximo": 27,
    },
    "gad7": {
        "chave": "gad7",
        "nome": "GAD-7 — Transtorno de Ansiedade Generalizada",
        "descricao": "Rastreio de sintomas ansiosos nas últimas duas semanas.",
        "instrucoes": "Nas últimas 2 semanas, com que frequência você foi incomodado(a) pelos problemas abaixo?",
        "prefixo": "q",
        "perguntas": _PERGUNTAS_GAD7,
        "opcoes": _OPCOES_GAD7,
        "maximo": 21,
    },
    "beck": {
        "chave": "beck",
        "nome": "Inventário de Depressão de Beck (BDI-II)",
        "descricao": "Rastreio de sintomas depressivos na última semana.",
        "instrucoes": "Avalie cada afirmação de acordo com como você se sentiu na última semana, incluindo hoje.",
        "prefixo": "item_",
        "perguntas": _PERGUNTAS_BECK,
        "opcoes": _OPCOES_BECK,
        "maximo": 63,
    },
}

_NIVEL_LABEL = {
    "minima": "Mínima",
    "leve": "Leve",
    "moderada": "Moderada",
    "moderadamente_grave": "Moderadamente grave",
    "grave": "Grave",
}


def _instrumento_publico(chave):
    inst = INSTRUMENTOS[chave]
    perguntas = [
        {"campo": f"{inst['prefixo']}{i}", "numero": i, "texto": texto}
        for i, texto in enumerate(inst["perguntas"], start=1)
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
    }


def _nivel_label(nivel):
    return _NIVEL_LABEL.get(nivel, nivel or "")


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

    registros.sort(key=lambda r: r["data_realizacao"] or "", reverse=True)
    return registros


def _validar_respostas(inst, data):
    respostas = {}
    for i in range(1, len(inst["perguntas"]) + 1):
        campo = f"{inst['prefixo']}{i}"
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
            "n_itens": len(inst["perguntas"]),
            "opcoes": inst["opcoes"],
            "pontuacao_maxima": inst["maximo"],
        }
        for chave, inst in INSTRUMENTOS.items()
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

        db.session.flush()

        _criar_evolucao(
            paciente, teste, inst["nome"], teste.pontuacao_total, nivel
        )

        db.session.commit()

        return jsonify({
            'message': 'Rastreio registrado com sucesso',
            'teste': teste.to_dict(),
            'resultado': {
                'pontuacao_total': teste.pontuacao_total,
                'pontuacao_maxima': inst["maximo"],
                'nivel': nivel,
                'nivel_label': _nivel_label(nivel),
            },
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao registrar rastreio: {str(e)}'}), 500
