#!/bin/sh
set -euo pipefail

# Wait for Postgres before seeding
until python - <<'PY'
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

username = os.environ["DATABASE_USERNAME"]
password = os.environ["DATABASE_PASSWORD"]
host = os.environ["DATABASE_HOST"]
database = os.environ["DATABASE_NAME"]

engine = create_engine(f"postgresql+psycopg://{username}:{password}@{host}/{database}")
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except OperationalError:
    raise SystemExit(1)
PY
do
  echo "Database not ready, retrying..."
  sleep 2
done

echo "DB ready, running seed..."
python database/seed.py

# Enable request/worker logs to stdout so `docker compose logs` shows them.
: "${GUNICORN_CMD_ARGS:=--access-logfile - --error-logfile - --log-level info}"
export GUNICORN_CMD_ARGS

echo "Starting API..."
exec gunicorn -w 4 -k gthread -t 60 -b 0.0.0.0:8001 api.wsgi:app
