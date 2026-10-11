#!/usr/bin/env bash
# Runs everything on one Fly machine, like `h4h dev` without reloads. Caddy on :8080 is the only
# public port. /data is the volume: signing keys, media and the linked WhatsApp session.
set -euo pipefail
cd /app

export PUBLIC_URL="https://${FLY_APP_NAME}.fly.dev"
export CORE_PUBLIC_URL="$PUBLIC_URL" KEYS_DIR=/data/keys MEDIA_DIR=/data/media MODULES_CONFIG=/app/modules.fly.toml
mkdir -p /data/keys /data/media /data/wa-auth
ln -sfn /data/wa-auth clients/wa/auth
sed "s|PUBLIC_URL|$PUBLIC_URL|g" deploy/modules.toml > "$MODULES_CONFIG"

.venv/bin/h4h init  # keys on the volume the first time; tokens into each service's .env on every boot
.venv/bin/alembic upgrade head

.venv/bin/uvicorn core.app:app --port 8000 &
(cd modules/moph && exec .venv/bin/uvicorn app.main:app --port 8002) &
(cd modules/requests && exec .venv/bin/uvicorn app.main:app --port 8003) &
(cd modules/bills && exec .venv/bin/uvicorn app.main:app --port 8004) &
(cd clients/web && exec .venv/bin/uvicorn app.main:app --timeout-graceful-shutdown 1 --port 9000) &
(cd clients/wa && PORT=9001 exec node main.js) &
caddy run --config deploy/Caddyfile --adapter caddyfile &

wait -n  # one service died: stop, so Fly restarts the machine
exit 1
