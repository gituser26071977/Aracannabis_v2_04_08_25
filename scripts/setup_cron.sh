#!/usr/bin/env bash
# Cron entries for production
# Adicionar via: ./scripts/setup_cron.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Backup diário 03:00 UTC
# Healthcheck a cada 5min
# Rotação de logs semanal

(crontab -l 2>/dev/null || true; cat <<EOF
# AraOS
0 3 * * *  $SCRIPT_DIR/backup.sh --env=production >> /var/log/siap/backup.log 2>&1
*/5 * * * * $SCRIPT_DIR/healthcheck.sh --env=production >> /var/log/siap/healthcheck.log 2>&1
0 4 * * 0  find /var/log/siap -name "*.log" -mtime +30 -delete
EOF
) | crontab -

echo "✓ Cron instalado"
crontab -l
