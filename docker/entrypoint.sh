#!/usr/bin/env bash
set -euo pipefail

wait_for_port() {
  local host="${1}"
  local port="${2}"
  local timeout="${3:-60}"

  python - <<PY
import os, socket, time, sys
host = ${host!r}
port = int(${port!r})
timeout = int(${timeout!r})
start = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"DB is reachable at {host}:{port}")
            sys.exit(0)
    except OSError:
        if time.time() - start > timeout:
            print(f"Timed out waiting for {host}:{port}")
            sys.exit(1)
        time.sleep(1)
PY
}

DB_HOST="${DB_HOST:-}"
DB_PORT="${DB_PORT:-5432}"

if [[ -n "${DB_HOST}" ]]; then
  echo "Waiting for DB ${DB_HOST}:${DB_PORT}..."
  wait_for_port "${DB_HOST}" "${DB_PORT}" 90
fi

echo "Running migrations..."
python manage.py migrate --noinput --settings=config.settings

echo "Collecting static..."
python manage.py collectstatic --noinput --settings=config.settings

exec "$@"

