#!/usr/bin/env bash
# Aplica (idempotente) as rotas de aracannabis.com.br no Traefik file provider.
#
# Uso:  sudo ./apply-traefik.sh
# Requer: python3 + PyYAML no host (Traefik recarrega o arquivo automaticamente).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPET="${TRAEFIK_SNIPPET:-$SCRIPT_DIR/traefik-aracannabis.yml}"
TARGET="${TRAEFIK_DYNAMIC:-/opt/traefik-dynamic.yml}"

if [[ ! -f "$TARGET" ]]; then
  echo "✗ $TARGET não existe" >&2
  exit 1
fi

cp "$TARGET" "$TARGET.bak.$(date +%Y%m%d_%H%M%S)"

python3 - "$TARGET" "$SNIPPET" <<'PY'
import sys, yaml

target_path, snippet_path = sys.argv[1], sys.argv[2]
target = yaml.safe_load(open(target_path)) or {}
snippet = yaml.safe_load(open(snippet_path)) or {}

t_http = target.setdefault("http", {})
s_http = snippet.get("http", {})
for section in ("routers", "services", "middlewares"):
    t_http.setdefault(section, {})
    t_http[section].update(s_http.get(section, {}))

yaml.safe_dump(target, open(target_path, "w"), sort_keys=False, allow_unicode=True)
print("✓ Traefik dynamic atualizado:", target_path)
PY

echo "✓ Rotas de aracannabis aplicadas (Traefik recarrega via watcher)."
