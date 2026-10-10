"""Priority steps 1-4: administrative services, facility locator, drugs database, free-medicine Excel files."""
from __future__ import annotations

import asyncio
import csv
import json
import re
from typing import Dict, List, Optional

from . import config as C
from . import parse as P
from .fetch import Fetcher
from .store import Stores, now_iso
from .progress import log


def write_csv(path, rows: List[Dict], columns: List[str]) -> None:
    extra = []
    for r in rows:
        for k in r:
            if k not in columns and k not in extra:
                extra.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:  # BOM so Excel opens Arabic correctly
        w = csv.DictWriter(fh, fieldnames=columns + extra, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("; ".join(map(str, v)) if isinstance(v, list) else v) for k, v in r.items()})


async def gather_limited(coros, limit: int = 50):
    """Run coroutines in chunks so progress can be logged and memory stays flat (Fetcher enforces concurrency)."""
    out = []
    coros = list(coros)
    for i in range(0, len(coros), limit):
        out.extend(await asyncio.gather(*coros[i:i + limit]))
    return out


# =========================================================================== 1. services

def _service_listing_meta(html: str) -> Dict[str, Dict]:
    """From /AdministrativeServices/view/{dept}/0: service id -> {department_unit, section, number}."""
    doc = P.soup(html)
    meta: Dict[str, Dict] = {}
    cur_interest = cur_section = ""
    for el in doc.find_all(["td", "a"]):
        cls = el.get("class") or []
        if el.name == "td" and "interestCol" in cls:
            cur_interest = el.get_text(" ", strip=True)
        elif el.name == "td" and "sectionCol" in cls:
            cur_section = el.get_text(" ", strip=True)
        elif el.name == "a":
            m = re.search(r"/AdministrativeServices/details/(\d+)", el.get("href", ""))
            if m:
                nb = ""
                tr = el.find_parent("tr")
                if tr is not None:
                    nbtd = tr.select_one("td.nbCol")
                    nb = nbtd.get_text(" ", strip=True) if nbtd else ""
                meta.setdefault(m.group(1), {"listing_unit": cur_interest, "listing_section": cur_section,
                                             "listing_number": nb, "listing_title": el.get_text(" ", strip=True)})
    return meta


async def step_services(f: Fetcher, st: Stores) -> None:
    log("services: discovering ids from the department/category trees")
    meta: Dict[str, Dict] = {}
    dept_names = {}
    for lang in ("ar", "en"):
        idx = await f.get(f"{C.BASE}/{lang}/AdministrativeServices/index")
        if idx.ok:
            for m in re.finditer(r'openAsCat\((\d+),\s*0\);">\s*<div class="lawCatRowTitle">([^<]+)<', idx.text):
                dept_names.setdefault(m.group(1), {})[lang] = m.group(2).strip()
    for mode in (0, 1):
        for c in range(1, 31):
            r = await f.get(f"{C.BASE}/ar/AdministrativeServices/view/{c}/{mode}", ajax=True, log_fail=False)
            if r.ok:
                for sid, mm in _service_listing_meta(r.text).items():
                    if mode == 0:
                        mm["department_ar"] = dept_names.get(str(c), {}).get("ar", "")
                        mm["department_en"] = dept_names.get(str(c), {}).get("en", "")
                    else:
                        mm = {"category_id": c}
                    meta.setdefault(sid, {}).update({k: v for k, v in mm.items() if v})
    known = sorted(int(x) for x in meta)
    top = (known[-1] if known else 300) + 150
    ids = sorted(set(known) | set(range(1, top + 1)))
    log(f"services: {len(known)} ids listed in trees (max {known[-1] if known else '?'}); probing 1..{top}")

    async def one(sid: int, lang: str):
        url = f"{C.BASE}/{lang}/AdministrativeServices/details/{sid}"
        r = await f.get(url)
        if not r.ok:
            return sid, lang, url, None, r
        return sid, lang, url, P.parse_service(r.text, url), r

    results = await gather_limited([one(i, l) for i in ids for l in ("ar", "en")], 60)
    by_id: Dict[int, Dict] = {}
    for sid, lang, url, rec, r in results:
        if rec is None:
            continue
        by_id.setdefault(sid, {})[lang] = (url, rec, r)
    out = []
    for sid in sorted(by_id):
        ar = by_id[sid].get("ar")
        en = by_id[sid].get("en")
        prim = (ar or en)[1]
        sec = (en or ar)[1]

        def pick(field, default=None):
            v = prim.get(field)
            if v in (None, "", []):
                v = sec.get(field)
            return v if v not in (None, "") else default

        form_urls = []
        for src in (prim, sec):
            for fu in src.get("form_urls", []):
                if fu["url"] not in [x["url"] for x in form_urls]:
                    form_urls.append(fu)
        m = meta.get(str(sid), {})
        rec = {
            "id": sid,
            "url_ar": ar[0] if ar else None,
            "url_en": en[0] if en else None,
            "title_ar": ar[1]["title"] if ar else None,
            "title_en": en[1]["title"] if en else None,
            "eligibility": pick("eligibility", ""),
            "eligibility_items": pick("eligibility_items", []),
            "documents": pick("documents", []),
            "steps": pick("steps", []),
            "responsible_unit": pick("responsible_unit", ""),
            "directorate": pick("directorate", ""),
            "office_address": pick("office_address", ""),
            "email": pick("email", ""),
            "hours": pick("hours", ""),
            "fees": pick("fees", ""),
            "duration": pick("duration", ""),
            "form_number": pick("form_number", ""),
            "form_urls": [x["url"] for x in form_urls],
            "form_labels": [x["label"] for x in form_urls],
            "related_links": sorted(set(prim.get("links", [])) | set(sec.get("links", []))),
            "apply_online": bool(prim.get("apply_online") or sec.get("apply_online")),
            "track_transaction": bool(prim.get("track_transaction") or sec.get("track_transaction")),
            "department_ar": m.get("department_ar", ""),
            "department_en": m.get("department_en", ""),
            "listing_unit": m.get("listing_unit", ""),
            "listing_section": m.get("listing_section", ""),
            "listing_number": m.get("listing_number", ""),
            "in_public_listing": str(sid) in meta,
            "fields_ar": ar[1]["fields"] if ar else {},
            "fields_en": en[1]["fields"] if en else {},
            "fetched_at": now_iso(),
        }
        out.append(rec)
        for lang_rec in (ar, en):
            if lang_rec:
                st.add_page_from_html(lang_rec[0], lang_rec[2].text, section="service", extra={"service_id": sid})
        for fu in form_urls:
            st.queue_attachment(fu["url"], (ar or en)[0], fu["label"], None, "service")
    path = C.STRUCT / "services.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"services: wrote {len(out)} services -> {path.relative_to(C.ROOT)} ({f.stats()})")


