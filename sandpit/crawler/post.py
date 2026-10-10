"""Post-processing: hotlines.csv, rules_candidates.csv (input for the current-rules sheet), report.md."""
from __future__ import annotations

import collections
import csv
import json
import random
import re
from pathlib import Path
from typing import Dict, List

from . import config as C
from .progress import log


def iter_pages():
    if C.PAGES_JSONL.exists():
        with C.PAGES_JSONL.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    yield json.loads(line)
                except Exception:
                    continue


# --------------------------------------------------------------------------- hotlines

KNOWN_HOTLINES = [
    ("1214", "MoPH hotline (الخط الساخن لوزارة الصحة العامة)"),
    ("1787", "Hotline for health services for displaced Lebanese (الخط الساخن للخدمات الصحية للنازحين)"),
]
HOTLINE_CTX = re.compile(r"hotline|hot line|call center|call centre|الخط الساخن|خط ساخن|الخطّ الساخن|رقم الطوارئ|"
                         r"الاتصال على الرقم|الاتصال بالرقم|الرقم المجاني|toll[- ]free|call\s+\d{3,4}", re.I)
SHORT_NUM = re.compile(r"(?<![\d/.\-])(1\d{2,3}|14\d|112|125|140|175)(?![\d/.\-])")


def step_hotlines() -> None:
    hits: Dict[str, Dict] = {}
    for p in iter_pages():
        text = p.get("text") or ""
        for m in HOTLINE_CTX.finditer(text):
            window = text[max(0, m.start() - 160): m.end() + 160]
            window = re.sub(r"\s+", " ", window)
            from .parse import to_ascii_digits
            for n in SHORT_NUM.findall(to_ascii_digits(window)):
                d = p.get("date") or ""
                cur = hits.get(n)
                # keep the most recent page as the source
                if cur is None or d > (cur["source_date"] or ""):
                    hits[n] = {"number": n, "purpose": window.strip()[:300], "source_url": p.get("canonical_url") or p["url"],
                               "source_date": d, "lang": p.get("lang"), "mentions": (cur or {}).get("mentions", 0) + 1}
                else:
                    cur["mentions"] += 1
    rows = []
    for n, purpose in KNOWN_HOTLINES:
        h = hits.pop(n, None)
        rows.append({"number": n, "purpose": purpose, "source_url": (h or {}).get("source_url", C.BASE + "/ar/"),
                     "source_date": (h or {}).get("source_date", ""), "mentions": (h or {}).get("mentions", 0),
                     "context": (h or {}).get("purpose", "site header on every page")})
    for h in sorted(hits.values(), key=lambda x: -x["mentions"]):
        rows.append({"number": h["number"], "purpose": "", "source_url": h["source_url"], "source_date": h["source_date"],
                     "mentions": h["mentions"], "context": h["purpose"]})
    path = C.STRUCT / "hotlines.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["number", "purpose", "source_url", "source_date", "mentions", "context"])
        w.writeheader()
        w.writerows(rows)
    log(f"hotlines: {len(rows)} numbers -> {path.relative_to(C.ROOT)} (rows after the first two need a human 'purpose')")


# --------------------------------------------------------------------------- current-rules candidates

