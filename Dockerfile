# One image with every service; deploy/start.sh runs them. See fly.toml.

FROM node:22-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
COPY admin/package.json admin/
COPY sdk/ui/package.json sdk/ui/
COPY modules/moph/ui/package.json modules/moph/ui/
COPY modules/requests/ui/package.json modules/requests/ui/
COPY modules/bills/ui/package.json modules/bills/ui/
COPY modules/noop/ui/package.json modules/noop/ui/
COPY clients/wa/package.json clients/wa/
RUN npm ci
COPY admin admin
COPY sdk/ui sdk/ui
COPY modules/moph/ui modules/moph/ui
COPY modules/requests/ui modules/requests/ui
COPY modules/bills/ui modules/bills/ui
ARG VITE_SHELL_ORIGIN
RUN npm run build -w admin \
 && UI_BASE=/modules/moph/ui/ npm run build -w modules/moph/ui \
 && UI_BASE=/modules/requests/ui/ npm run build -w modules/requests/ui \
 && UI_BASE=/modules/bills/ui/ npm run build -w modules/bills/ui \
 && npm prune --omit=dev

FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=caddy:2 /usr/bin/caddy /usr/local/bin/caddy
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
ENV UV_FROZEN=1 UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
WORKDIR /app
COPY . .
RUN uv sync --no-dev \
 && for project in modules/moph modules/requests modules/bills clients/web; do uv sync --no-dev --directory "$project"; done
COPY --from=web /app/node_modules node_modules
COPY --from=web /app/admin/dist admin/dist
COPY --from=web /app/modules/moph/ui/dist modules/moph/ui/dist
COPY --from=web /app/modules/requests/ui/dist modules/requests/ui/dist
COPY --from=web /app/modules/bills/ui/dist modules/bills/ui/dist
CMD ["deploy/start.sh"]
