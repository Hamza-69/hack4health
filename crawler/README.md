# Wasel crawler: all public data on moph.gov.lb (Arabic + English)

## Run it (from the repo root, in your own Terminal)

```bash
cd ~/Developer/hack4health
python3 -m venv .venv && source .venv/bin/activate
pip install -r crawler/requirements.txt

python crawler/tests/test_parsers.py      # 10 offline parser tests, takes 1 second
python crawler/tests/e2e_mock.py          # whole pipeline against a fake site, takes 5 seconds

python -m crawler.run priority            # steps 1-4: services, facilities, drugs, free meds (~10-20 min)
caffeinate -i python -m crawler.run full  # everything else, overnight (keeps the Mac awake)
```

Watch progress from a second Terminal tab with `tail -f data/state/progress.log`.

The crawl is **resumable**. Every fetched URL is cached in `data/state/cache/` and listed in `data/state/visited.txt`, so after a crash or Ctrl-C you run the same command again and it continues where it stopped. To refresh, delete the cache entry or the whole `data/state/cache/`. The first news listing page is always refetched.

You can also run single steps:
`python -m crawler.run services | facilities | drugs | free_meds | pages | page_attachments | news_recent | news_old | attachments | facility_details | drug_details | retry_failed | extract | hotlines | rules_candidates | report`

Environment knobs: `WASEL_CONCURRENCY` (default 3), `WASEL_DELAY` (default 0.5 s per request), `WASEL_MAX_FILE_MB` (default 150), `WASEL_UA`.

## Endpoints found (browser DevTools, 10 Oct 2026)

None of the databases has a JSON API. The "AJAX" calls are CakePHP pagination requests that return an **HTML fragment** with a `<table>`. The named parameter `limit:` is honoured up to **100 rows per page** (anything higher is capped at 100).

| Data | Endpoint the page calls | What we call |
|---|---|---|
| Facility Locator | `GET /HealthFacilities/index/3/188/{type}/page:{N}?` (30 rows) | `GET /{lang}/HealthFacilities/index/3/188/{type}/limit:100/page:{N}`, where type `0` = all facilities (≈2,360 rows, 24 pages) and `1`-`8` = one type each (1 Governmental Hospitals, 2 Physiotherapy, 3 Radiology Lab, 4 PHC Centers, 5 Dental Lab, 6 Nurseries, 7 Pharmacies, 8 Private Hospitals). We run every type in English (type 0 plus each of 1-8) and union by facility id in case the server's ordering isn't stable between pages. The Arabic pass adds the Arabic type name. |
| Facility detail | — | `GET /{lang}/HealthFacilities/view/3/188/{id}/`: address, fax, email, director, status, ownership, beds by ward, staff, lab and blood-bank licences |
| National Drugs DB | `GET /en/Drugs/index/3/4848/page:{N}/sort:Drug.brand_name/direction:ASC` (30 rows) | `GET /en/Drugs/index/3/4848/limit:100/page:{N}/sort:Drug.id/direction:ASC` (≈6,030 rows, 61 pages), plus the same sorted by `Drug.brand_name` as a cross-check, unioned by drug id |
| Drug detail | `view_shop('/en/Drugs/view/{id}')` | `GET /en/Drugs/view/{id}`: code, registration number, presentation, route, agent, laboratory, country, pharmacist margin, stratum, exchange date, % subsidy |
| News | `GET /{lang}/DynamicPages/listing/16/page:{N}` (8 per page, 529 pages) | `GET /{lang}/DynamicPages/listing/16/limit:100/page:{N}` (≈43 pages per language) |
| Admin services list | `openAsCat(dept, mode)` → `GET /AdministrativeServices/view/{dept}/{mode}` (mode 0 = by department, 1 = by category) | Same URL with a language prefix. This lists 229 service ids (max id 251). We also probe ids `1..max+150`; a missing id returns HTTP 200 with an empty template, which the parser detects. |
| Service detail | — | `GET /{lang}/AdministrativeServices/details/{id}`. Form downloads are at `/AdministrativeServices/download/{fileId}`. |
| Laws tree | `openLawCat(cat)` → `GET /Laws/view/{cat}` | Same URL with a language prefix. Files are at `/Laws/download_file/{id}`. |

Other site facts the parsers rely on:

- The main content is always `#paginatedContent`. News dates are `.newsBlockDate`: `DD/MM/YYYY` on the English side and `YYYY/MM/DD` in Arabic-Indic digits on the Arabic side.
- Emails are Cloudflare-obfuscated (`data-cfemail`). We decode them.
- `Media/view/{id}`, `DynamicPages/view_page/{id}/16`, `DynamicPages/view/{id}` and `/view/{id}` are the same item. We dedup on `{lang}:item:{id}`.
- Service pages show Arabic labels on both language sides. Usually the content is identical, and Arabic is taken as primary.
- The site sits behind Cloudflare. If you see many `cloudflare_403` lines in `data/failed_urls.txt`, slow down (`WASEL_DELAY=2`) and re-run.

## What gets written

```
data/raw/pages.jsonl        url, canonical_url, lang, content_id, section, title, date, text, attachments, fetched_at, dedup_key (+service_id/facility_id/listing_date)
data/raw/files/...          attachments at their original path (e.g. data/raw/files/userfiles/files/News/...)
data/raw/files.jsonl        url, local_path, type, size, source_page_url, text_path (+extract_note, pages)
data/text/...               .txt for PDF/DOCX, one .csv per sheet for XLSX/XLS
data/structured/services.json   spec fields + directorate, email, form_number, form_labels, department/section from the tree, raw label->value maps (fields_ar / fields_en)
data/structured/facilities.csv  name_en, name_ar, type, caza, phone, investment_auth_no, url (+facility_id, type_id, type_ar, url_ar)
data/structured/facilities_details.csv
data/structured/drugs.csv       atc, brand_name, brand_or_generic, ingredients, dosage, form, price, url (+drug_id, price_lbp)
data/structured/drugs_details.csv
data/structured/free_meds.csv   every column of the free-medicine / tender / AMAN Excel files + source_file, source_sheet, source_url
data/structured/hotlines.csv    number, purpose, source_url (+source_date, mentions, context)
data/structured/rules_candidates.csv  2025-26 pages mentioning coverage topics, used to draft current_rules.csv
data/report.md, data/failed_urls.txt
data/state/                 cache + progress log (do not commit)
```

## Rules the crawler follows

- Only `www.moph.gov.lb`, never the `*.intouchmena.com` mirrors. It respects robots.txt (`/files/*` is skipped).
- It skips `sort:`, `direction:`, `orderField=`, `orderDir=`, `letter:` and `limit:` variants, share links, `/Users/*` (login, register, `track_document`), `/Search/*` and every form.
  - **Exception:** the drugs step itself requests `sort:Drug.id`. A fixed order is the only way to page through the drugs table without gaps.
- At most 3 requests run in parallel, with a 0.5-0.7 s pause after each. Timeout is 30 s, with 3 retries at 2, 4 and 8 s backoff. User-Agent: `WaselHackathonBot (AUB Hack for Health)`.
- Failed URLs are logged to `data/failed_urls.txt`, retried by the `retry_failed` step, and anything still failing is kept in that file.
