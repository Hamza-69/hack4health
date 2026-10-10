"""Append-only JSONL stores with de-duplication (safe to resume)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Iterable, Optional

from bs4 import BeautifulSoup

from . import config as C
from . import parse as P


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


class JsonlSet:
    def __init__(self, path: Path, key_field: str) -> None:
        self.path = path
        self.key_field = key_field
        self.keys = set()
        if path.exists():
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    try:
                        self.keys.add(json.loads(line)[key_field])
                    except Exception:
                        pass
        self.fh = path.open("a", encoding="utf-8")

    def __contains__(self, k) -> bool:
        return k in self.keys

    def add(self, rec: Dict) -> bool:
        k = rec[self.key_field]
        if k in self.keys:
            return False
        self.keys.add(k)
        self.fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.fh.flush()
        return True

    def close(self) -> None:
        self.fh.close()


class Stores:
    """pages.jsonl (key = content key) + attachment queue (key = url)."""

    def __init__(self) -> None:
        self.pages = JsonlSet(C.PAGES_JSONL, "dedup_key")
        self.attq = JsonlSet(C.ATTACH_QUEUE, "url")

    def close(self) -> None:
        self.pages.close()
        self.attq.close()

    def has_page(self, url: str) -> bool:
        return P.content_key(url)[0] in self.pages

    def add_page_from_html(self, url: str, html: str, section: Optional[str] = None,
                           extra: Optional[Dict] = None, final_url: Optional[str] = None) -> Optional[Dict]:
        key, cid = P.content_key(url)
        if key in self.pages:
            return None
        doc = P.soup(html)
        node = P.clean_main(doc)
        text = P.block_text(node) if node is not None else ""
        _, atts = P.extract_links(html if node is None else str(node), url)
        rec = {
            "url": url,
            "canonical_url": canonical(url),
            "lang": P.url_lang(url),
            "content_id": cid,
            "section": section or P.section_of(url),
            "title": P.page_title(doc),
            "date": P.page_date(doc),
            "text": text,
            "attachments": [a for a, _ in atts],
            "fetched_at": now_iso(),
            "dedup_key": key,
        }
        if extra:
            rec.update(extra)
        if not rec["date"] and rec.get("listing_date"):
            rec["date"] = rec["listing_date"]
        self.pages.add(rec)
        for a, label in atts:
            self.attq.add({"url": a, "label": label, "source_page_url": url, "lang": rec["lang"], "section": rec["section"]})
        return rec

    def queue_attachment(self, url: str, source: str, label: str = "", lang: Optional[str] = None, section: str = "") -> None:
        self.attq.add({"url": url, "label": label, "source_page_url": source, "lang": lang, "section": section})


def canonical(url: str) -> str:
    """One stable URL per content item (news items -> /{lang}/Media/view/{id})."""
    key, cid = P.content_key(url)
    parts = key.split(":")
    if len(parts) >= 3 and parts[1] == "item":
        return f"{C.BASE}/{parts[0]}/Media/view/{cid}"
    if len(parts) >= 3 and parts[1] == "service":
        return f"{C.BASE}/{parts[0]}/AdministrativeServices/details/{cid}"
    return url
