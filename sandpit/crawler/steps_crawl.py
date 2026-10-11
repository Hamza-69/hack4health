"""Steps 5-6 (+ extras): static pages BFS, news archive, facility/drug detail pages, failed-URL retry."""
from __future__ import annotations

import asyncio
import csv
import json
import re
from collections import deque
from typing import Dict, List, Optional

from . import config as C
from . import parse as P
from .fetch import Fetcher
from .progress import log
from .store import Stores
from .steps_structured import write_csv, gather_limited

SEED_PATHS = ["/", "/about", "/laws", "/AdministrativeServices/index", "/AdministrativeServices/index/1", "/e-services",
              "/publications", "/Media", "/Media/alerts", "/Media/announcements", "/Media/events_conferences",
              "/Media/health_in_lebanon", "/faq", "/complaints", "/contact", "/health_awareness", "/health_care",
              "/quality", "/campaigns", "/programs_projects", "/governance", "/statistics", "/administrative_services",
              "/Pages/3/77224", "/Pages/3/3010", "/Drugs/recalls/3/4849"]

# handled by dedicated steps (or pure duplicates) -> not followed by the generic crawler
BFS_SKIP = re.compile(r"/(ar|en)/(DynamicPages/listing/16|Media/news|Drugs/index|Drugs/view|HealthFacilities/|"
                      r"AdministrativeServices/details|AdministrativeServices/download)|/limit:|/letter:")


async def step_pages(f: Fetcher, st: Stores, max_pages: int = 60000) -> None:
    """Breadth-first crawl of everything that is not news/drug/facility/service (those have their own steps)."""
    queue = deque()
    bfs_keys = set()  # content keys already fetched/queued by this crawl (Media/view/X == view_page/X ...)
    for lang in C.LANGS:
        for sp in SEED_PATHS:
            u = P.normalize_url(f"/{lang}{sp}" if sp != "/" else f"/{lang}/", C.BASE, lang)
            if u and P.content_key(u)[0] not in bfs_keys:
                bfs_keys.add(P.content_key(u)[0])
                queue.append(u)
    n_done = 0
    n_new = 0

    async def worker():
        nonlocal n_done, n_new
        while queue and n_done < max_pages:
            url = queue.popleft()
            r = await f.get(url)
            n_done += 1
            if not r.ok or not r.text or not re.search(r"<(html|div|body|table|ul)", r.text[:5000], re.I):
                continue
            rec = st.add_page_from_html(url, r.text)
            if rec:
                n_new += 1
            links, atts = P.extract_links(r.text, url)
            for a, label in atts:
                st.queue_attachment(a, url, label, P.url_lang(url), P.section_of(url))
            for u in links:
                if BFS_SKIP.search(u):
                    continue
                k, _ = P.content_key(u)
                if k in bfs_keys:
                    continue
                bfs_keys.add(k)
                if ":item:" in k and k in st.pages:
                    continue  # news item already stored by the news step
                queue.append(u)
            if n_done % 200 == 0:
                log(f"pages: {n_done} fetched, {n_new} new records, queue={len(queue)} ({f.stats()})")

    log(f"pages: BFS from {len(queue)} seeds (ar+en)")
    workers = [asyncio.create_task(worker()) for _ in range(C.MAX_CONCURRENCY * 2)]
    # workers exit when the queue is momentarily empty; restart them until it's really drained
    while True:
        await asyncio.gather(*workers)
        if not queue or n_done >= max_pages:
            break
        workers = [asyncio.create_task(worker()) for _ in range(C.MAX_CONCURRENCY * 2)]
    log(f"pages: finished - {n_done} fetched, {n_new} new page records ({f.stats()})")


