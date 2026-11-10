#!/usr/bin/env python3
"""Campanha de convite ao Portal do Paciente (WhatsApp).

Seleciona pacientes com CPF + WhatsApp, valida os números na Evolution API e
envia uma mensagem convite — respeitando consentimento e opt-out.

Uso:
    # Simulação (padrão): não envia nada, só mostra quem seria convidado
    python scripts/campanha_portal_paciente.py

    # Enviar de verdade (máx. 20 por execução, 30s entre mensagens)
    python scripts/campanha_portal_paciente.py --enviar

    # Apenas alguns pacientes e intervalo maior
    python scripts/campanha_portal_paciente.py --enviar --ids 9,24 --intervalo 60

    # Incluir quem ainda não tem consentimento explícito (serviço, não marketing)
    python scripts/campanha_portal_paciente.py --enviar --incluir-sem-consentimento

Segurança:
  * sem `--enviar` nada é disparado (dry-run);
  * se houver mais destinatários que `--limite`, aborta sem `--force`;
  * números inexistentes no WhatsApp são marcados e não recebem mensagem;
  * cada tentativa fica registrada em `patient_convites` (auditoria LGPD).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func  # noqa: E402

from app_cors_livre import create_app  # noqa: E402
from models import db, Paciente, PatientConvite  # noqa: E402
from services.whatsapp_service import WhatsAppService  # noqa: E402

PORTAL_URL = os.environ.get(
    "PORTAL_PACIENTE_URL", "https://api.aracannabis.com.br/paciente"
)

TEMPLATE_WHATSAPP = (
    "Olá, {primeiro_nome}! Aqui é do Instituto Vittalis. "
    "Seu Portal do Paciente está disponível: lá você consulta consultas, "
    "exames, documentos e receitas. Acesse: {link} — entre com seu CPF e "
    "receba um código no WhatsApp. Qualquer dúvida, fale com nossa equipe. "
    "Para não receber avisos, responda SAIR."
)


def primeiro_nome(nome: str) -> str:
    return (nome or "").strip().split(" ")[0] if (nome or "").strip() else "paciente"


def render_mensagem(nome: str, template: str = TEMPLATE_WHATSAPP) -> str:
    return template.format(primeiro_nome=primeiro_nome(nome), link=PORTAL_URL)


def selecionar_destinatarios(
    ids: list[int] | None = None,
    excluir_ids: list[int] | None = None,
    incluir_sem_consentimento: bool = False,
) -> list[Paciente]:
    """Pacientes elegíveis: ativos, com CPF e telefone, sem opt-out.

    Por padrão exige consentimento explícito (`aceita_comunicacao_whatsapp=True`).
    """
    q = (
        Paciente.query.filter(func.coalesce(Paciente.is_active, True).is_(True))
        .filter(func.coalesce(func.trim(Paciente.cpf), "") != "")
        .filter(func.coalesce(func.trim(Paciente.telefone), "") != "")
        .filter(Paciente.opt_out_em.is_(None))
        .filter(Paciente.aceita_comunicacao_whatsapp.isnot(False))
    )
    if not incluir_sem_consentimento:
        q = q.filter(Paciente.aceita_comunicacao_whatsapp.is_(True))
    if ids:
        q = q.filter(Paciente.id.in_(ids))
    if excluir_ids:
        q = q.filter(Paciente.id.notin_(excluir_ids))
    return q.order_by(Paciente.id).all()


def _sincronizar_dados(app) -> None:
    """Garante que o schema novo exista (idempotente) em ambientes já migrados."""
    from sqlalchemy import text

    with app.app_context():
        db.session.execute(text(
            "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS "
            "aceita_comunicacao_whatsapp BOOLEAN"
        ))
        db.session.execute(text(
            "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS opt_out_em TIMESTAMP"
        ))
        db.session.execute(text(
            "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS "
            "opt_out_motivo VARCHAR(255)"
        ))
        db.session.execute(text(
            "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS "
            "convite_portal_enviado_em TIMESTAMP"
        ))
        db.session.execute(text(
            """
            CREATE TABLE IF NOT EXISTS patient_convites (
                id SERIAL PRIMARY KEY,
                associacao_id INTEGER,
                paciente_id INTEGER NOT NULL,
                canal VARCHAR(20) NOT NULL DEFAULT 'whatsapp',
                template VARCHAR(40),
                status VARCHAR(20) NOT NULL DEFAULT 'pendente',
                provider_id VARCHAR(120),
                erro TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        ))
        db.session.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Convite ao Portal do Paciente")
    parser.add_argument("--enviar", action="store_true", help="envia de verdade")
    parser.add_argument("--ids", type=str, default="", help="IDs separados por vírgula")
    parser.add_argument("--excluir-ids", type=str, default="", help="IDs a excluir")
    parser.add_argument("--limite", type=int, default=20, help="máximo por execução")
    parser.add_argument("--intervalo", type=int, default=30, help="segundos entre envios")
    parser.add_argument(
        "--incluir-sem-consentimento",
        action="store_true",
        help="inclui pacientes sem consentimento explícito (comunicação de serviço)",
    )
    parser.add_argument("--force", action="store_true", help="ignora o limite")
    args = parser.parse_args()

    def _ids(valor: str) -> list[int] | None:
        itens = [p.strip() for p in (valor or "").split(",") if p.strip()]
        return [int(p) for p in itens] if itens else None

    app = create_app()
    _sincronizar_dados(app)

    with app.app_context():
        destinatarios = selecionar_destinatarios(
            ids=_ids(args.ids),
            excluir_ids=_ids(args.excluir_ids),
            incluir_sem_consentimento=args.incluir_sem_consentimento,
        )
        total = len(destinatarios)
        print(f"Elegíveis: {total}")
        for p in destinatarios:
            falta = "sem consentimento" if p.aceita_comunicacao_whatsapp is not True else "ok"
            print(f"  {p.id:>4}  {p.nome:<38} {p.telefone:<16} [{falta}]")

        if not args.enviar:
            print("\nDry-run: nada foi enviado. Use --enviar para disparar.")
            return 0

        if total == 0:
            print("Nada a enviar.")
            return 0
        if total > args.limite and not args.force:
            print(
                f"Abortado: {total} destinatários > limite {args.limite}. "
                "Use --limite/--force para prosseguir."
            )
            return 1

        svc = WhatsAppService()
        numeros = [p.telefone for p in destinatarios]
        checagem: dict = {}
        for i in range(0, len(numeros), 10):
            checagem.update(svc.check_numbers(numeros[i:i + 10]))

        enviados = erros = invalidos = 0
        for p in destinatarios:
            info = checagem.get(p.telefone) or {}
            if not info.get("exists"):
                invalidos += 1
                db.session.add(PatientConvite(
                    paciente_id=p.id, canal="whatsapp", template="convite_portal",
                    status="numero_invalido", erro="Número não existe no WhatsApp",
                ))
                print(f"  ! {p.id} {p.nome}: número inválido")
                continue

            mensagem = render_mensagem(p.nome)
            resultado = svc.send_text(p.telefone, mensagem)
            status = "enviado" if resultado.get("ok") else "erro"
            db.session.add(PatientConvite(
                paciente_id=p.id, canal="whatsapp", template="convite_portal",
                status=status, provider_id=resultado.get("provider_id"),
                erro=resultado.get("erro"),
            ))
            if resultado.get("ok"):
                enviados += 1
                p.convite_portal_enviado_em = datetime.utcnow()
                print(f"  ✓ {p.id} {p.nome}")
            else:
                erros += 1
                print(f"  ✗ {p.id} {p.nome}: {resultado.get('erro')}")
            db.session.commit()
            time.sleep(max(1, args.intervalo))

        print(
            f"\nResumo: {enviados} enviados, {invalidos} números inválidos, "
            f"{erros} erros (de {total})."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
