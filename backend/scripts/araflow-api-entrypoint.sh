#!/bin/sh
# AraFlow — API container entrypoint.
#
# Reads /app/COMMIT (written by the Dockerfile from $GIT_COMMIT) into
# the GIT_COMMIT env var if it is not already set. The /health endpoint
# surfaces this value verbatim.
#
# Runs as UID 1001 (non-root). Node refuses to bind to ports below 1024
# without --allow-privileged, which is fine because we expose 5005.
#
# Exit codes:
#   0  clean shutdown
#   1  exec failure (propagated from node)

set -eu

if [ -z "${GIT_COMMIT:-}" ] && [ -f /app/COMMIT ]; then
  GIT_COMMIT=$(cat /app/COMMIT | tr -d '\r\n')
  export GIT_COMMIT
fi

if [ -z "${BUILD_TIME:-}" ]; then
  BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
  export BUILD_TIME
fi

exec node /app/backend/dist/index.js