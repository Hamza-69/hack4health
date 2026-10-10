# Ministry Info (`moph`)

Answers the public's questions about Lebanon's Ministry of Public Health from the moph.gov.lb crawl in `data/` (see `crawler/README.md`) plus facts curated by our team.

## Setup

Add `OPENAI_API_KEY=...` to `modules/moph/.env` (not committed). Then:

```bash
uv run h4h dev                                   # from the repo root; starts this module on :8002
cd modules/moph && uv run python -m app.ingest   # once, and after every re-crawl
```

Or press **Reload from files** on the module's admin page. A reload replaces the crawled data and keeps the official facts, unanswered questions and search log.

## Agent side

The answering rules live in the MCP server instructions (`app/module.py`). The agent's system prompt should include them. Tools:

| Tool | Answers |
|---|---|
| `search_services` | how to apply for something: documents, eligibility, office, hours, fees, forms |
| `get_service` | one service by id |
| `get_official_facts` | what the ministry covers and for whom, hotlines (curated, dated, most authoritative) |
| `search_ministry_site` | site pages and news, with dates |
| `lookup_drug` | public price, cheaper equivalents, free medicine lists |
| `find_facilities` | hospitals, PHC centres, pharmacies... by type, area, name |
| `get_contacts` | hotlines |
| `report_unanswered` | logs a question we could not answer, for the admin page |

Every result says `found`, carries official links and `data_as_of`. An empty result also returns fallback contacts.

Services, pages and facts are searched by meaning with OpenAI embeddings (`app/embeddings.py`), so questions in English, Arabic or Arabizi find the Arabic data. Keyword search (BM25 with Arabic normalization, `app/text.py`) is fused in for exact terms like form numbers, and takes over when there is no API key (`app/hybrid.py`). Embeddings are cached in the module's database. Drug names are matched in Latin letters, with typo tolerance.

## Admin side

- **Overview**: data counts, last load, reload button, search stats
- **Official facts**: add, edit, switch off the rules the agent trusts most
- **Unanswered**: questions the agent could not answer
- **Searches**: what the agent searched for, and which searches found nothing

## Tests

```bash
cd modules/moph && uv run pytest
```

`tests/test_retrieval.py` runs real questions against the crawl data. Add a case whenever a search returns the wrong thing.

## Known gaps in the data

- The Facility Locator has pharmacies only for Beirut, Mount Lebanon, Bekaa and Baalbek-Hermel, and no street addresses.
- Only 3 of 229 services list explicit steps; 70 list eligibility.
- Law and circular PDFs were not downloaded (`/files/*` is disallowed by robots.txt).
