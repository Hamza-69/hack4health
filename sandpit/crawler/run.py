"""Wasel MoPH crawler - command line.

    python -m crawler.run priority     # steps 1-4: services, facilities, drugs, free_meds (~20-30 min)
    python -m crawler.run fast         # today: 2025-26 news + capped site crawl + key attachments (~20-30 min)
    python -m crawler.run full         # everything else, in priority order (overnight)
    python -m crawler.run all          # priority + full
    python -m crawler.run services drugs report   # any list of single steps

Single steps: services facilities drugs free_meds pages page_attachments news_recent news_old
              news facility_details drug_details attachments extract ocr retry_failed hotlines
              rules_candidates report

ocr needs OPENAI_API_KEY in the environment.

Everything is resumable: re-running skips URLs already fetched (data/state/cache) and records already written.
"""
from __future__ import annotations

import asyncio
import sys
import time

from . import config as C
from .fetch import Fetcher
from .progress import log
from .store import Stores
from . import steps_structured as S1
from . import steps_crawl as S2
from . import steps_files as F
from . import post
from . import clean

# "fast": what we need today in ~20-30 min - 2025-26 news, a capped site crawl, the useful attachments
FAST = ["news_2025", "pages_fast", "attachments_fast", "retry_failed", "extract", "ocr", "hotlines", "rules_candidates", "clean", "report"]
PRIORITY = ["services", "facilities", "drugs", "free_meds", "hotlines", "clean", "report"]
FULL = ["pages", "page_attachments", "news_recent", "news_old", "attachments", "facility_details", "drug_details",
        "free_meds", "retry_failed", "extract", "ocr", "hotlines", "rules_candidates", "clean", "report"]

NET_STEPS = {
    "services": S1.step_services,
    "facilities": S1.step_facilities,
    "drugs": S1.step_drugs,
    "free_meds": S1.step_free_meds,
    "pages": S2.step_pages,
    "page_attachments": lambda f, st: F.step_attachments(f, st, sections=("page", "service", "other")),
    "news_recent": lambda f, st: S2.step_news(f, st, since="2024-01-01"),
    "news_old": lambda f, st: S2.step_news(f, st, until="2024-01-01"),
    "news": S2.step_news,
    "news_2025": lambda f, st: S2.step_news(f, st, since="2025-01-01"),
    "pages_fast": lambda f, st: S2.step_pages(f, st, max_pages=int(__import__("os").environ.get("WASEL_MAX_PAGES", "700"))),
    "attachments_fast": lambda f, st: F.step_attachments(f, st, max_files=int(__import__("os").environ.get("WASEL_MAX_FILES", "400")),
                                                        exts=(".pdf", ".xlsx", ".xls", ".docx"), since="2025-01-01"),
    "attachments": F.step_attachments,
    "facility_details": S2.step_facility_details,
    "drug_details": S2.step_drug_details,
    "retry_failed": S2.step_retry_failed,
}
LOCAL_STEPS = {
    "extract": F.step_extract,
    "ocr": F.step_ocr,
    "hotlines": post.step_hotlines,
    "rules_candidates": post.step_rules_candidates,
    "report": post.step_report,
    "clean": clean.step_clean,
}


async def run(steps):
    async with Fetcher() as f:
        st = Stores()
        try:
            for s in steps:
                t0 = time.time()
                log(f"=== step {s} ===")
                try:
                    if s in NET_STEPS:
                        await NET_STEPS[s](f, st)
                    elif s in LOCAL_STEPS:
                        LOCAL_STEPS[s]()
                    else:
                        log(f"unknown step {s}")
                except Exception as e:  # keep going - one broken step must not kill the overnight crawl
                    import traceback
                    traceback.print_exc()
                    log(f"!!! step {s} crashed: {type(e).__name__}: {e} - continuing")
                log(f"=== step {s} done in {time.time() - t0:.0f}s ({f.stats()}) ===")
        finally:
            st.close()


def main(argv):
    if not argv:
        print(__doc__)
        return
    steps = []
    for a in argv:
        if a == "priority":
            steps += PRIORITY
        elif a == "full":
            steps += FULL
        elif a == "fast":
            steps += FAST
        elif a == "all":
            steps += PRIORITY + FULL
        else:
            steps.append(a)
    log(f"Wasel crawler starting: {steps} -> {C.DATA}")
    asyncio.run(run(steps))


if __name__ == "__main__":
    main(sys.argv[1:])
