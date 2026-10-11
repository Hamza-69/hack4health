# Wasel (hack4health)

Wasel (واصل) is an AI agent on WhatsApp for Lebanon's Ministry of Public Health (MoPH). It answers any question from what the ministry publishes. When the answer is "you need to apply", it does the paperwork with the patient, sends it to the right desk at the ministry, and tells the patient when it moves. Think of it as the ministry's معقّب, the person who runs your paperwork through a ministry for you.

- Tagline: **"Ask it anything. When there's something to do, it does it."**
- Lebanese: **"اسأل… وهو بيخلّصلك المعاملة."**
- **Current focus: information access.** The agent must answer ministry questions correctly before anything else gets built on top.

## The hackathon

**Hack for Health Lebanon**, organised by the AUB Department of Computer Science and Faculty of Arts and Sciences. It runs October 10–11, 2026 in West Hall, AUB. Site: https://sites.aub.edu.lb/hack4health/ (the content is in an iframe to https://gregarious-taffy-e0e823.netlify.app/). Contact: Prof. Rida Assaf, ra278@aub.edu.lb, hackathon@aub.edu.lb.

- **Deadline: Sunday Oct 11, 14:00 sharp.** Upload the code and the presentation to OneDrive and submit both links through the site's form. Team demos follow. Shortlisted teams present to the judges at 16:00, and awards are at 17:00.
- **Demo length:** 3 minutes for the jury, 10 minutes on stage. The organisers want "build & demo, not slides" and ask for something that runs.
- **Challenge area:** Area 01, *Health information & access*: procedures and steps, eligibility and coverage, medications, services, referrals, costs, where to seek care. The "what people are asking" panel also touches Area 02 (complaints and feedback patterns). The other areas are Area 03 (displaced communities) and Area 04 (system readiness: shortages, inventory, capacity).
- **Judges:**
  - Prof. Rida Assaf (AUB Computer Science)
  - H.E. Dr. Rakan Nassereddine, **Minister of Public Health**
  - Ali Houjeij (Managing Director & Partner, BCG)

  The minister is on the panel, so pitch Wasel as a tool the ministry could adopt.
- **Policy hook:** the MoPH & UNICEF National Digital Health Transformation Strategy 2025–2030. It names AI-assisted decision-making, e-health and connected data as pillars. It also names the problems Wasel targets: records in silos, and information people can't reach when they need it.
- **Prizes:** USD 500, mentorship, and a possible path to a pilot.

Judging criteria and what each one means for this repo:

| Criterion | What they check | For us |
|---|---|---|
| Solution fit and impact | A real gap in Lebanon today; would it make sense if the ministry picked it up on Monday? | Ground everything in real ministry data and real procedures |
| Technical readiness | "We open it, press the buttons", a working system, not a mock-up | A demo that works end to end beats more features. Don't leave half-built paths in the demo |
| User experience | Usable without explanation, for low digital confidence, on real devices and connections | WhatsApp, short plain replies, Arabic / English / Arabizi, voice notes |
| Privacy and security | What is collected, who sees it, where a human stays in the loop | Admin panel never sees chats; signed tokens; ministry staff decide every request; the agent never diagnoses |
| Demo and presentation | A room that doesn't know the project gets it fast | One story, below |

## Product

**The gap: "six services, six doors."** The ministry's own pages send patients through a different channel for each service (sources in `modules/requests/app/catalog.json` and `sandpit/data/`):

| Service | How you get it today |
|---|---|
| Hospitalisation at the ministry's expense (operations) | Bring the papers in person to the card centre in Bir Hassan, Monday to Saturday |
| Cancer or MS medicine | Your doctor files on AMAN, you wait for an SMS, then get it from the hospital or pharmacy |
| Haemophilia or transplant medicine | Send documents by WhatsApp to 81/348838 |
| Humira | Go in person to the ministry's 4th floor |
| IVIG | Hand in form AK010IVIG-4 at the ministry, or apply online with a site account |
| Complaints | Call 1214 (also the app, website or email) |

Facts to keep straight, because the Minister is judging: the ministry's data never names hernia, so Wasel answers about the hospitalisation request in general and never claims a specific operation is covered. 1787 is for questions about hospital cover and for displaced people, not complaints. The hospitalisation request needs a civil registry extract (إخراج قيد فردي), not the ID card.

A Q&A bot fixes half of this: the information gets easy to find, but every request still goes through one person. Wasel gives the patient one door and the ministry one inbox. Positioning against the other team: they built the ministry's encyclopedia; we built its معقّب.

