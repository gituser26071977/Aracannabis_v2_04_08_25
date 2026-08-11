#!/usr/bin/env python3
"""Replay histórico do SIAP → AraOS (F2 retrofit) — CLI.

Dispara o replay das anamneses/evoluções históricas para o AraOS,
bootstrap do genome com histórico.

Uso (dentro do container do SIAP no VPS):
    python scripts/replay_historical.py [--limit N] [--dry-run]

Saída: JSON com total / emitted / failed / errors.
"""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay histórico SIAP → AraOS")
    parser.add_argument("--limit", type=int, default=None, help="Limite de registros")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Não emite eventos; apenas contabiliza (emitted fica 0)",
    )
    args = parser.parse_args()

    # Garante app context do Flask (usado por db.session)
    from app_cors_livre import create_app

    app = create_app()
    with app.app_context():
        from models import db
        from services.historical_replay import HistoricalReplayService

        replay = HistoricalReplayService(db.session)
        result = replay.run(limit=args.limit)

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        print(f"⚠️  {result.failed} falhas — ver logs", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
