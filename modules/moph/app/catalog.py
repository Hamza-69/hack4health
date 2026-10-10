"""Search over everything the module knows. Pure Python over plain rows, so it is testable without a
database: tools build it from the tables (get_catalog), tests from the files (app.ingest.load_files).

Every result carries its official source URL, and dates where the source has them, so the agent
can cite and date what it says.
"""

import asyncio
from collections import defaultdict
from typing import Literal

from rapidfuzz import fuzz, process
from sqlalchemy import select

from app.bm25 import BM25
from app.text import is_arabic, normalize

FacilityType = Literal[
    "pharmacy",
    "government_hospital",
    "private_hospital",
    "any_hospital",
    "primary_care_center",
    "radiology_lab",
    "physiotherapy_center",
    "dental_lab",
    "nursery",
]
FACILITY_TYPES: dict[str, set[str]] = {
    "pharmacy": {"Pharmacies"},
    "government_hospital": {"Governmental Hospitals"},
    "private_hospital": {"Private Hospitals"},
    "any_hospital": {"Governmental Hospitals", "Private Hospitals"},
    "primary_care_center": {"PHC Centers"},
    "radiology_lab": {"Radiology Lab"},
    "physiotherapy_center": {"Physiotherapy Centers"},
    "dental_lab": {"Dental Lab"},
    "nursery": {"Nurseries"},
}

FREE_LISTS = {
    "aman_intractable_diseases": "AMAN list: medicines for intractable diseases that MoPH provides (file dated 2024-10-23)",
    "tender_388_2024": "Tender 388/2024 list of medicines MoPH provides (2024)",
    "allocation_free": "Allocation list of medicines MoPH provides (2024)",
}

STRONG = 0.5  # share of query terms a result must contain to count as a strong match


def _strength(coverage: float) -> str:
    return "strong" if coverage >= STRONG else "weak"