RULE_TOPICS = {
    "hospitalization_coverage": r"استشفاء|الاستشفاء|hospitali[sz]ation|غير المضمونين|uninsured|على نفقة الوزارة|at the expense of the ministry|السقف العادل|fair ceiling|100\s*%|100 بالمئة|مئة بالمئة",
    "emergency": r"طوارئ|الطوارىء|emergency|الحالات الطارئة|العمليات الطارئة",
    "transplant": r"زرع|زراعة|transplant|نقي العظم|bone marrow|الكلى|kidney",
    "open_heart": r"القلب المفتوح|open[- ]heart|جراحة القلب",
    "dialysis": r"غسيل الكلى|غسل الكلى|dialysis|96\s*\$|\$\s*96|96 دولار",
    "mammography": r"ماموغرافي|الماموغرافي|mammograph|سرطان الثدي|breast cancer",
    "cancer_drugs": r"أدوية السرطان|الأدوية السرطانية|cancer (drugs|medication)|oncology|الأمراض السرطانية|الأدوية المستعصية|الأمراض المستعصية",
    "ms": r"التصلب اللويحي|التصلّب اللويحي|multiple sclerosis|\bMS\b",
    "haemophilia": r"هيموفيليا|الناعور|نزف الدم|ha?emophilia|bleeding disorder",
    "thalassaemia": r"تلاسيميا|الثلاسيميا|thalass",
    "humira": r"هيوميرا|humira|adalimumab|أداليموماب",
    "displaced": r"النازحين|نازح|displaced|الحرب|العدوان|war-affected",
    "hotline": r"الخط الساخن|hotline|1214|1787",
    "medicine_request": r"طلب أدوية|طلب الحصول على مساعدة أدوية|مركز توزيع الأدوية|الكرنتينا|Karantina|AMAN|أمان|منصة",
    "vaccination": r"لقاح|تلقيح|vaccin",
    "primary_care": r"الرعاية الصحية الأولية|primary health care|PHC|مراكز الرعاية",
}
RULE_RX = {k: re.compile(v, re.I) for k, v in RULE_TOPICS.items()}
POLICY_RX = re.compile(r"تغطية|يغطي|تتحمل|على نفقة|مجان|مجاناً|مجانا|free|cover|coverage|ابتداء|اعتباراً|اعتبارا|effective|تعميم|قرار|decision|circular|يحق|eligible|ملزمة|must|إلزام", re.I)


def step_rules_candidates(since: str = "2025-01-01") -> None:
    rows = []
    for p in iter_pages():
        d = p.get("date") or ""
        if d < since:
            continue
        text = (p.get("title") or "") + "\n" + (p.get("text") or "")
        topics = [k for k, rx in RULE_RX.items() if rx.search(text)]
        if not topics or not POLICY_RX.search(text):
            continue
        # best snippet: first sentence that hits a topic and a policy word
        snippet = ""
        for sent in re.split(r"(?<=[.!؟?\n])\s+", p.get("text") or ""):
            if POLICY_RX.search(sent) and any(RULE_RX[t].search(sent) for t in topics):
                snippet = sent.strip()[:400]
                break
        rows.append({"source_date": d, "lang": p.get("lang"), "section": p.get("section"), "title": p.get("title"),
                     "topics": ";".join(topics), "snippet": snippet, "source_url": p.get("canonical_url") or p["url"],
                     "n_chars": len(p.get("text") or "")})
    rows.sort(key=lambda r: r["source_date"], reverse=True)
    path = C.STRUCT / "rules_candidates.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["source_date"])
        w.writeheader()
        w.writerows(rows)
    log(f"rules_candidates: {len(rows)} pages since {since} -> {path.relative_to(C.ROOT)}")


# --------------------------------------------------------------------------- report

def _csv_rows(p: Path) -> int:
    if not p.exists():
        return 0
    with p.open(encoding="utf-8-sig") as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


