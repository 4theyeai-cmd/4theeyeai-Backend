#!/bin/sh
set -e

echo "[entrypoint] Python: $(python --version)"
if command -v ffmpeg >/dev/null 2>&1; then
  echo "[entrypoint] ffmpeg: $(ffmpeg -version | head -n1)"
else
  echo "[entrypoint] ffmpeg not found" >&2
fi

echo "[entrypoint] Working dir: $(pwd)"
echo "[entrypoint] Listening on port: ${PORT:-4000}"

# Show key environment variables if present (mask secrets)
mask() { echo "$1" | sed -e 's/./*/g'; }
[ -n "$DATABASE_URL" ] && echo "[entrypoint] DATABASE_URL set"

# Strict DB connectivity check (only DATABASE_URL)
python - <<'PY'
import os
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('[entrypoint] ERROR: DATABASE_URL not set, cannot connect to DB')
else:
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('[entrypoint] Database connectivity: OK')
    except Exception as e:
        print(f'[entrypoint] Database connectivity: FAILED -> {e}')
PY

# Start the server
exec uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-4000}
