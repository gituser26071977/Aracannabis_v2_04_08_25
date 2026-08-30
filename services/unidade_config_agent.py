"""Agente de configuração de unidade física — conversacional com IA.

Fluxo:
  1. Agente pergunta sobre a clínica (nome, tipo, endereço)
  2. Pergunta sobre a estrutura (andares, salas, banheiros, consultórios)
  3. Salva os dados nas models UnidadeFisica, AndarSetor, SalaAmbiente
  4. Integra com VSF
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from models import db
from models_extra import UnidadeFisica, AndarSetor, SalaAmbiente

logger = logging.getLogger(__name__)

# Estados do fluxo conversacional
STATE_INICIO = "inicio"
STATE_NOME = "nome"
STATE_TIPO = "tipo"
STATE_ENDERECO = "endereco"
STATE_ANDARES = "andares"
STATE_SALAS = "salas"
STATE_REVISAO = "revisao"
STATE_CONCLUIDO = "concluido"

LABEL_TIPO = {
    "clinica": "Clínica",
    "consultorio": "Consultório",
    "hospital": "Hospital",
    "home_care": "Home Care",
}

LABEL_ESPACO = {
    "consultorio": "Consultório",
    "sala_espera": "Sala de Espera",
    "infusao": "Sala de Infusão",
    "procedimento": "Procedimento/Exames",
    "banheiro": "Banheiro",
    "terapia": "Sala de Terapia",
    "pre_atendimento": "Pré-atendimento",
    "recepcao": "Recepção",
    "triagem": "Triagem",
    "outro": "Outro",
}


class UnidadeConfigAgent:
    """Agente conversacional para configurar a unidade física"""

    def __init__(self, associacao_id: int, profissional_id: int):
        self.associacao_id = associacao_id
        self.profissional_id = profissional_id
        self.state = STATE_INICIO
        self.dados: Dict[str, Any] = {
            "nome": None,
            "tipo": "clinica",
            "endereco": None,
            "cidade": None,
            "uf": None,
            "andares": [],
            "espacos": [],
        }
        self.unidade_id: Optional[int] = None

    def processar(self, mensagem: str) -> Dict[str, Any]:
        """Processa mensagem do usuário e retorna resposta do agente."""
        msg = mensagem.strip().lower()

        if self.state == STATE_INICIO:
            return self._inicio(msg)
        elif self.state == STATE_NOME:
            return self._perguntar_nome(msg)
        elif self.state == STATE_TIPO:
            return self._perguntar_tipo(msg)
        elif self.state == STATE_ENDERECO:
            return self._perguntar_endereco(msg)
        elif self.state == STATE_ANDARES:
            return self._perguntar_andares(msg)
        elif self.state == STATE_SALAS:
            return self._perguntar_salas(msg)
        elif self.state == STATE_REVISAO:
            return self._revisar(msg)
        elif self.state == STATE_CONCLUIDO:
            return self._concluido(msg)
        return {"resposta": "Não entendi. Vamos começar de novo?", "state": STATE_INICIO}

    def _inicio(self, msg: str) -> Dict[str, Any]:
        respostas = [
            "👋 Olá! Vou ajudar você a configurar a estrutura física da sua clínica.",
            "Isso é importante para o sistema VSF (Visão Computacional) e para organizar "
            "os espaços de atendimento.",
            "",
            "📝 **Qual o nome da sua clínica ou consultório?**",
        ]
        self.state = STATE_NOME
        return {"resposta": "\n".join(respostas), "state": self.state}

    def _perguntar_nome(self, msg: str) -> Dict[str, Any]:
        if len(msg) < 3:
            return {"resposta": "Por favor, digite um nome válido (mínimo 3 caracteres).", "state": self.state}

        self.dados["nome"] = mensagem_original(msg)
        self.state = STATE_TIPO

        respostas = [
            f"Ótimo! **{self.dados['nome']}** é um nome excelente! 🏥",
            "",
            "Qual o tipo da unidade?",
            "1️⃣ **Clínica** — Consultórios médicos",
            "2️⃣ **Consultório** — Atendimento individual",
            "3️⃣ **Hospital** — Estrutura hospitalar",
            "4️⃣ **Home Care** — Atendimento domiciliar",
            "",
            "Digite o número ou o nome do tipo:",
        ]
        return {"resposta": "\n".join(respostas), "state": self.state}

    def _perguntar_tipo(self, msg: str) -> Dict[str, Any]:
        tipo_map = {
            "1": "clinica", "clínica": "clinica", "clinica": "clinica",
            "2": "consultorio", "consultório": "consultorio", "consultorio": "consultorio",
            "3": "hospital", "hospital": "hospital",
            "4": "home_care", "home care": "home_care",
        }
        tipo = tipo_map.get(msg)
        if not tipo:
            return {"resposta": "Opção inválida. Digite 1 (Clínica), 2 (Consultório), 3 (Hospital) ou 4 (Home Care).", "state": self.state}

        self.dados["tipo"] = tipo
        self.state = STATE_ENDERECO
        return {
            "resposta": f"Tipo definido: **{LABEL_TIPO.get(tipo, tipo)}** ✅\n\n"
                       f"📍 Agora informe o **endereço completo** da unidade "
                       f"(rua, número, cidade, UF — ex: Rua das Flores, 123, São Paulo, SP):",
            "state": self.state,
        }

    def _perguntar_endereco(self, msg: str) -> Dict[str, Any]:
        self.dados["endereco"] = mensagem_original(msg)

        import re
        uf_match = re.search(r'\b([A-Za-z]{2})\b$', msg)
        if uf_match:
            self.dados["uf"] = uf_match.group(1).upper()

        self.state = STATE_ANDARES
        return {
            "resposta": f"Endereço salvo ✅\n\n"
                       f"📐 Agora vamos falar sobre a estrutura física.\n\n"
                       f"**Quantos andares/pavimentos tem a unidade?**\n"
                       f"(Digite um número, ex: 1, 2, 3... Se for térreo, digite 1)",
            "state": self.state,
        }

    def _perguntar_andares(self, msg: str) -> Dict[str, Any]:
        try:
            qtd = int(msg)
            if qtd < 1 or qtd > 50:
                return {"resposta": "Número inválido. Digite entre 1 e 50.", "state": self.state}
        except ValueError:
            return {"resposta": "Por favor, digite um número válido.", "state": self.state}

        self.dados["qtd_andares"] = qtd
        self.dados["andares"] = [f"Pavimento {i+1}" for i in range(qtd)]

        self.state = STATE_SALAS
        return {
            "resposta": f"{qtd} andar(es) ✅\n\n"
                       f"🪑 **Quais espaços/salas existem na unidade?**\n\n"
                       f"Digite os tipos separados por vírgula, ex:\n"
                       f"`consultorio, sala_espera, banheiro, recepcao, procedimento, infusao`\n\n"
                       f"Opções disponíveis: consultorio, sala_espera, infusao, procedimento, "
                       f"banheiro, terapia, pre_atendimento, recepcao, triagem, outro",
            "state": self.state,
        }

    def _perguntar_salas(self, msg: str) -> Dict[str, Any]:
        tipos_validos = set(LABEL_ESPACO.keys())
        itens = [s.strip() for s in msg.replace("e", ",").split(",")]
        espacos = []
        invalidos = []

        for item in itens:
            if item in tipos_validos:
                espacos.append(item)
            else:
                invalidos.append(item)

        if not espacos:
            return {
                "resposta": f"Nenhum tipo válido encontrado. Opções: {', '.join(sorted(tipos_validos))}",
                "state": self.state,
            }

        for espaco in espacos:
            qtd = self.dados["qtd_andares"]
            for andar_idx in range(qtd):
                for i in range(1, 3):
                    self.dados["espacos"].append({
                        "tipo": espaco,
                        "nome": f"{LABEL_ESPACO[espaco]} {i}",
                        "andar": f"Pavimento {andar_idx + 1}",
                        "capacidade": 1 if espaco in ("banheiro", "triagem") else
                                      4 if espaco == "sala_espera" else
                                      2 if espaco == "infusao" else 1,
                    })

        extras = ""
        if invalidos:
            extras = f"\n\n⚠️ Ignorados (não reconhecidos): {', '.join(invalidos)}"

        self.state = STATE_REVISAO
        return {
            "resposta": f"Espaços adicionados ✅\n\n"
                       f"{self._resumo_espacos()}{extras}\n\n"
                       f"---\n\n"
                       f"📋 **Resumo da configuração:**\n"
                       f"{self._resumo_completo()}\n\n"
                       f"---\n\n"
                       f"Tudo certo? Digite **sim** para salvar ou **não** para recomeçar.",
            "state": self.state,
        }

    def _resumo_espacos(self) -> str:
        from collections import Counter
        tipos = Counter(e["tipo"] for e in self.dados["espacos"])
        linhas = [f"  • {count}x {LABEL_ESPACO.get(t, t)}" for t, count in tipos.most_common()]
        return "\n".join(linhas)

    def _resumo_completo(self) -> str:
        return (
            f"🏥 **Nome:** {self.dados['nome']}\n"
            f"📌 **Tipo:** {LABEL_TIPO.get(self.dados['tipo'], self.dados['tipo'])}\n"
            f"📍 **Endereço:** {self.dados['endereco']}\n"
            f"📐 **Andares:** {self.dados.get('qtd_andares', 0)}\n"
            f"🪑 **Espaços:** {len(self.dados['espacos'])} salas"
        )

    def _revisar(self, msg: str) -> Dict[str, Any]:
        if msg in ("sim", "s", "yes", "pode salvar", "confirmar", "ok"):
            return self._salvar()
        elif msg in ("nao", "não", "n", "no", "recomeçar", "reiniciar"):
            self.dados = {
                "nome": None, "tipo": "clinica", "endereco": None,
                "cidade": None, "uf": None, "andares": [], "espacos": [],
            }
            self.state = STATE_INICIO
            return self._inicio("")
        else:
            return {
                "resposta": "Digite **sim** para salvar ou **não** para recomeçar.",
                "state": self.state,
            }

    def _salvar(self) -> Dict[str, Any]:
        try:
            unidade = UnidadeFisica(
                associacao_id=self.associacao_id,
                nome=self.dados["nome"],
                tipo=self.dados["tipo"],
                endereco=self.dados.get("endereco"),
                uf=self.dados.get("uf"),
            )
            db.session.add(unidade)
            db.session.flush()
            self.unidade_id = unidade.id

            for i, nome_andar in enumerate(self.dados.get("andares", [])):
                andar = AndarSetor(
                    associacao_id=self.associacao_id,
                    unidade_id=unidade.id,
                    nome=nome_andar,
                    tipo="andar",
                    ordem=i,
                )
                db.session.add(andar)
                db.session.flush()

                espacos_andar = [e for e in self.dados["espacos"] if e["andar"] == nome_andar]
                for esp in espacos_andar:
                    sala = SalaAmbiente(
                        associacao_id=self.associacao_id,
                        nome=esp["nome"],
                        tipo=esp["tipo"],
                        capacidade=esp.get("capacidade", 1),
                        andar=nome_andar,
                        unidade_id=unidade.id,
                        andar_setor_id=andar.id,
                        ativo=True,
                    )
                    db.session.add(sala)

            db.session.commit()
            self.state = STATE_CONCLUIDO

            return {
                "resposta": (
                    f"✅ **Unidade configurada com sucesso!**\n\n"
                    f"{self._resumo_completo()}\n\n"
                    f"ID da unidade: **{unidade.id}**\n\n"
                    f"Os dados já estão disponíveis para o sistema VSF e demais "
                    f"funcionalidades.\n\n"
                    f"Digite **ok** para finalizar ou **reconfigurar** para refazer."
                ),
                "state": self.state,
                "unidade_id": unidade.id,
                "dados": self.dados,
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar unidade: {e}")
            return {
                "resposta": f"❌ Erro ao salvar: {str(e)}. Tente novamente.",
                "state": STATE_REVISAO,
            }

    def _concluido(self, msg: str) -> Dict[str, Any]:
        if "reconfig" in msg or "refazer" in msg:
            self.__init__(self.associacao_id, self.profissional_id)
            return self._inicio("")
        return {
            "resposta": "Configuração concluída! ✅ Use o menu Admin > Configurar Unidade "
                       "a qualquer momento para revisar ou alterar.",
            "state": self.state,
        }


def mensagem_original(msg: str) -> str:
    """Retorna a mensagem original (capitalizada)"""
    return msg.strip().title()


def criar_ou_atualizar_unidade(associacao_id: int, dados: Dict) -> Dict:
    """Cria ou atualiza unidade física a partir de dados estruturados."""
    from models_extra import UnidadeFisica, AndarSetor, SalaAmbiente

    unidade = UnidadeFisica.query.filter_by(associacao_id=associacao_id).first()
    if not unidade:
        unidade = UnidadeFisica(associacao_id=associacao_id)
        db.session.add(unidade)

    unidade.nome = dados.get("nome", unidade.nome)
    unidade.tipo = dados.get("tipo", unidade.tipo)
    unidade.endereco = dados.get("endereco", unidade.endereco)
    unidade.cidade = dados.get("cidade", unidade.cidade)
    unidade.uf = dados.get("uf", unidade.uf)
    db.session.commit()
    return {"id": unidade.id, "message": "Unidade atualizada"}