def step_report() -> None:
    pages = list(iter_pages())
    by = collections.Counter((p.get("section"), p.get("lang")) for p in pages)
    news_dates = sorted(p["date"] for p in pages if p.get("section") == "news" and p.get("date"))
    files = [json.loads(l) for l in C.FILES_JSONL.open(encoding="utf-8")] if C.FILES_JSONL.exists() else []
    ftypes = collections.Counter(f.get("type") for f in files)
    notes = collections.Counter((f.get("extract_note") or "").split(":")[0] for f in files if f.get("extract_note"))
    scanned = [f for f in files if f.get("extract_note") == "scanned_or_no_text"]
    failed = []
    if C.FAILED_TXT.exists():
        failed = sorted({l.split("\t")[0] for l in C.FAILED_TXT.open(encoding="utf-8") if l.strip()})
    empty_text = [p for p in pages if len(p.get("text") or "") < 40]
    services_n = 0
    sp = C.STRUCT / "services.json"
    if sp.exists():
        services_n = len(json.loads(sp.read_text(encoding="utf-8")))
    L = []
    L.append("# Wasel data crawl report\n")
    L.append(f"Generated by `python -m crawler.run report`. Source: https://www.moph.gov.lb (ar + en).\n")
    L.append("## Pages (data/raw/pages.jsonl)\n")
    L.append(f"Total records: **{len(pages)}**\n")
    L.append("| section | ar | en | total |\n|---|---|---|---|")
    for sec in sorted({s for s, _ in by}, key=str):
        a, e = by.get((sec, "ar"), 0), by.get((sec, "en"), 0)
        L.append(f"| {sec} | {a} | {e} | {a + e + by.get((sec, None), 0)} |")
    if news_dates:
        L.append(f"\nNews date range: **{news_dates[0]} → {news_dates[-1]}** "
                 f"({sum(1 for d in news_dates if d >= '2024-01-01')} items from 2024 onward)\n")
    L.append("## Attachments (data/raw/files.jsonl)\n")
    L.append(f"Downloaded: **{len(files)}** files, {sum(f.get('size', 0) for f in files) / 1e6:.0f} MB\n")
    L.append("| type | count |\n|---|---|")
    for t, n in ftypes.most_common():
        L.append(f"| {t} | {n} |")
    L.append(f"\nWith extracted text/CSV: {sum(1 for f in files if f.get('text_path'))}. "
             f"Scanned PDFs with no text layer (need OCR): {len(scanned)}. Other extraction notes: {dict(notes)}\n")
    L.append("## Structured files (data/structured/)\n")
    L.append("| file | rows |\n|---|---|")
    L.append(f"| services.json | {services_n} |")
    for name in ("facilities.csv", "facilities_clean.csv", "facilities_details.csv", "drugs.csv", "drugs_clean.csv",
                 "drugs_details.csv", "free_meds.csv", "free_meds_unified.csv",
                 "hotlines.csv", "rules_candidates.csv", "current_rules.csv"):
        L.append(f"| {name} | {_csv_rows(C.STRUCT / name)} |")
    L.append("\n## AJAX endpoints used\n")
    L.append("- Facility Locator: `GET /{lang}/HealthFacilities/index/3/188/{type}/limit:100/page:{N}` "
             "(type 0 = all, 1-8 = per type; returns an HTML fragment `<table>`; `limit` is capped at 100 by the server)")
    L.append("- Drugs DB: `GET /en/Drugs/index/3/4848/limit:100/page:{N}/sort:Drug.id/direction:ASC` "
             "(and the same with `sort:Drug.brand_name` as a cross-check, unioned by drug id)")
    L.append("- News: `GET /{lang}/DynamicPages/listing/16/limit:100/page:{N}`")
    L.append("- Administrative services tree: `GET /{lang}/AdministrativeServices/view/{dept}/{0|1}` "
             "(0 = by department, 1 = by category) + id probe of `/AdministrativeServices/details/{id}`")
    L.append("- Laws tree: `GET /{lang}/Laws/view/{category}`")
    L.append("\n## Failed URLs still failing\n")
    L.append(f"{len(failed)} (see data/failed_urls.txt)\n")
    for u in failed[:40]:
        L.append(f"- {u}")
    L.append("\n## Known gaps\n")
    L.append(f"- Pages with (almost) no extracted text: {len(empty_text)} (usually pure link lists or image-only pages)")
    L.append(f"- Scanned PDFs without text layer: {len(scanned)} (first few below)")
    for f in scanned[:10]:
        L.append(f"  - {f['url']}")
    L.append("- `/files/*` is disallowed by robots.txt, so images and `/files/media/docs/*.pdf` law scans were not downloaded.")
    L.append("- Online application, Track Transaction and login areas were not touched (no forms submitted).")
    L.append("\n## 10 random spot-checks\n")
    rnd = random.Random(42)
    sample = rnd.sample(pages, min(10, len(pages))) if pages else []
    for p in sample:
        snippet = re.sub(r"\s+", " ", (p.get("text") or ""))[:200]
        L.append(f"- **{p.get('title')}** ({p.get('section')}, {p.get('lang')}, {p.get('date') or 'no date'})  \n"
                 f"  {p['url']}  \n  > {snippet}")
    L.append("\n## Decisions taken without asking\n")
    L.append("- Arabic side is the primary source for services (more complete); English values fill gaps.")
    L.append("- The drugs listing was taken from the English side only (the Arabic side shows the same English rows).")
    L.append("- Sorted listing URLs (`sort:`) are used *only* for the drugs endpoint to get a stable order; the "
             "general crawler never follows sort/filter variants.")
    L.append("- Facility and drug *detail* pages were crawled as extras (address, beds, subsidy %, agent...).")
    L.append("- CSV files are written as UTF-8 with BOM so Excel shows Arabic correctly.")
    C.REPORT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    log(f"report: wrote {C.REPORT_MD.relative_to(C.ROOT)}")