async def step_news(f: Fetcher, st: Stores, since: Optional[str] = None, until: Optional[str] = None) -> None:
    """News archive via /{lang}/DynamicPages/listing/16/limit:100/page:N, details newest first."""
    items: List[Dict] = []
    for lang in C.LANGS:
        base = f"{C.BASE}/{lang}/DynamicPages/listing/16/limit:100"
        first = await f.get(base, ajax=True, use_cache=False)  # page 1 changes daily
        if not first.ok:
            log(f"news: listing {lang} failed")
            continue
        n = P.max_page(first.text)
        pages = [first] + await gather_limited([f.get(f"{base}/page:{p}", ajax=True) for p in range(2, n + 1)], 40)
        cnt = 0
        for r in pages:
            if r.ok:
                for it in P.parse_news_listing(r.text, r.url):
                    it["lang"] = lang
                    items.append(it)
                    cnt += 1
        log(f"news: {lang} listing pages={n} items={cnt}")
    # newest first: 2024-2026 first, then the rest
    items.sort(key=lambda x: (x["date"] or "0000", int(x["content_id"] or 0)), reverse=True)
    if since:
        items = [i for i in items if (i["date"] or "9999") >= since]
    if until:
        items = [i for i in items if (i["date"] or "0000") < until]
    todo = [i for i in items if i["key"] not in st.pages]
    log(f"news: {len(items)} listed, {len(todo)} details to fetch (since={since}, until={until})")

    async def one(it):
        r = await f.get(it["url"])
        if r.ok:
            st.add_page_from_html(it["url"], r.text, section="news", extra={"listing_date": it["date"]})
        return r.ok

    ok = 0
    for i in range(0, len(todo), 60):
        res = await asyncio.gather(*[one(it) for it in todo[i:i + 60]])
        ok += sum(res)
        if (i // 60) % 5 == 0:
            log(f"news: {i + len(res)}/{len(todo)} details ({ok} ok, newest date in batch {todo[i]['date']}) ({f.stats()})")
    log(f"news: finished {ok}/{len(todo)}")


async def step_facility_details(f: Fetcher, st: Stores) -> None:
    path = C.STRUCT / "facilities.csv"
    if not path.exists():
        log("facility_details: run facilities first")
        return
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    out = []

    # The Arabic page is a copy of the English one (same fields, English labels), and find_facilities
    # serves these, so they stay out of pages.jsonl and site search.
    async def one(row):
        rec = {"facility_id": row.get("facility_id"), "name_en": row.get("name_en"), "type": row.get("type")}
        if u := row.get("url"):
            r = await f.get(P.normalize_url(u, C.BASE, "en"))
            if r.ok:
                for k, v in P.parse_kv_details(r.text).items():
                    rec[f"en:{k}"] = v
        return rec

    for i in range(0, len(rows), 60):
        out.extend(await asyncio.gather(*[one(r) for r in rows[i:i + 60]]))
        if (i // 60) % 5 == 0:
            log(f"facility_details: {len(out)}/{len(rows)} ({f.stats()})")
    write_csv(C.STRUCT / "facilities_details.csv", out, ["facility_id", "name_en", "type"])
    log(f"facility_details: wrote {len(out)} rows")


async def step_drug_details(f: Fetcher, st: Stores) -> None:
    path = C.STRUCT / "drugs.csv"
    if not path.exists():
        log("drug_details: run drugs first")
        return
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    out = []

    async def one(row):
        u = row.get("url")
        rec = {"drug_id": row.get("drug_id"), "url": u}
        if u:
            r = await f.get(u)
            if r.ok:
                rec.update(P.parse_drug_view(r.text))
        return rec

    for i in range(0, len(rows), 60):
        out.extend(await asyncio.gather(*[one(r) for r in rows[i:i + 60]]))
        if (i // 60) % 10 == 0:
            log(f"drug_details: {len(out)}/{len(rows)} ({f.stats()})")
    write_csv(C.STRUCT / "drugs_details.csv", out, ["drug_id", "url"])
    log(f"drug_details: wrote {len(out)} rows")


async def step_retry_failed(f: Fetcher, st: Stores) -> None:
    if not C.FAILED_TXT.exists():
        return
    urls = []
    for line in C.FAILED_TXT.open(encoding="utf-8"):
        u = line.split("\t")[0].strip()
        if u and u not in urls:
            urls.append(u)
    still = []
    log(f"retry_failed: {len(urls)} distinct failed urls")
    for i in range(0, len(urls), 30):
        batch = urls[i:i + 30]

        async def one(u):
            if P.is_attachment(u):
                from .steps_files import download_one
                rec = await download_one(f, u, "")
                return u, bool(rec)
            if u in f.visited:
                return u, True
            r = await f.get(u, log_fail=False)
            if r.ok:
                st.add_page_from_html(u, r.text)
            return u, r.ok

        for u, ok in await asyncio.gather(*[one(u) for u in batch]):
            if not ok:
                still.append(u)
    C.FAILED_TXT.write_text("".join(f"{u}\tstill_failing_after_retry\n" for u in still), encoding="utf-8")
    log(f"retry_failed: {len(urls) - len(still)} recovered, {len(still)} still failing")