# =========================================================================== 2. facilities

FAC_COLS = ["name_en", "name_ar", "type", "caza", "phone", "investment_auth_no", "url"]


async def _facility_pages(f: Fetcher, lang: str, ftype: str) -> List[Dict]:
    base = f"{C.BASE}/{lang}/HealthFacilities/index/3/188/{ftype}/limit:100"
    first = await f.get(base, ajax=True)
    if not first.ok:
        return []
    n = P.max_page(first.text)
    rows = P.parse_facility_rows(first.text, lang)
    rest = await gather_limited([f.get(f"{base}/page:{p}", ajax=True) for p in range(2, n + 1)], 40)
    for r in rest:
        if r.ok:
            rows.extend(P.parse_facility_rows(r.text, lang))
    log(f"facilities: {lang} type={ftype or 'all'} pages={n} rows={len(rows)}")
    return rows


async def step_facilities(f: Fetcher, st: Stores) -> None:
    log("facilities: AJAX endpoint /{lang}/HealthFacilities/index/3/188/{type}/limit:100/page:N")
    by_id: Dict[str, Dict] = {}
    # English: all + per type (per-type pass protects against unstable ordering between pages)
    for ftype in ["0"] + list(C.FACILITY_TYPES_EN):
        for row in await _facility_pages(f, "en", ftype):
            fid = row["facility_id"] or row["url"]
            cur = by_id.setdefault(fid, {})
            for k, v in row.items():
                if k != "lang" and v and not cur.get(k):
                    cur[k] = v
            if ftype != "0":
                cur["type_id"] = ftype
    for ftype in ["0"]:  # Arabic pass only adds type_ar / url_ar
        for row in await _facility_pages(f, "ar", ftype):
            fid = row["facility_id"] or row["url"]
            cur = by_id.setdefault(fid, {})
            cur.setdefault("type_ar", row["type"])
            cur.setdefault("url_ar", row["url"])
            for k in ("name_en", "name_ar", "caza", "phone", "investment_auth_no", "facility_id"):
                if row.get(k) and not cur.get(k):
                    cur[k] = row[k]
            if not cur.get("type"):
                cur["type"] = C.FACILITY_TYPES_EN.get(ftype, "") if ftype != "0" else ""
    rows = sorted(by_id.values(), key=lambda r: (r.get("type", ""), r.get("caza", ""), r.get("name_en", "")))
    path = C.STRUCT / "facilities.csv"
    write_csv(path, rows, FAC_COLS + ["facility_id", "type_id", "type_ar", "url_ar"])
    log(f"facilities: wrote {len(rows)} facilities -> {path.relative_to(C.ROOT)} ({f.stats()})")


