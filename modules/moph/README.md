# Ministry Info (`moph`)

Answers the public's questions about Lebanon's Ministry of Public Health from the moph.gov.lb crawl in `sandpit/data/` (see `sandpit/crawler/README.md`).

## Setup

Add `OPENAI_API_KEY=...` and `PINECONE_API_KEY=...` to `modules/moph/.env` (not committed). Then:

```bash
uv run h4h dev                                   # from the repo root; starts this module on :8002
cd modules/moph && uv run python -m app.ingest   # once, and after every re-crawl
```

Or press **Reload from files** on the module's admin page. A reload replaces the crawled data, syncs the search index and keeps the unanswered questions and search log. The first load embeds everything (a few minutes); later ones only embed text that changed.

## Agent side

The answering rules live in the MCP server instructions (`app/module.py`). The agent's system prompt should include them. Tools:

| Tool | Answers |
|---|---|
| `search_services` | how to apply for something: documents, eligibility, office, hours, fees, forms |
| `get_service` | one service by id |
| `search_ministry_site` | site pages, news and the documents they link (laws, decisions, circulars, guidelines), with dates: programmes, announcements, what the ministry covers and for whom |
| `lookup_drug` | public price, cheaper equivalents, free medicine lists |
| `find_facilities` | hospitals, PHC centres, pharmacies... by type, area, name, or a location the user shared (matched to its caza by `app/places.py`, no distances); each with a Google Maps link |
| `get_contacts` | hotlines |
| `report_unanswered` | logs a question we could not answer, for the admin page |
| `report_claim` | logs a forwarded message or rumour the agent checked, with its verdict and source; near-duplicates share a key (`app/text.py`) |

Every result says `found`, carries official links and `data_as_of`. Searches always return the closest records, each marked `strong` or `weak`; `found` means at least one strong match. When nothing is found, the result also carries fallback contacts.

## Search

Services, pages, news and documents are searched by meaning in a Pinecone serverless index (`app/search_index.py`), so questions in English, Arabic or Arabizi find the Arabic data:

- **Index:** one index (`moph`, created on the first load), two namespaces: `services` (one vector per service) and `site` (chunks of pages, news and documents, with their title, URL, date and text as metadata).
- **Embeddings:** OpenAI `text-embedding-3-large` at 1024 dimensions, for the data when it is loaded and for each question.
- **Sync:** a vector's id is its record plus a hash of what was embedded, so a load embeds only new or changed text and deletes what is gone. Pinecone is the only place vectors are kept.
- **Documents** are the files the crawler downloaded and extracted (or OCR'd); Excel price lists are tables and stay out.
- Without the two keys, search tools return an error the agent can explain; drug and facility lookups still work.

Drug names are matched in Latin letters, with typo tolerance.

## Admin side

- **Overview**: data counts, last load, reload button, search stats
- **Insights**: questions per day for the last 7 days by kind, the share of searches answered, and the top 5 rumours. Counts only, never question text; any count under 5 shows as "fewer than 5"
- **Rumours**: claims people asked Wasel to check, with how often, the verdict and the official source
- **Unanswered**: questions the agent could not answer
- **Searches**: what the agent searched for, and which searches found nothing

## Tests

```bash
cd modules/moph && uv run pytest
```

`tests/test_retrieval.py` runs real questions against the crawl data and the Pinecone index (read-only; load the data first). Add a case whenever a search returns the wrong thing.

## Known gaps in the data

- The Facility Locator has pharmacies only for Beirut, Mount Lebanon, Bekaa and Baalbek-Hermel, and no street addresses.
- Only 3 of 229 services list explicit steps; 70 list eligibility.
- Only some of the ~11,000 files linked from the site are downloaded so far (`attachments` crawler step); `/files/*` is disallowed by robots.txt.
