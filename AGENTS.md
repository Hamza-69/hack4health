# hack4health

Modular AI agent reached through chat clients. Each capability is a separate module service; suppliers act on them from one admin panel.

## Components

- **Clients**: WhatsApp, Telegram, a web app. The only way into the system. Each is registered in `clients.toml` with the URL the core POSTs replies to. Built so far: `clients/web/`, a web chat for testing.
- **Agent API** (`POST /agent/messages`): the webhook. Takes `account_id` + `messages[]` (debounced by the client) and returns at once; the agent's replies are POSTed to the client's `<url>/messages` as `{account_id, text}`. Only registered clients, with their client token, can call it.
- **Agent** (`core/agent.py`, `core/runs.py`): a LangGraph agent that runs inside the core (see Agent).
- **Core** (`core/`): owns users, chats, tickets, archives and admins. Serves the admin API, the module API and the public key. Reads the module registry.
- **Modules** (`modules/<name>/`): one service per functionality, built on the SDK (see Modules).
- **Admin panel** (`admin/`): React shell that embeds each module's UI in an iframe. Never sees chats, only tickets and module data.
- **SDK** (`sdk/python` = `h4h`, `sdk/ui` = `@h4h/module-ui`): everything shared by modules, so a module only writes tools, routes, tables and pages.
- **DB**: one Postgres server. Core tables live in the default schema; each module gets its own schema.

## Modules

The registry is `modules.toml` at the repo root; the core reads it on every use:

```toml
[noop]
title = "Noop"                    # shown in the admin panel (optional)
url = "http://localhost:8001"     # backend: MCP at <url>/mcp, admin API at <url>/api
ui_url = "http://localhost:5174"  # embedded admin UI (optional; defaults to <url>/ui/, the built UI)
```

`uv run h4h module new <name>` copies `modules/noop`, renames it, picks free ports, adds the registry entry and writes the module's token. `uv run h4h dev` starts every local module from the registry.

Each module:

- runs one backend (`Module(...).app()`): MCP server, admin API, and the built UI
- keeps its tables in its own Postgres schema (created on startup) and never touches core tables
- creates tickets for the user from its MCP tools through the core API; `tickets.kind` is the module's name
- refers to tickets by `ticket_id` (no foreign key across schemas)
- updates its tickets and calls `notify` through the core API, authenticated with its module token
- owns the update event and WhatsApp template sent to the user when a supplier acts

The agent reaches every module's tools through `core/tools.py`: tool names are `<module>__<tool>`, and each call gets a fresh user token in `_meta`. `uv run h4h tools call` uses the same path.

## Agent

A LangGraph loop (`core/agent.py`): the model answers or calls tools until it answers without one. The model is `AGENT_MODEL` (any `init_chat_model` string, default `openai:gpt-5.6-luna`; OpenAI models go through the Responses API) and needs `OPENAI_API_KEY` in the root `.env`.

