# hack4health

A modular AI agent that users reach through WhatsApp, Telegram or the web. Each capability is a **module**: its own small service with MCP tools for the agent, its own database schema, and its own admin page that the admin panel embeds. The architecture is in [AGENTS.md](AGENTS.md).

## Quick start

Needs `uv`, Node and Docker. The agent needs `OPENAI_API_KEY=...` in a `.env` at the repo root.

```bash
docker compose up -d                 # Postgres on localhost:5432
uv sync
npm install
uv run alembic upgrade head          # core tables
uv run h4h init                      # signing keys + a token for each local module and client
uv run h4h admin create you@example.com   # prompts for a password
uv run h4h dev                       # core, admin panel, every module and the web chat
```

Talk to the agent at http://localhost:9000, the web chat client. Each browser is its own user; **New chat** starts over as a new one. The admin panel is at http://localhost:5173.

To watch a ticket flow through without the model, make the agent's tool call yourself:

```bash
uv run h4h tools call noop__open_request --user wa:+96170123456 --args '{"title": "Insulin refill", "details": "2 pens by Tuesday"}'
```

The ticket shows up under **Tickets**. Answer it under **Modules → Noop**, then check the agent's view:

```bash
uv run h4h tools call noop__request_status --user wa:+96170123456 --args '{"ticket_id": "<id from above>"}'
```

## Make a module

```bash
uv run h4h module new pharmacy       # copies modules/noop, registers it, writes its token
```

Restart `uv run h4h dev`. It appears in the admin panel, and its tools are callable as `pharmacy__<tool>`. Then edit:

| File | What goes there |
|---|---|
| `modules/pharmacy/app/tools.py` | MCP tools the agent calls |
| `modules/pharmacy/app/models.py` | your tables (in the `pharmacy` Postgres schema) |
| `modules/pharmacy/app/api.py` | API for your admin page, under `/api` |
| `modules/pharmacy/ui/src/App.tsx` | your admin page |

To give a supplier access to just this module:

```bash
uv run h4h admin create pharmacist@example.com --role supplier --module pharmacy
```

### SDK cheatsheet

Python (`from h4h import ...`, module object in `app/module.py`):

- `user = await module.user(ctx)` in a tool: the chat user. The id comes from a core-signed token, never from the model. Calls without a valid token are refused before any tool runs, so a tool can't be left open by accident.
- `module.core.create_ticket(user, title, details)` (sends the user's token as proof, so call it while handling the tool call), `.get_ticket(id)`, `.list_tickets()`, `.update_ticket(id, status=..., resolution=...)`, `.notify(id, message)`: the core's ticket API. A module only sees its own tickets.
- `raise ToolError("...")` for failures the agent should read. Any other exception reaches the agent as a generic error.
- `class Thing(module.Base)` for tables. They're created on startup in the module's schema. Store `ticket_id` to link to tickets; there are no foreign keys into the core.
- `@module.api.get("/things")` for admin routes. Every route requires an admin token; add `admin: Admin = Depends(module.admin)` to know who is calling.

UI (`from "@h4h/module-ui"`):

- `<ShellProvider>` wraps the app. It gets the admin token from the panel and renews it.
- `useApi()` is `fetch` for your `/api`, with the token attached.
- `useAdmin()` returns the logged-in admin: `{ id, email, role }`.

## Commands

```bash
uv run h4h --help
uv run h4h module list               # the registry (modules.toml)
uv run h4h tools list                # every module's tools, as the agent sees them
uv run h4h client token web          # fresh token for a chat client registered in clients.toml
uv run pytest                        # DB tests skip without Postgres
uv run alembic revision --autogenerate -m "message"   # after changing core/models.py
```
