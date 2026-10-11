# Deploying on Fly and Neon

One Fly machine runs everything (`start.sh`): the core, the three modules, the web client and the WhatsApp client, with Caddy (`Caddyfile`) as the one public port. Postgres is a Neon database. The machine's volume (`/data`) keeps the signing keys, the photos and PDFs users send, and the linked WhatsApp session.

| Address | What |
|---|---|
| `https://wasel.fly.dev/` | the public site (redirects to `/chat/`); the chat is `/chat/chat`, the embed `/chat/widget.js` |
| `https://wasel.fly.dev/login` | the admin panel |

The WhatsApp QR page is not public: reach it with `fly proxy` (step 4).

## 1. Neon

Create a project in **AWS US East 1 (N. Virginia)**, next to the Fly region (`iad`), with Postgres 17. Copy the connection string with **connection pooling off** (the host has no `-pooler`): each service keeps its own pool. Paste it as Neon gives it; `h4h.db.database_url()` turns it into what asyncpg takes.

```bash
NEON='postgresql://neondb_owner:...@ep-....us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
```

## 2. Fill the database from the laptop

The image has no crawl data, so load it from here. The search index is the same Pinecone index as local, so nothing is embedded again.

```bash
DATABASE_URL="$NEON" uv run alembic upgrade head
(cd modules/moph && DATABASE_URL="$NEON" uv run python -m app.ingest)   # needs the keys in modules/moph/.env
DATABASE_URL="$NEON" uv run h4h admin create <email>                     # an operator, sees every module
DATABASE_URL="$NEON" uv run h4h admin create <email> --role supplier --module requests   # the desk
```

## 3. Fly

```bash
fly apps create wasel
fly volumes create wasel_data --region iad --size 1 -y
fly secrets set DATABASE_URL="$NEON" OPENAI_API_KEY=... PINECONE_API_KEY=...
fly deploy
```

Optional secrets: `AGENT_MODEL`, `WA_ALLOW` (see `clients/wa/`). The release command runs the core migrations before each deploy; the modules create their tables on startup. If the app name is taken, change `app` and `VITE_SHELL_ORIGIN` in `fly.toml`.

## 4. Link WhatsApp

```bash
fly proxy 9001
```

Open http://localhost:9001 and scan the QR code from WhatsApp › Settings › Linked devices on Wasel's phone. The session stays on the volume. Don't also run the WhatsApp client on a laptop with the same number, or both answer.

## Before the demo

```bash
DATABASE_URL="$NEON" uv run python -m sandpit.demo.reset   # clean slate, W-1042 next
fly logs
```

The core checks for stale runs every minute, so the Neon compute stays awake while the machine runs: no cold starts, but it uses compute hours the whole time.
