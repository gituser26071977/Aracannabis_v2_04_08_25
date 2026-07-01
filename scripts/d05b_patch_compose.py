#!/usr/bin/env python3
"""D05b — patch inline em docker-compose.prod.yml APOS git checkout rc.10.

rc.10 (7d3bed1) tem 'build:' para siap-backend e siap-frontend. Sem
'image:' no compose, docker-compose pull faz 'Skipped - No image to be
pulled' e o restart usa imagem local antiga. Este patch troca 'build:'
por 'image: GHCR' para os 2 servicos. E idempotente: se ja tem 'image:',
nao faz nada.

Uso: python3 scripts/d05b_patch_compose.py
"""
import re, pathlib, sys

p = pathlib.Path("docker-compose.prod.yml")
s = p.read_text()

changed = []

# siap-backend
backend_pat = re.compile(
    r"(  siap-backend:)\n    build:\n      context: \.\n      dockerfile: Dockerfile\.backend\n"
)
if backend_pat.search(s):
    s = backend_pat.sub(
        r"\1\n    image: ${GHCR_BACKEND_IMAGE:-ghcr.io/gituser26071977/siap-backend}:${IMAGE_TAG:-latest}\n",
        s,
    )
    changed.append("siap-backend")
else:
    print("  siap-backend: ja tem image: (ou padrao nao bate)")

# siap-frontend
frontend_pat = re.compile(
    r"(  siap-frontend:)\n    build:\n      context: \./frontend\n      dockerfile: Dockerfile\n      args:\n        REACT_APP_API_URL: https://api\.visualsmartflow\.com\.br\n        REACT_APP_WS_URL: wss://api\.visualsmartflow\.com\.br/ws\n"
)
if frontend_pat.search(s):
    s = frontend_pat.sub(
        r"\1\n    image: ${GHCR_FRONTEND_IMAGE:-ghcr.io/gituser26071977/siap-frontend}:${IMAGE_TAG:-latest}\n",
        s,
    )
    changed.append("siap-frontend")
else:
    print("  siap-frontend: ja tem image: (ou padrao nao bate)")

if changed:
    p.write_text(s)
    print(f"  patched: {', '.join(changed)}")
else:
    print("  nada para patchar")
