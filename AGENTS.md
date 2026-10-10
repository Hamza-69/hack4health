# hack4health

Modular AI agent reached through chat clients. Capabilities are added as modules; suppliers act on them from an admin panel.

## Components

- **Clients**: WhatsApp, Telegram, maybe a web app. The only way into the system.
- **Agent API**: one REST endpoint (webhook). Takes `user_id` + `messages[]` (debounced by the client). Only our clients can call it.
- **Modules**: one per functionality. Each module owns:
  - MCP tools (used by the agent)
  - its own tables, linked to tickets by `ticket_id`
  - admin API routes and pages
  - the update event sent to the user when a supplier acts, and its WhatsApp template
- **Admin panel**: thin shell. A shared tickets page (filter by `kind` and status) plus one page per module. Never sees chats, only tickets and module data.
- **DB**: Postgres.

## Identity

- One user per app account; no linking across apps.
- `user_id = uuid5(prefix + id)`, prefix per app: `wa:`, `tg:`, `web:`.
- Phone numbers are normalized to E.164 before hashing.

## Data model

```
users
  id                    uuid PK
  messages              jsonb    -- live chat, full LLM API format
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

1. Client debounces and calls the webhook with `user_id` + `messages[]`.
2. Lock the user row (`SELECT ... FOR UPDATE`).
3. If an agent run is active (`agent_running_since` set and not stale): push messages to the live queue, unlock, return.
4. Otherwise: prune if needed, append messages, set `agent_running_since`, unlock, start the agent.
5. During the run, the live queue is poured into context at each tool-call step.
6. When the loop ends: lock. If the queue has messages, pour them in and run another turn. Otherwise clear `agent_running_since`. Unlock.
7. A run flag older than a few minutes counts as stale (crashed run).

## Supplier updates

When a supplier acts in a module, the module produces an update event and the core calls `notify(user_id, event, template)`:

- The event becomes a message tagged for the agent: `{"role": "user", "content": "[supplier · ticket 12] Appointment confirmed, Tue 10am"}`. The system prompt says tagged messages come from suppliers, not the user.
- It goes into `users.messages` and starts the agent if idle, or into the live queue if a run is active.
- Within 24h of the user's last message: the agent tells the user in its own words.
- After 24h: the module's WhatsApp template is sent instead of running the agent; the message is still appended so the agent has context when the user replies.
- The ticket moves to `awaiting_user`. When the user responds, the agent marks it `resolved` and writes `resolution`.

## Code

```
core/
  db.py          # engine, Session, Base (DATABASE_URL env var)
  models.py      # users, tickets, archives
  identity.py    # user_id_for(app, account_id)
  chat.py        # lock_user, archive_if_done
  registry.py    # MODULES list; load_models() for Alembic
modules/
  <name>/models.py   # module tables, linked by ticket_id
migrations/      # Alembic; env.py loads every registered module
tests/
```

Adding a module: create `modules/<name>/models.py` with tables on `core.db.Base` (prefix table names with the module name), add `"<name>"` to `MODULES` in `core/registry.py`, then autogenerate a migration.

Commands:

```bash
docker compose up -d                                  # local Postgres
uv run alembic upgrade head                           # apply migrations
uv run alembic revision --autogenerate -m "message"   # new migration after model changes
uv run pytest                                         # DB tests skip without Postgres
```

Alembic autogenerate does not handle two things; fix them by hand in the migration: foreign keys that close a cycle (like `users.current_ticket_id`) must be added with `op.create_foreign_key` after both tables exist, and Postgres enum types must be dropped explicitly in `downgrade`.

## Open

- Agent internals (framework, prompts, tools) — later.
- Where the live queue is stored.
- How the API restricts callers to our clients.
