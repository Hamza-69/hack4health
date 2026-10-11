# Eval

Runs each question in `questions.json` through the real agent (in process, a fresh user per question) and writes `report.md`: the answers, the tools called, what they found, latency, and the `expect` note to grade against.

1. Keys: `OPENAI_API_KEY` in the root `.env`; `OPENAI_API_KEY` and `PINECONE_API_KEY` in `modules/moph/.env`. The moph data must be loaded (`cd modules/moph && uv run python -m app.ingest`, with `DATABASE_URL` set as in the root `.env`, or **Reload from files** on its admin page).
2. Start everything: `uv run h4h dev`. The eval needs the core on :8000 (modules check user tokens against its JWKS) and moph on :8002.
3. From the repo root: `uv run python -m sandpit.eval.run`. Options: `--only demo_hernia_lb,ivig_en`, `--out path.md`, `--concurrency 4`.
4. It checks the key, the database, the moph module and search before asking anything, and stops with the reason if one is missing.
5. Runs write to the moph admin page like real users do (Searches, and Unanswered via `report_unanswered`): clear them before the demo.