def _lines(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    return [v.strip() for v in str(value).splitlines() if v.strip()]


def _price(value: float | None) -> str | None:
    return f"{value:,.0f} LBP" if value else None


class Catalog:
    def __init__(self, rows: dict):
        self.data_date: str = rows.get("data_date") or ""
        self.services = sorted(rows["services"], key=lambda s: s["id"])
        self.pages = rows["pages"]
        self.drugs = rows["drugs"]
        self.free_meds = rows["free_meds"]
        self.facilities = rows["facilities"]
        self.facts = [f for f in rows["facts"] if f.get("active", True)]

        self._services_index = BM25([self._service_doc(s["data"]) for s in self.services])
        self._pages_index = BM25([f"{p['title']}\n{p['title']}\n{p['text']}" for p in self.pages])
        self._facts_index = BM25(
            [f"{f['topic'].replace('_', ' ')}\n{f['rule']}\n{f['who_is_eligible']}\n{f['where']}" for f in self.facts]
        )

        self._brands = [normalize(d["brand_name"]) for d in self.drugs]
        self._ingredients = [normalize(d["ingredients"]) for d in self.drugs]
        self._by_equiv = defaultdict(list)
        for d in self.drugs:
            if d["equiv_key"] and d["price_lbp"]:
                self._by_equiv[d["equiv_key"]].append(d)

        self._areas = sorted(
            {v for f in self.facilities for v in (f["governorate"], f["caza_en"], f["caza_ar"]) if v}
        )

    # Services

    @staticmethod
    def _service_doc(s: dict) -> str:
        title = s.get("title_ar") or ""
        parts = [title, title, title, s.get("department_ar"), s.get("department_en"), s.get("listing_section"),
                 s.get("listing_unit"), s.get("responsible_unit"), s.get("eligibility"),
                 *_lines(s.get("documents")), *_lines(s.get("form_labels")), *_lines(s.get("steps"))]
        return "\n".join(p for p in parts if p)

    @staticmethod
    def service_card(s: dict) -> dict:
        labels, urls = _lines(s.get("form_labels")), _lines(s.get("form_urls"))
        if labels and len(labels) == len(urls):
            forms = [{"name": n, "url": u} for n, u in zip(labels, urls)]
        else:
            forms = [{"url": u} for u in urls]
        card = {
            "service_id": s["id"],
            "title": s.get("title_ar"),
            "who_is_eligible": _lines(s.get("eligibility_items") or s.get("eligibility")),
            "required_documents": _lines(s.get("documents")),
            "steps": _lines(s.get("steps")),
            "fees": s.get("fees"),
            "processing_time": s.get("duration"),
            "form_number": s.get("form_number"),
            "forms": forms[:15],
            "apply_online": s.get("apply_online") or False,
            "office": {
                "directorate": s.get("directorate"),
                "unit": s.get("responsible_unit"),
                "address": s.get("office_address"),
                "email": s.get("email"),
                "hours": s.get("hours"),
            },
            "official_page": s.get("url_ar"),
            "official_page_en": s.get("url_en") if s.get("english_available") else None,
        }
        card["office"] = {k: v for k, v in card["office"].items() if v}
        return {k: v for k, v in card.items() if v not in (None, "", [], {})}

    def search_services(self, query: str, limit: int = 3) -> list[dict]:
        out = []
        for hit in self._services_index.search(query, limit):
            card = self.service_card(self.services[hit.index]["data"])
            out.append({"match": _strength(hit.coverage), **card})
        return out

    def get_service(self, service_id: int) -> dict | None:
        for s in self.services:
            if s["id"] == service_id:
                return self.service_card(s["data"])
        return None

    # Site pages and news

    def search_pages(self, query: str, limit: int = 5) -> list[dict]:
        hits = self._pages_index.search(query, limit * 6)
        # Prefer recent items a little: rules and announcements change.
        ranked = sorted(
            hits,
            key=lambda h: h.score * (1.25 if (self.pages[h.index]["date"] or "") >= "2025" else 1),
            reverse=True,
        )
        out, per_url = [], defaultdict(int)
        for hit in ranked:
            p = self.pages[hit.index]
            if per_url[p["url"]] >= 2:
                continue
            per_url[p["url"]] += 1
            out.append(
                {
                    "match": _strength(hit.coverage),
                    "title": p["title"],
                    "date": p["date"],
                    "kind": p["section"],
                    "text": p["text"],
                    "url": p["url"],
                }
            )
            if len(out) == limit:
                break
        return out

    # Curated facts

    @staticmethod
    def fact_card(f: dict) -> dict:
        card = {
            "topic": f["topic"],
            "rule": f["rule"],
            "who_is_eligible": f["who_is_eligible"],
            "where": f["where"],
            "effective": f["effective_date"],
            "confidence": f["confidence"],
            "editor_note": f["note"],
            "source_url": f["source_url"],
            "source_date": f["source_date"],
        }
        return {k: v for k, v in card.items() if v}

    def search_facts(self, query: str | None, limit: int = 8) -> list[dict]:
        if not query or not query.strip():
            return [self.fact_card(f) for f in self.facts]
        return [
            {"match": _strength(h.coverage), **self.fact_card(self.facts[h.index])}
            for h in self._facts_index.search(query, limit)
        ]

    def contacts(self) -> list[dict]:
        hotlines = [{"contact": f["rule"], "source_url": f["source_url"]} for f in self.facts if f["topic"] == "hotline"]
        return hotlines or [{"contact": "1214: Ministry of Public Health hotline"}]

    # Drugs

    def _drug_card(self, d: dict) -> dict:
        cheaper = [
            e for e in self._by_equiv.get(d["equiv_key"], [])
            if e["id"] != d["id"] and d["price_lbp"] and e["price_lbp"] < d["price_lbp"]
        ]
        cheaper.sort(key=lambda e: e["price_lbp"])
        card = {
            "brand_name": d["brand_name"],
            "type": "generic" if d["generic"] else "brand",
            "ingredients": d["ingredients"],
            "dosage": d["dosage"],
            "form": d["form"],
            "public_price": _price(d["price_lbp"]) or "no price listed",
            "on_moph_free_list": d["on_free_list"],
            "cheaper_equivalents": [
                {"brand_name": e["brand_name"], "dosage": e["dosage"], "form": e["form"],
                 "public_price": _price(e["price_lbp"]), "url": e["url"]}
                for e in cheaper[:3]
            ],
            "url": d["url"],
        }
        return {k: v for k, v in card.items() if v not in (None, "", [])}

    def lookup_drug(self, name: str, limit: int = 5) -> dict:
        q = normalize(name).strip()
        if not q:
            return {"drugs": [], "free_lists": []}
        scores: dict[int, float] = {}
        for i, (brand, ingredients) in enumerate(zip(self._brands, self._ingredients)):
            if brand == q:
                scores[i] = 100
            elif brand.startswith(q):
                scores[i] = 96
            elif q in brand:
                scores[i] = 92
            elif q in ingredients:
                scores[i] = 90
        exact = set(scores)
        if len(q) >= 4:
            for _, score, i in process.extract(q, self._brands, scorer=fuzz.WRatio, limit=30, score_cutoff=82):
                scores[i] = max(scores.get(i, 0), score - 10)  # a typo match ranks below exact ones
        ranked = sorted(scores, key=lambda i: (-scores[i], self._brands[i], self.drugs[i]["dosage"]))
        drugs = [
            {"match": "name" if i in exact else "similar_name", **self._drug_card(self.drugs[i])}
            for i in ranked[:limit]
        ]

        free = [
            m for m in self.free_meds
            if q in normalize(m["brand_name"]) or q in normalize(m["composition"])
        ]
        free_lists = [
            {"brand_name": m["brand_name"], "composition": m["composition"], "strength": m["strength"],
             "form": m["form"], "therapeutic_class": m["therapeutic_class"],
             "list": FREE_LISTS.get(m["list_type"], m["list_type"]), "source_url": m["source_url"]}
            for m in free[:limit]
        ]
        return {"drugs": drugs, "more_matches": max(0, len(ranked) - limit), "free_lists": free_lists}

    # Facilities

    def match_areas(self, area: str) -> set[str]:
        q = normalize(area).strip()
        found = {a for a in self._areas if q == normalize(a) or q in normalize(a)}
        if not found and len(q) >= 3:
            found = {a for a, score, _ in process.extract(q, self._areas, processor=normalize,
                                                          scorer=fuzz.WRatio, limit=3, score_cutoff=85)}
        return found

    def find_facilities(
        self, type: FacilityType | None = None, area: str | None = None, name: str | None = None, limit: int = 10
    ) -> dict:
        rows = self.facilities
        if type:
            types = FACILITY_TYPES[type]
            rows = [f for f in rows if f["type"] in types]
        if area:
            areas = self.match_areas(area)
            if not areas:
                return {"total": 0, "facilities": [], "unknown_area": area,
                        "known_areas": sorted({f["governorate"] for f in self.facilities if f["governorate"]})}
            rows = [f for f in rows if {f["governorate"], f["caza_en"], f["caza_ar"]} & areas]
        if name:
            q = normalize(name)
            rows = [f for f in rows if q in normalize(f["name_en"]) or q in normalize(f["name_ar"])]
        rows = sorted(rows, key=lambda f: (f["type"] != "Governmental Hospitals", f["name_ar"]))
        result = {
            "total": len(rows),
            "facilities": [
                {k: v for k, v in {
                    "name": f["name_ar"] if is_arabic(f["name_en"]) or not f["name_en"] else f["name_en"],
                    "name_ar": f["name_ar"],
                    "type": f["type"],
                    "governorate": f["governorate"],
                    "caza": f["caza_en"],
                    "phone": f["phone"],
                    "url": f["url"],
                }.items() if v}
                for f in rows[:limit]
            ],
        }
        if not rows:
            result["note"] = (
                "Nothing matching in our copy of the ministry's Facility Locator. That list is incomplete "
                "(for example it has pharmacies only for Beirut, Mount Lebanon, Bekaa and Baalbek-Hermel), "
                "so this does not mean none exist."
            )
        return result


# The catalog the tools use, built from the module's tables and rebuilt after changes.

_catalog: Catalog | None = None
_lock = asyncio.Lock()


def invalidate() -> None:
    global _catalog
    _catalog = None


async def get_catalog() -> Catalog:
    global _catalog
    async with _lock:
        if _catalog is None:
            _catalog = await _load()
        return _catalog


async def _load() -> Catalog:
    from app.models import Drug, Facility, Fact, FreeMed, IngestRun, Page, Service
    from app.module import module

    def as_dicts(objs) -> list[dict]:
        return [{c.key: getattr(o, c.key) for c in o.__table__.columns} for o in objs]

    async with module.db() as session:
        rows = {
            name: as_dicts(await session.scalars(select(model)))
            for name, model in [("services", Service), ("pages", Page), ("drugs", Drug),
                                ("free_meds", FreeMed), ("facilities", Facility), ("facts", Fact)]
        }
        last = await session.scalar(select(IngestRun).order_by(IngestRun.id.desc()).limit(1))
    rows["data_date"] = last.data_date if last else ""
    return await asyncio.to_thread(Catalog, rows)
