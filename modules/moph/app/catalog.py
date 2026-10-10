"""Search over everything the module knows. Built from plain rows, so it needs no database: tools
build it from the tables (get_catalog), tests from the files (app.ingest.load_files).

Services, site pages, news and documents are searched by meaning in Pinecone (app.search_index);
the catalog turns the matches into results. Drugs and facilities are matched by name and filters.

Every result carries its official source URL, and dates where the source has them, so the agent
can cite and date what it says.
"""

import asyncio
from collections import defaultdict
from datetime import date, timedelta
from typing import Literal

from rapidfuzz import fuzz, process
from sqlalchemy import select

from app import search_index
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

HOTLINES = [
    {"contact": "1214: Ministry of Public Health hotline, also for cancer and intractable-disease medicines",
     "source_url": "https://www.moph.gov.lb/ar/Media/view/82895"},
    {"contact": "1787: questions and complaints about hospital care, e.g. a hospital asking for extra payment (working hours)",
     "source_url": "https://www.moph.gov.lb/ar/Media/view/85973"},
    {"contact": "1564: mental health support line", "source_url": "https://www.moph.gov.lb/ar/Media/view/82829"},
]

STRONG_SIMILARITY = 0.45  # cosine similarity of a "strong" match with text-embedding-3-large
RECENT_DAYS = 548  # site results from the last 18 months rank a little higher: rules change
RECENT_BOOST = 1.1


def _strength(score: float) -> str:
    return "strong" if score >= STRONG_SIMILARITY else "weak"


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
        self.services = {s["id"]: s for s in rows["services"]}
        self.drugs = rows["drugs"]
        self.free_meds = rows["free_meds"]
        self.facilities = rows["facilities"]

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
    def service_text(s: dict) -> str:
        """What gets embedded for a service."""
        parts = [s.get("title_ar"), s.get("department_ar"), s.get("department_en"), s.get("listing_section"),
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

    async def search_services(self, query: str, limit: int = 5) -> list[dict]:
        matches = await search_index.query(search_index.SERVICES, query, limit)
        return [
            {"match": _strength(m.score), **self.service_card(self.services[int(m.metadata["service_id"])]["data"])}
            for m in matches
            if int(m.metadata.get("service_id", -1)) in self.services
        ]

    def get_service(self, service_id: int) -> dict | None:
        s = self.services.get(service_id)
        return self.service_card(s["data"]) if s else None

    # Site pages, news and documents

    @staticmethod
    async def search_site(query: str, limit: int = 5) -> list[dict]:
        matches = await search_index.query(search_index.SITE, query, limit * 6)
        recent = (date.today() - timedelta(days=RECENT_DAYS)).isoformat()
        ranked = sorted(
            matches,
            key=lambda m: m.score * (RECENT_BOOST if m.metadata.get("date", "") >= recent else 1),
            reverse=True,
        )
        out, seen = [], set()
        for m in ranked:
            meta = m.metadata
            # One result per source: its best chunk. A dated announcement appears under several URLs.
            key = (meta.get("title"), meta["date"]) if meta.get("date") else meta["url"]
            if key in seen:
                continue
            seen.add(key)
            result = {
                "match": _strength(m.score),
                "kind": meta["kind"],
                "title": meta.get("title"),
                "date": meta.get("date"),
                "text": meta["text"],
                "url": meta["url"],
                "found_on": meta.get("found_on"),
                "found_on_title": meta.get("found_on_title"),
            }
            out.append({k: v for k, v in result.items() if v})
            if len(out) == limit:
                break
        return out

    @staticmethod
    def contacts() -> list[dict]:
        return HOTLINES

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
        if _catalog is None or not _catalog.services:  # not loaded yet: check again next time
            _catalog = await _load()
        return _catalog


async def _load() -> Catalog:
    from app.models import Drug, Facility, FreeMed, IngestRun, Service
    from app.module import module

    def as_dicts(objs) -> list[dict]:
        return [{c.key: getattr(o, c.key) for c in o.__table__.columns} for o in objs]

    async with module.db() as session:
        rows = {
            name: as_dicts(await session.scalars(select(model)))
            for name, model in [("services", Service), ("drugs", Drug), ("free_meds", FreeMed),
                                ("facilities", Facility)]
        }
        last = await session.scalar(select(IngestRun).order_by(IngestRun.id.desc()).limit(1))
    rows["data_date"] = last.data_date if last else ""
    return await asyncio.to_thread(Catalog, rows)
