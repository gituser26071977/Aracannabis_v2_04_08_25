#!/bin/bash
set -e

# Esperar DB
echo "Waiting for postgres..."
while ! pg_isready -h siap-db -p 5432 -U siap_user; do
  sleep 1
done

echo "Running DB init/upgrade..."
# Se houver migrações, rode. Se não, create_all
if [ -d "migrations" ]; then
  flask db upgrade
else
  python tools/init_db.py || echo "DB init tool failed"
  # Depois, apply_sql SaaS...
  python tools/apply_sql.py saas_v1_init.sql || echo "SaaS Migration skipped or applied"
fi

echo "Starting App..."
exec python app_cors_livre.py --port 3000
