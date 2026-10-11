# Plan for today (submission at 14:00)

## Step 1: get it working on both laptops (now to 07:00)

You type a question in the web chat at http://localhost:9000, and Wasel answers correctly with a ministry link. Everything else builds on this, so nothing else starts until it works.

- **Hamza** already has the keys. Run `uv run h4h dev` and ask a question at localhost:9000 to confirm it works.
- **Hamza** sends Ahmad three values privately: `OPENAI_API_KEY`, `PINECONE_API_KEY`, and `AGENT_MODEL` if it's set. Ahmad pastes them into his `.env` files.
  - Don't share `MODULE_TOKEN` or `CLIENT_TOKEN`. Each laptop makes its own.

## Step 2: split the work (07:00 to 11:00)

We split by folder, so we never edit the same files.

**Hamza: the phone side** (`core/`, `clients/`)

1. Wasel's prompt in `core/agent.py`: name, languages, short WhatsApp-style replies. About 30 minutes.
2. A WhatsApp client in `clients/whatsapp/`.
   - It links a spare phone number by QR code, using the Baileys library.
   - It passes incoming messages to the agent and sends the replies back.
   - It's the same job as `clients/web/`, but for WhatsApp.
3. Voice notes and photos, handled in that client:
   - A voice note is transcribed, then sent as `[voice note] <transcript>`.
   - A photo is saved and described in one line, then sent as `[photo <link>] <what the document is>`.

**Ahmad: the brain side** (`modules/`)

1. Answer quality: run the 29 test questions in `sandpit/eval/` and fix the wrong answers.
2. A new `requests` module:
   - Wasel collects the documents for a ministry request, spots what's missing, and submits it with a number like W-1042.
   - A ministry employee then approves it, asks for more, or declines it from the admin panel.

**How the halves connect:**

- Hamza's client turns voice notes and photos into the text messages above. Ahmad's module reads those.
- When the ministry presses Approve, the module tells the core. The core runs the agent, and the agent's reply goes to the user through Hamza's client.
- The core already does this part.

## Checkpoints (a 5-minute call each)

| Time | What should work |
|---|---|
| 07:00 | Both laptops answer questions in the web chat |
| 09:00 | Text in and out over WhatsApp. Filing a request from the web chat |
| 11:00 | **Stop adding features.** The full demo has worked once over WhatsApp |
| 11:00–13:00 | Rehearse, slides, record a backup video of the demo |
| 13:30 | Submit: zip the code and slides to OneDrive, paste the links in the site's form |

If WhatsApp isn't working by 09:30, we demo on the web chat instead.

## Git

Small commits straight to `main`. Run `git pull --rebase` before every push. Don't edit the other person's folders.

## Facts to get right

These come from the ministry's own pages. With the Minister judging, a wrong fact costs more than a missing one.

- **Hernia isn't mentioned anywhere.** The real service is the "hospitalisation request" for uninsured Lebanese patients. It's decided the same day.
  - Wasel answers about that service and never says "hernia is covered".
- **That service needs four documents:**
  - a civil registry extract (إخراج قيد فردي), not the ID card
  - a medical report
  - an NSSF "no cover" statement
  - a pledge of no other cover

  In the demo, Wasel catches the missing extract.
- **Hotlines:**
  - 1214: complaints and the main line
  - 1787: questions about hospital cover, during working hours
  - 01/832700: hospital admission