- The system prompt is built each turn: base rules, each module's MCP `instructions`, the user's open tickets, and the resolutions of the last few archived tickets.
- Tools: every module's tools plus the core's own `resolve_ticket`, which closes one of this user's `awaiting_user` tickets with a `resolution`.
- No checkpointer: the chat lives in `users.messages` as chat-completions dicts. Provider extras (OpenAI's encrypted reasoning) stay in memory for the turn and are not saved.
- Every assistant message with text goes to the user's client as soon as the model returns it.
- A failed or timed-out tool call goes back to the model as the tool result. Any other failure ends the run and the user gets a short fallback message.

Runs (`core/runs.py`) serve many users at once, one run per user at a time:

- A run is an asyncio task in the core process, at most `AGENT_MAX_RUNS` (default 50) at once. Model and tool calls never hold a DB connection or the user lock.
- While a user's run is active, only it writes `users.messages`; new messages and supplier updates go to `users.queue`.
- Before each model call the run locks the user, checks `agent_running_since` is still the value it set, saves the chat, pours in the queue and refreshes the flag. A run whose flag was replaced stops without writing.
- All of this state is in Postgres, so several core workers can share users. A sweeper in each core restarts runs whose flag went stale.

## Tokens

The core signs JWTs (EdDSA) with `keys/private.pem` and publishes the public key at `/.well-known/jwks.json`. Modules verify with it, so they can read tokens but never create them. A token's audience is either `core` or one module, so any other module rejects it, and its `typ` claim stops one kind being used as another.

| Token | From → to | Audience | Lifetime |
|---|---|---|---|
| session | admin panel → core | `core` | 12h, from login |
| module | module → core | `core` | no expiry; removing the module from `modules.toml` revokes it |
| user | core → module MCP server, in `_meta["h4h/user_token"]`; module → core when creating a ticket | the module | 5 min, minted per tool call |
| admin | admin panel → module UI → module backend | the module | 15 min |
| client | chat client → agent API | `core` | no expiry; removing the app from `clients.toml` revokes it |
| reply | core → chat client, with each reply | `client:<app>` | 5 min, minted per reply |

- **User token**: the model never sees the user id and cannot change it. The SDK refuses any tool call without a valid one before the tool runs; tools get the user with `await module.user(ctx)`. To create a ticket, the module hands the same token back to the core instead of a bare user id, and the core verifies it was minted for that module, so a module can't open tickets for users who never called it.
- **Admin token**: the shell gets it from `POST /admin/modules/<name>/token` and hands it to the iframe with `postMessage` (never in the URL). The module UI sends it as `Authorization: Bearer <token>` to its backend. A minute before expiry, or after a 401, the UI asks the shell for a fresh one. Protocol: `sdk/ui/src/protocol.ts`.

## Identity

- One user per app account; no linking across apps.
- `user_id = uuid5(prefix + id)`, prefix per app: `wa:`, `tg:`, `web:`.
- Phone numbers are normalized to E.164 before hashing.
- The core keeps the normalized account id in `users.address` (and the app in `users.app`) to send replies.

## Data model

```
users
  id                    uuid PK
  messages              jsonb    -- live chat, chat-completions format
  queue                 jsonb    -- live queue: messages that arrived during a run
  app, address          -- where replies go: wa | tg | web, normalized account id
  current_ticket_id     → tickets.id, nullable
  agent_running_since   timestamp, nullable

tickets
  id, user_id
  kind                  -- which module
  title, details
  status                -- active | awaiting_user | resolved | archived
  resolution            text, nullable
  archive_id            → archives.id, nullable
  created_at, resolved_at, archived_at

archives
  id, user_id
  messages              jsonb    -- the pruned slice of the chat
  created_at

admins
  id, email, password_hash
  role                  -- operator | supplier
  modules               -- module names this admin can open
```

## Ticket lifecycle

```
active → awaiting_user → resolved → archived
```

- `active`: being worked on.
- `awaiting_user`: supplier is done, waiting for the user to respond.
- `resolved`: the agent closed it after the user responded and wrote `resolution`.
- `archived`: pruned together with the chat slice it belongs to.

A ticket in `awaiting_user` stays open indefinitely; no timeout.

## Chat pruning

Each user has one continuous chat. The live part sits in `users.messages`.

Pruning happens when the next message arrives, under the user lock, in one transaction, if the user has at least one `resolved` ticket and none `active` or `awaiting_user`:

1. Create an `archives` row with the live messages.
2. Set those tickets to `archived` with that `archive_id`.
3. Clear `users.messages` and `current_ticket_id`.
4. The incoming messages start the new live chat.

The new chat loads the last few `resolution` notes as background instead of old messages.

## Request flow

1. Client debounces and POSTs `account_id` + `messages[]` to `/agent/messages` with its client token; the app comes from the token.
2. Lock the user row (`SELECT ... FOR UPDATE`), creating it if new, and store `app` and `address`.
3. If an agent run is active (`agent_running_since` set and not stale): append the messages to `users.queue`, unlock, return `queued: true`.
4. Otherwise: prune if needed, append whatever a crashed run left in the queue and then the messages, set `agent_running_since`, unlock, start the run.
5. During the run, the queue is poured into the chat before each model call.
6. When the agent answers without calling a tool: lock. If the queue has messages, pour them in and run another turn. Otherwise clear `agent_running_since`. Unlock.
7. A run flag older than 5 minutes counts as stale (crashed run): the next message starts a new run, and the sweeper restarts it within a minute anyway.

## Supplier updates

When a supplier acts in a module, the module calls the core's `notify` endpoint (`POST /module/tickets/<id>/notify`). Everything below is built except the 24h template:

- The event becomes a message tagged for the agent: `{"role": "user", "content": "[supplier · <module> · ticket <id>] Appointment confirmed, Tue 10am"}`. The system prompt says tagged messages come from suppliers, not the user.
- It goes into `users.messages` and starts the agent if idle, or into the live queue if a run is active.
- Within 24h of the user's last message: the agent tells the user in its own words.
- After 24h: the module's WhatsApp template is sent instead of running the agent; the message is still appended so the agent has context when the user replies.
- The ticket moves to `awaiting_user`. When the user responds, the agent marks it `resolved` and writes `resolution`.

## Code

```
core/
  db.py, models.py   # engine, Base; users, tickets, archives, admins
  identity.py        # user_id_for(app, account_id)
  chat.py            # lock_user, archive_if_done
  tokens.py          # signing keys, minting, JWKS
  registry.py        # modules.toml, clients.toml
  app.py             # FastAPI app: admin_api.py (/admin), module_api.py (/module), agent_api.py (/agent), JWKS
  agent.py           # the LangGraph agent: prompt, tools, model loop
  runs.py            # agent runs: one per user, live queue, sweeper, replies to clients
  tools.py           # agent side: list and call every module's MCP tools
  cli.py             # `uv run h4h ...`
admin/               # admin panel shell (Vite + React + Tailwind)
sdk/python/h4h/      # module SDK: Module, User, Admin, CoreClient, ToolError
sdk/ui/              # @h4h/module-ui: ShellProvider, useApi, useAdmin, postMessage protocol
modules/noop/        # example module and the template for `h4h module new`
clients/web/         # web chat client: the page, debounce, reply callback (app/main.py, app/static/index.html)
  app/               # module.py, tools.py, models.py, api.py, main.py
  ui/                # its admin page
migrations/          # Alembic, core tables only
modules.toml         # module registry
clients.toml         # chat client registry
sandpit/             # not part of the product: moph.gov.lb crawler and its data (crawler/, data/)
tests/
```

Each module is its own uv project (own `.venv`, depends on `h4h` by path) and its UI is an npm workspace. `uv run h4h dev` runs the core on :8000, the admin panel on :5173, every local module on the ports from `modules.toml`, and every local client on the port from `clients.toml` (the web chat on :9000), with merged output.

Commands:

```bash
docker compose up -d                                  # local Postgres
uv run alembic upgrade head                           # apply core migrations
uv run h4h init                                       # signing keys + module and client tokens
uv run h4h admin create <email> [--role supplier --module <name>]
uv run h4h dev                                        # run everything
uv run h4h module new <name>                          # new module from the noop template
uv run h4h tools list | call <module>__<tool> --user wa:<phone> --args '{...}'
uv run h4h client token <app>                         # fresh token into clients/<app>/.env (printed if hosted elsewhere)
uv run alembic revision --autogenerate -m "message"   # new migration after core model changes
uv run pytest                                         # DB tests skip without Postgres
```

Core migrations only cover the default schema; modules create their own tables on startup (switch a module to its own Alembic setup once its schema starts changing).

Alembic autogenerate does not handle two things; fix them by hand in the migration: foreign keys that close a cycle (like `users.current_ticket_id`) must be added with `op.create_foreign_key` after both tables exist, and Postgres enum types must be dropped explicitly in `downgrade`.

MCP tool errors: raise `ToolError` for messages the agent should see; any other exception is hidden as a generic crash message.

## Open

- The WhatsApp and Telegram clients: receive messages, debounce, call the agent API, send replies, verify the reply token (`clients/web/` shows the shape).
- The 24h WhatsApp template fallback: modules need a way to name their template in `notify`, and the core sends it through the client instead of running the agent.
