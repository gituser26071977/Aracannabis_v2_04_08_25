#!/usr/bin/env bash
# ================================================================
# AraOS — Healthcheck (Prometheus-style output)
# Coleta métricas locais: CPU, RAM, Disk, PG, Redis, Workers, RQ
# Saída em formato Prometheus textfile collector (Node Exporter compatible)
# Uso: ./scripts/healthcheck.sh [--env=staging|production]
# ================================================================
set -euo pipefail

ENV="production"
for arg in "$@"; do [[ "$arg" == --env=* ]] && ENV="${arg#*=}"; done

case "$ENV" in
  staging)
    DB_CONTAINER="siap-db-staging"
    REDIS_CONTAINER="siap-redis-staging"
    BACKEND_CONTAINER="siap-backend-staging"
    ;;
  production)
    DB_CONTAINER="siap-db"
    REDIS_CONTAINER="siap-redis"
    BACKEND_CONTAINER="siap-backend"
    ;;
esac

# Métricas em formato Prometheus exposition
METRICS=""

# CPU (1 - idle)
CPU_IDLE=$(top -bn1 | grep "Cpu(s)" | awk '{print $8}' 2>/dev/null || echo "0")
CPU_USED=$(awk "BEGIN {printf \"%.2f\", 100 - $CPU_IDLE}")
METRICS+="# HELP siap_cpu_used_percent CPU utilization\n"
METRICS+="# TYPE siap_cpu_used_percent gauge\n"
METRICS+="siap_cpu_used_percent{env=\"$ENV\"} $CPU_USED\n"

# RAM
MEM_TOTAL=$(free -m | awk 'NR==2{print $2}')
MEM_USED=$(free -m | awk 'NR==2{print $3}')
MEM_PCT=$(awk "BEGIN {printf \"%.2f\", $MEM_USED*100/$MEM_TOTAL}")
METRICS+="siap_memory_used_percent{env=\"$ENV\"} $MEM_PCT\n"

# Disk
DISK_PCT=$(df -P / | awk 'NR==2{print $5}' | tr -d '%')
METRICS+="siap_disk_used_percent{env=\"$ENV\"} $DISK_PCT\n"

# PG: conexões ativas
if docker ps -q -f name="$DB_CONTAINER" >/dev/null; then
  PG_ACTIVE=$(docker exec "$DB_CONTAINER" psql -U "${POSTGRES_USER:-siap_user}" -d "${POSTGRES_DB:-aracannabis}" -t -A -c "SELECT count(*) FROM pg_stat_activity WHERE state='active';" 2>/dev/null || echo "0")
  METRICS+="siap_pg_active_connections{env=\"$ENV\"} $PG_ACTIVE\n"
fi

# Redis: ping
if docker ps -q -f name="$REDIS_CONTAINER" >/dev/null; then
  if docker exec "$REDIS_CONTAINER" redis-cli ping 2>/dev/null | grep -q PONG; then
    METRICS+="siap_redis_up{env=\"$ENV\"} 1\n"
  else
    METRICS+="siap_redis_up{env=\"$ENV\"} 0\n"
  fi
fi

# Workers (gunicorn)
if docker ps -q -f name="$BACKEND_CONTAINER" >/dev/null; then
  WORKERS=$(docker exec "$BACKEND_CONTAINER" ps aux 2>/dev/null | grep -c "gunicorn" || echo "0")
  METRICS+="siap_gunicorn_workers{env=\"$ENV\"} $WORKERS\n"
fi

# Webhook queue (estimativa via logs)
WEBHOOK_QUEUE=$(docker logs "$BACKEND_CONTAINER" --since 5m 2>/dev/null | grep -c "queued webhook" || echo "0")
METRICS+="siap_webhook_queue_size{env=\"$ENV\"} $WEBHOOK_QUEUE\n"

# Saída em textfile collector (Node Exporter)
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
mkdir -p "$TEXTFILE_DIR"
echo -e "$METRICS" > "$TEXTFILE_DIR/siap_${ENV}.prom"

# Saída legível em stdout
echo "═══ HEALTHCHECK $ENV ═══"
echo "CPU:        ${CPU_USED}%"
echo "RAM:        ${MEM_PCT}%  (${MEM_USED}/${MEM_TOTAL} MB)"
echo "Disk:       ${DISK_PCT}%"
echo "PG active:  ${PG_ACTIVE:-N/A}"
echo "Redis up:   $(echo "$METRICS" | grep '^siap_redis_up' | awk '{print $2}')"
echo "Workers:    ${WORKERS:-N/A}"
echo "WH queue:   ${WEBHOOK_QUEUE}"
echo "══════════════════════"