# =========================================================================== 3. drugs

DRUG_COLS = ["atc", "brand_name", "brand_or_generic", "ingredients", "dosage", "form", "price", "url"]


async def step_drugs(f: Fetcher, st: Stores) -> None:
    log("drugs: AJAX endpoint /en/Drugs/index/3/4848/limit:100/page:N/sort:Drug.id/direction:ASC")
    by_id: Dict[str, Dict] = {}
    for sort in ("Drug.id", "Drug.brand_name"):
        base = f"{C.BASE}/en/Drugs/index/3/4848/limit:100"
        first = await f.get(f"{base}/page:1/sort:{sort}/direction:ASC", ajax=True)
        if not first.ok:
            continue
        n = P.max_page(first.text)
        pages = [first] + await gather_limited(
            [f.get(f"{base}/page:{p}/sort:{sort}/direction:ASC", ajax=True) for p in range(2, n + 1)], 40)
        cnt = 0
        for r in pages:
            if r.ok:
                for row in P.parse_drug_rows(r.text):
                    cnt += 1
                    by_id.setdefault(row["drug_id"] or row["url"], row)
        # two orderings, unioned by drug id: protects against unstable paging (cheap, ~60 requests each)
        log(f"drugs: sort={sort} pages={n} rows={cnt} unique so far={len(by_id)}")
    rows = sorted(by_id.values(), key=lambda r: (r["brand_name"], r["dosage"]))
    path = C.STRUCT / "drugs.csv"
    write_csv(path, rows, DRUG_COLS + ["drug_id", "price_lbp"])
    log(f"drugs: wrote {len(rows)} drugs -> {path.relative_to(C.ROOT)} ({f.stats()})")


# =========================================================================== 4. free medicines / AMAN / tenders

FREE_MED_PAGES = ["/ar/Pages/3/77224", "/en/Pages/3/77224"]
FREE_MED_KEYWORDS = re.compile(r"aman|tender|allocation|free|medication|meds|مجان|مناقص|أدوية|ادوية", re.I)


async def step_free_meds(f: Fetcher, st: Stores) -> None:
    from .steps_files import download_one, excel_to_frames  # local import to avoid cycles
    import pandas as pd

    log("free_meds: reading /Pages/3/77224 (ar+en) and any AMAN/tender/allocation Excel already discovered")
    xls: Dict[str, Dict] = {}
    for path in FREE_MED_PAGES:
        url = C.BASE + path
        r = await f.get(url)
        if not r.ok:
            continue
        st.add_page_from_html(url, r.text, section="page")
        _, atts = P.extract_links(r.text, url)
        for a, label in atts:
            if a.lower().split("?")[0].endswith((".xlsx", ".xls")):
                xls.setdefault(a, {"label": label, "source": url})
    # any other Excel in the attachment queue that looks like a medicines list
    if C.ATTACH_QUEUE.exists():
        for line in C.ATTACH_QUEUE.open(encoding="utf-8"):
            q = json.loads(line)
            u = q["url"]
            name = P.unquote(u.rsplit("/", 1)[-1])
            if u.lower().endswith((".xlsx", ".xls")) and FREE_MED_KEYWORDS.search(name + " " + (q.get("label") or "")):
                xls.setdefault(u, {"label": q.get("label", ""), "source": q.get("source_page_url", "")})
    frames = []
    for u, info in xls.items():
        st.queue_attachment(u, info["source"], info["label"], None, "page")
        rec = await download_one(f, u, info["source"])
        if not rec or not rec.get("local_path"):
            continue
        fname = P.unquote(u.rsplit("/", 1)[-1])
        for sheet, df in excel_to_frames(C.ROOT / rec["local_path"]):
            df = df.copy()
            df.insert(0, "source_sheet", sheet)
            df.insert(0, "source_file", fname)
            df["source_url"] = u
            df["source_page_label"] = info["label"]
            frames.append(df)
            log(f"free_meds: {fname} [{sheet}] {len(df)} rows, cols={list(df.columns)[2:8]}")
    path = C.STRUCT / "free_meds.csv"
    if frames:
        out = pd.concat(frames, ignore_index=True, sort=False)
        out.to_csv(path, index=False, encoding="utf-8-sig")
        log(f"free_meds: wrote {len(out)} rows from {len(xls)} files -> {path.relative_to(C.ROOT)}")
    else:
        log("free_meds: no Excel rows parsed (see failed_urls.txt)")