Three layers, one engine:

1. **Knows.** One knowledge base from the ministry's public data: hospitals, primary care centres, medicine lists and prices, procedures, circulars and coverage announcements. Every answer cites its source.
2. **Does.** A catalog of ministry services. Each entry lists who qualifies, the documents needed, the official form, the responsible desk and the deadline. One engine runs every service: it collects photos of the papers, catches what's missing, fills in the form and submits it with a request number. **Adding a service means adding an entry, not writing code.**
3. **Follows up.** The patient gets a message on every change and can ask "where's my request?" at any time. A request whose desk misses its deadline moves up a level on its own.

Ministry side:

- One inbox where requests arrive complete, with Approve / Ask for more / Decline.
- A "what people are asking" panel that surfaces confusion and rumours early. In July 2026 the ministry had to deny fake news about what it covers.

Answering rules (the product bar):

- **Accuracy beats coverage.** State only what a tool result says, with the official link and date. When the data doesn't cover a question, say so plainly and point to the right contact (the service's office, or 1214 / 1787). Never guess.
- If eligibility depends on something unknown (nationality, NSSF or army cover, displaced or not, which disease), ask one short question first.
- Reply in the user's language. Never diagnose; for emergencies, point to the Red Cross on 140.

Out of scope: medicine-arrival alerts, and actions for NSSF or private insurance.

**Demo story:**

1. A voice note: "My dad needs a hernia operation, does the ministry cover it?" Wasel asks whether he has other cover, then answers with the official source (hospitalisation for uninsured Lebanese, the documents, the desk) and offers to submit the request.
2. The family sends photos of the medical report and the NSSF statement (`sandpit/demo/specimens.html`). Wasel catches that the إخراج قيد is missing; they send it; Wasel shows a summary, asks to confirm, and submits request W-1042.
   Rehearse with `uv run python -m sandpit.eval.demo_flow --lang lb`; reset with `uv run python -m sandpit.demo.reset`.
3. On the laptop, someone presses Approve in the admin panel, and the judge's phone buzzes.
4. A judge asks any question of their own, to show the full knowledge base.

### Status (Oct 11, 2026)

| Layer | Where | State |
|---|---|---|
| Knows | `modules/moph/` (data from the `sandpit/` crawl of moph.gov.lb) | Built. Tools for services, site/news/document search (Pinecone, multilingual), drugs, facilities, hotlines, unanswered questions. Needs `OPENAI_API_KEY` + `PINECONE_API_KEY` and a data load (`modules/moph/README.md`) |
| Agent | `core/agent.py`, `core/runs.py` | Built: LangGraph loop, queue, supplier updates. Wasel prompt; replies in the user's language and script (a reminder each turn, and a rewrite when a reply comes out in the wrong script); voice/photo tags |
| Does | `modules/requests/` | Built: catalog of 4 services (hospitalisation, IVIG, haemophilia/transplant, complaints), missing-document check, confirm, submit with W-numbers |
| Follows up | core tickets, `notify`, `resolve_ticket`, `requests__request_status` | Built. Deadline escalation not built (overdue requests are flagged in the inbox) |
| Ministry inbox | admin panel → Ministry Inbox | Built: live queue, filled form, documents, Approve / Ask for more / Decline that reach the user in seconds |
| What people are asking | moph admin page: Unanswered, Searches | First version built |
| Clients | `clients/` | WhatsApp (`clients/wa/`, a number linked by QR code) and the web chat (`clients/web/`). Both take text, voice notes, photos and PDFs |

## Architecture

Modular AI agent reached through chat clients. Each capability is a separate module service; suppliers (here, ministry desks) act on them from one admin panel.

## Components

- **Clients**: WhatsApp, Telegram, a web app. The only way into the system. Each is registered in `clients.toml` with the URL the core POSTs replies to. Built so far: `clients/wa/` (WhatsApp) and `clients/web/` (a web chat for testing, and the demo fallback).
- **Agent API** (`POST /agent/messages`): the webhook. Takes `account_id` + `messages[]` (debounced by the client) and returns at once; the agent's replies are POSTed to the client's `<url>/messages` as `{account_id, text}`. Only registered clients, with their client token, can call it.
- **Media** (`POST /agent/media`): a client uploads a voice note, photo or PDF and gets back a text message to send with the user's others (see Media).
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

A LangGraph loop (`core/agent.py`): the model answers or calls tools until it answers without one. The model is `AGENT_MODEL` (any `init_chat_model` string, default `openai:gpt-6.1-sol`; OpenAI models go through the Responses API) and needs `OPENAI_API_KEY` in the root `.env`.

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

