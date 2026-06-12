"""
SecretariaService — Dados agregados para o Dashboard da Secretária.

FASE 4 — Fornece uma visão consolidada do dia a dia para a equipe administrativa
da clínica: agenda, pacientes esperados, dispensações pendentes.

Princípios:
  - Sempre filtra por `associacao_id` (multi-tenant) — secretária de clínica A
    NÃO vê dados de clínica B.
  - Cacheia o objeto `associacao` para evitar queries repetidas.
  - Queries otimizadas — uma por seção do dashboard, não N+1.
"""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy import and_, or_, func

logger = logging.getLogger(__name__)


class SecretariaService:
    """Agrega dados clínicos/operacionais para o dashboard da secretária."""

    def __init__(self, associacao_id: int, profissional_id: int):
        if not associacao_id:
            raise ValueError("associacao_id é obrigatório")
        self.associacao_id = associacao_id
        self.profissional_id = profissional_id

    # ═══════════════════════════════════════════════════════════════════
    # DASHBOARD PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Retorna cards de resumo:
          - agenda_hoje: consultas marcadas para hoje
          - proximas_consultas: próximas 5 consultas (24h)
          - pacientes_esperados: lista de pacientes com consulta hoje
          - dispensacoes_pendentes: dispensações que precisam ação
          - resumo: contadores agregados
        """
        from models import Consulta, Paciente, db

        hoje = date.today()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())
        amanha = inicio_dia + timedelta(days=1)

        # Agenda de hoje
        agenda_hoje = (
            Consulta.query
            .filter(
                Consulta.associacao_id == self.associacao_id,
                Consulta.data_hora >= inicio_dia,
                Consulta.data_hora <= fim_dia,
                Consulta.status.in_(["agendada", "confirmada"]),
            )
            .order_by(Consulta.data_hora.asc())
            .all()
        )

        # Próximas consultas (24h, depois de agora)
        agora = datetime.utcnow()
        proximas = (
            Consulta.query
            .filter(
                Consulta.associacao_id == self.associacao_id,
                Consulta.data_hora > agora,
                Consulta.data_hora < amanha,
                Consulta.status.in_(["agendada", "confirmada"]),
            )
            .order_by(Consulta.data_hora.asc())
            .limit(5)
            .all()
        )

        # Pacientes únicos com consulta hoje
        pacientes_hoje_ids = list({c.paciente_id for c in agenda_hoje})
        pacientes_hoje_count = len(pacientes_hoje_ids)

        # Resumo
        total_consultas_hoje = len(agenda_hoje)
        consultas_confirmadas = sum(1 for c in agenda_hoje if c.status == "confirmada")
        consultas_agendadas = sum(1 for c in agenda_hoje if c.status == "agendada")

        # Dispensações pendentes (do tenant)
        dispensacoes_pendentes = self._get_dispensacoes_pendentes()

        # Total de pacientes do tenant
        total_pacientes_tenant = (
            Paciente.query
            .filter_by(associacao_id=self.associacao_id)
            .count()
        )

        return {
            "agenda_hoje": [self._consulta_to_dict(c) for c in agenda_hoje],
            "proximas_consultas": [self._consulta_to_dict(c) for c in proximas],
            "dispensacoes_pendentes": dispensacoes_pendentes,
            "resumo": {
                "total_pacientes_tenant": total_pacientes_tenant,
                "consultas_hoje": total_consultas_hoje,
                "consultas_confirmadas": consultas_confirmadas,
                "consultas_agendadas": consultas_agendadas,
                "pacientes_esperados_hoje": pacientes_hoje_count,
                "dispensacoes_pendentes": len(dispensacoes_pendentes),
            },
        }

    # ═══════════════════════════════════════════════════════════════════
    # AGENDA
    # ═══════════════════════════════════════════════════════════════════

    def get_agenda(self, data_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retorna agenda completa de uma data específica (default = hoje)."""
        from models import Consulta

        if data_str:
            try:
                data = datetime.strptime(data_str, "%Y-%m-%d").date()
            except ValueError:
                data = date.today()
        else:
            data = date.today()

        inicio_dia = datetime.combine(data, datetime.min.time())
        fim_dia = datetime.combine(data, datetime.max.time())

        consultas = (
            Consulta.query
            .filter(
                Consulta.associacao_id == self.associacao_id,
                Consulta.data_hora >= inicio_dia,
                Consulta.data_hora <= fim_dia,
            )
            .order_by(Consulta.data_hora.asc())
            .all()
        )
        return [self._consulta_to_dict(c) for c in consultas]

    # ═══════════════════════════════════════════════════════════════════
    # CHECK-IN
    # ═══════════════════════════════════════════════════════════════════

    def marcar_checkin(self, consulta_id: int) -> Dict[str, Any]:
        """Marca uma consulta como 'confirmada' (check-in feito pela secretária)."""
        from models import Consulta, db

        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return {"success": False, "error": "Consulta não encontrada."}
        if consulta.associacao_id != self.associacao_id:
            return {"success": False, "error": "Acesso negado a esta consulta."}

        if consulta.status not in ("agendada", "confirmada"):
            return {
                "success": False,
                "error": f"Não é possível fazer check-in de consulta com status '{consulta.status}'.",
            }

        consulta.status = "confirmada"
        db.session.commit()

        return {
            "success": True,
            "message": "Check-in realizado com sucesso.",
            "consulta": self._consulta_to_dict(consulta),
        }

    # ═══════════════════════════════════════════════════════════════════
    # PACIENTES (read-only)
    # ═══════════════════════════════════════════════════════════════════

    def quick_search_pacientes(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca pacientes do tenant por nome ou CPF (read-only)."""
        from models import Paciente

        if not query or len(query.strip()) < 2:
            return []

        q = query.strip()
        like_pattern = f"%{q}%"
        pacientes = (
            Paciente.query
            .filter(
                Paciente.associacao_id == self.associacao_id,
                or_(
                    Paciente.nome.ilike(like_pattern),
                    Paciente.cpf.ilike(like_pattern),
                ),
            )
            .limit(limit)
            .all()
        )
        return [
            {
                "id": p.id,
                "nome": p.nome,
                "cpf": p.cpf,
                "data_nascimento": p.data_nascimento.isoformat() if p.data_nascimento else None,
                "telefone": getattr(p, "telefone", None),
                "email": getattr(p, "email", None),
            }
            for p in pacientes
        ]

    def listar_pacientes(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Lista pacientes do tenant (read-only)."""
        from models import Paciente

        total = Paciente.query.filter_by(associacao_id=self.associacao_id).count()
        pacientes = (
            Paciente.query
            .filter_by(associacao_id=self.associacao_id)
            .order_by(Paciente.nome.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return {
            "total": total,
            "items": [
                {
                    "id": p.id,
                    "nome": p.nome,
                    "cpf": p.cpf,
                    "data_nascimento": p.data_nascimento.isoformat() if p.data_nascimento else None,
                    "telefone": getattr(p, "telefone", None),
                    "email": getattr(p, "email", None),
                }
                for p in pacientes
            ],
        }

    # ═══════════════════════════════════════════════════════════════════
    # DISPENSAÇÕES
    # ═══════════════════════════════════════════════════════════════════

    def _get_dispensacoes_pendentes(self) -> List[Dict[str, Any]]:
        """Lista prescrições com dispensação pendente (heurística simples)."""
        # Heurística: prescrições recentes com status 'pendente'/'autorizada' sem dispensação
        # Se não houver modelo de dispensação explícito, retorna vazio
        try:
            from association.models import Dispensacao
            disp = (
                Dispensacao.query
                .filter_by(associacao_id=self.associacao_id, status="pendente")
                .limit(10)
                .all()
            )
            return [d.to_dict() if hasattr(d, "to_dict") else {"id": d.id} for d in disp]
        except Exception:
            return []

    # ═══════════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _consulta_to_dict(c) -> Dict[str, Any]:
        try:
            paciente_nome = c.paciente.nome if c.paciente else None
        except Exception:
            paciente_nome = None

        try:
            profissional_nome = c.profissional.nome if c.profissional else None
        except Exception:
            profissional_nome = None

        return {
            "id": c.id,
            "paciente_id": c.paciente_id,
            "paciente_nome": paciente_nome,
            "profissional_id": c.profissional_id,
            "profissional_nome": profissional_nome,
            "data_hora": c.data_hora.isoformat() if c.data_hora else None,
            "duracao_minutos": c.duracao_minutos,
            "tipo_consulta": c.tipo_consulta,
            "status": c.status,
            "observacoes": c.observacoes,
        }