## Media

Clients turn what isn't text into text before it reaches the agent, through the core's `POST /agent/media` (`core/media.py`). Modules only ever see these messages:

| The user sends | The agent gets | Kept? |
|---|---|---|
| voice note | `[voice note] <transcript>` (OpenAI `TRANSCRIBE_MODEL`, default `gpt-4o-transcribe`) | no |
| photo (JPEG, PNG, WebP) | `[photo <link>] <one line on what it is>` (`VISION_MODEL`, default `gpt-5.4-mini`) | yes |
| PDF | `[document <link>] <one line on what it is>` | yes |
| location | `[location: <place or coordinates>]` (WhatsApp only, made by the client) | no |
| video, other files, contacts | `[... can't be opened ...]`, so the agent asks for another way | no |

- Links are `CORE_PUBLIC_URL/media/<random name>` (default `http://localhost:8000`). The name is the only key, so a module (the ministry's inbox) can show the photo by its link, and nobody can list or guess the files.
- The description names the document type and whose it is, so the requests module can tell what is missing. It can be wrong, and the prompt says so.
- A client holds its debounce until every upload in the batch is read, so the agent gets the user's messages together and in order.

## WhatsApp

`clients/wa/` is a Node service on Baileys: it links one WhatsApp number as a device, like WhatsApp Web, so nothing needs a Meta business account or a public URL.

- Link it: run `uv run h4h dev`, open http://localhost:9001 and scan the QR code from WhatsApp › Settings › Linked devices on the phone with Wasel's number. The session stays in `clients/wa/auth/` (gitignored); delete that folder to link another number. Only one laptop can hold the session at a time.
- Use a spare number: the client answers every private chat on it. `WA_ALLOW=96170123456,...` in `clients/wa/.env` limits it to those numbers. Groups, statuses, channels, reactions and stickers are ignored.
- Account ids are E.164 numbers. When WhatsApp hides the number behind a LID (`<digits>@lid`), the client looks it up in the session's LID mapping, and passes the LID itself as the account id only if that fails.
- It marks messages read and shows "typing…" until the reply arrives. Replies that come in while WhatsApp is reconnecting wait and go out once it is back.
- No 24h window: that rule belongs to the Cloud API, not to a linked device, so supplier updates always go through the agent.

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

When a supplier acts in a module, the module calls the core's `notify` endpoint (`POST /module/tickets/<id>/notify`). Everything below is built except the 24h template, which the WhatsApp client doesn't need (see WhatsApp):

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
  media.py           # voice notes, photos and PDFs from clients, as text messages; /media/<name> files
  runs.py            # agent runs: one per user, live queue, sweeper, replies to clients
  tools.py           # agent side: list and call every module's MCP tools
  cli.py             # `uv run h4h ...`
admin/               # admin panel shell (Vite + React + Tailwind)
sdk/python/h4h/      # module SDK: Module, User, Admin, CoreClient, ToolError
sdk/ui/              # @h4h/module-ui: ShellProvider, useApi, useAdmin, postMessage protocol
modules/noop/        # example module and the template for `h4h module new`
  app/               # module.py, tools.py, models.py, api.py, main.py
  ui/                # its admin page
modules/moph/        # Ministry Info: the "Knows" layer (see its README)
modules/requests/    # Ministry Inbox: the "Does" layer: catalog.json, request tools, inbox page
clients/web/         # web chat client: the page, debounce, reply callback (app/main.py, app/static/index.html)
clients/wa/          # WhatsApp client (Node, Baileys): linking, debounce, media, replies (main.js)
migrations/          # Alembic, core tables only
modules.toml         # module registry
clients.toml         # chat client registry
sandpit/             # not part of the product: moph.gov.lb crawler and data, eval/ (test questions, demo rehearsal), demo/ (reset, document specimens)
tests/
```

Each module is its own uv project (own `.venv`, depends on `h4h` by path) and its UI is an npm workspace. `uv run h4h dev` runs the core on :8000, the admin panel on :5173, every local module on the ports from `modules.toml`, and every local client on the port from `clients.toml` (the web chat on :9000, WhatsApp on :9001), with merged output. A client folder with a `package.json` is a Node client and an npm workspace (`npm install` at the root installs it).

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

- The Telegram client (`clients/web/` and `clients/wa/` show the shape).
- The 24h WhatsApp template fallback, only if we move from a linked device to the WhatsApp Cloud API: modules would name their template in `notify`, and the core would send it through the client instead of running the agent.
