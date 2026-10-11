"""What the ministry pays at a hospital for a patient, from its own circulars (cover.json).

The rule kept changing through 2026 (80% normally, 100% for some, then for all uninsured Lebanese at
government and listed private hospitals), so patients rarely know what they are owed. This picks the
newest rule for the patient's situation, with its source and date, and says what it still needs to
know. It never judges items on a bill: hospital prices are not public.
"""

import csv
import json
import os
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

from rapidfuzz import fuzz, process

from app.text import is_arabic, normalize

DATA = Path(__file__).with_name("cover.json")
# The Facility Locator from the moph.gov.lb crawl, the same file the moph module loads.
FACILITIES = "structured/facilities_clean.csv"
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "sandpit" / "data"
HOSPITAL_TYPES = {"Governmental Hospitals": "government", "Private Hospitals": "private"}

PatientCover = Literal[
    "uninsured_lebanese", "nssf", "cooperative", "army_or_security", "insurance", "not_lebanese", "unknown"
]
Injury = Literal["none", "war", "port_blast"]
OTHER_PAYERS = {
    "nssf": "the NSSF", "cooperative": "the civil servants' cooperative",
    "army_or_security": "the army or security forces' health service", "insurance": "the insurance company",
}

# Words many hospital names share; dropped before matching so names are compared on what tells them
# apart. "Government" is used as a filter instead.
_GENERIC = {
    "مستشفي", "م", "مركز", "طبي", "الطبي", "الجامعي", "جامعي", "العام", "ش", "ل",
    "hospital", "hopital", "medical", "center", "centre", "university", "general", "the", "al", "el", "de", "du", "sal",
}
_GOVERNMENT = {"الحكومي", "حكومي", "governmental", "government", "gov"}
MATCH, MARGIN, CANDIDATE = 88, 5, 70


@cache
def data() -> dict:
    return json.loads(DATA.read_text())


def source(key: str) -> dict:
    return {"key": key, **data()["sources"][key]}


@dataclass
class Hospital:
    id: str  # "f<facility id>", or "list:<name>" for a listed hospital missing from the Facility Locator
    name: str
    name_ar: str
    kind: str  # government | private
    listed: bool  # on the ministry's published 100% list (circular of 14 Mar 2026)
    names: list[str]
    caza: str = ""
    phone: str = ""
    url: str = ""
    demo: bool = False  # fictional, for the demo bill

    def card(self) -> dict:
        return {k: v for k, v in {
            "id": self.id, "name": self.name, "name_ar": self.name_ar, "kind": self.kind, "on_100_percent_list": self.listed,
            "caza": self.caza, "phone": self.phone, "url": self.url,
        }.items() if v != ""} | ({"demo": True} if self.demo else {})


@cache
def hospitals() -> list[Hospital]:
    """The listed hospitals, joined to the Facility Locator, then every other licensed hospital."""
    path = Path(os.environ.get("MOPH_DATA_DIR", DEFAULT_DATA_DIR)) / FACILITIES
    with path.open(encoding="utf-8-sig") as f:
        by_id = {int(r["facility_id"]): r for r in csv.DictReader(f) if r["type"] in HOSPITAL_TYPES}
    out = []
    for h in data()["hospitals"]:
        f = by_id.pop(h["facility_id"], None)
        names = [h["name_ar"], *h.get("aliases", [])]
        if f:
            out.append(_from_facility(f, listed=True, extra=names, name_en=h.get("name_en", "")))
        else:
            out.append(Hospital(id=f"list:{h['name_ar']}", name=h.get("name_en") or h["name_ar"],
                                name_ar=h["name_ar"], kind=h["kind"],
                                listed=True, names=[*names, h.get("name_en", "")]))
    out += [_from_facility(f, listed=False) for f in by_id.values()]
    if os.environ.get("BILLS_DEMO", "1") != "0":
        out += [Hospital(id=f"demo:{h['name_ar']}", name=h["name_en"], name_ar=h["name_ar"], kind=h["kind"],
                         listed=False, names=[h["name_ar"], h["name_en"], *h.get("aliases", [])], demo=True)
                for h in data()["demo_hospitals"]]
    return out


def _from_facility(f: dict, listed: bool, extra: list[str] = (), name_en: str = "") -> Hospital:
    name = name_en or f["name_en"]
    if name.islower():  # the Facility Locator has some names in lower case
        name = name.title()
    return Hospital(
        id=f"f{f['facility_id']}", name=f["name_ar"] if is_arabic(name) or not name else name,
        name_ar=f["name_ar"], kind=HOSPITAL_TYPES[f["type"]], listed=listed,
        names=[*extra, f["name_ar"], f["name_en"]], caza=f["caza_en"], phone=f["phone"], url=f["url"],
    )


def _words(name: str) -> list[str]:
    return re.findall(r"\w+", normalize(name))


def _key(name: str, keep_government: bool = False) -> str:
    words = [w for w in _words(name) if w not in _GENERIC]
    return " ".join("gov" if w in _GOVERNMENT else w for w in words if keep_government or w not in _GOVERNMENT)


def match(name: str, options: list[Hospital]) -> tuple[Hospital | None, list[Hospital]]:
    """The hospital the name means, or None and the closest few when it is unclear.

    "Government" in the name narrows to government hospitals. Without it, a government hospital keeps
    the word in its name, so "اهدن" stays between Ehden's government and private hospitals and the
    agent asks, rather than promising full cover at the wrong one."""
    government = bool(_GOVERNMENT & set(_words(name)))
    if government:
        options = [h for h in options if h.kind == "government"]
    choices = {(i, j): _key(n, keep_government=not government)
               for i, h in enumerate(options) for j, n in enumerate(h.names) if n}
    best: dict[int, float] = {}
    for _, score, (i, _) in process.extract(_key(name), choices, scorer=fuzz.WRatio, limit=30,
                                            score_cutoff=CANDIDATE):
        best[i] = max(best.get(i, 0), score)
    ranked = sorted(best.items(), key=lambda kv: -kv[1])
    if ranked and ranked[0][1] >= MATCH and (len(ranked) == 1 or ranked[1][1] <= ranked[0][1] - MARGIN):
        return options[ranked[0][0]], []
    return None, [options[i] for i, _ in ranked[:3]]


ASK_HOSPITAL = "Which hospital is it? (as written on the bill)"
ASK_COVER = ("Is the patient Lebanese, and do they have any other cover: NSSF, the civil servants' cooperative, "
             "the army or security forces, or insurance?")

EMERGENCY_AND_LISTED_CASES = (
    "This covers all emergencies, and the hospital stays and operations the ministry covers; not every case "
    "(statement of 2 Jul 2026). The hospital can still charge for anything the ministry does not cover."
)
REPORT = (
    "The ministry asks patients who are charged differences anyway to report it (circular of 14 Mar 2026): "
    "offer to file the report with report_charge. At the billing desk right now, they can also call 1787."
)


def rule(hospital: Hospital, patient: PatientCover, injury: Injury) -> dict:
    """The rule for this patient at this hospital. `patient` must be known unless they were injured."""
    gov = hospital.kind == "government"
    if injury == "port_blast":
        return {
            "verdict": "no_extra_charge",
            "condition": None if gov else "if this hospital was already treating them for the injury on 13 Aug 2026",
            "rule": "The ministry pays 100% of the care linked to a port-explosion injury, whatever the patient's "
                    "other cover, and forbids hospitals to charge them any difference.",
            "patient_pays": "Nothing for care linked to the injury.",
            "sources": [source("port_blast")],
            "if_asked_to_pay": REPORT,
        }
    if injury == "war":
        return {
            "verdict": "no_extra_charge",
            "rule": "The ministry treats people wounded in the war at its expense, in government and private "
                    "hospitals, insured or not.",
            "patient_pays": "Nothing for the treatment of the war injury.",
            "sources": [source("war_cover")],
            "if_asked_to_pay": REPORT,
        }
    if patient in OTHER_PAYERS:
        return {
            "verdict": "not_ministry",
            "rule": f"The ministry's 100% cover is for patients with no other cover. Here {OTHER_PAYERS[patient]} "
                    "pays, and its own rules decide what the patient pays; Wasel cannot check those.",
            "patient_pays": f"Whatever {OTHER_PAYERS[patient]} does not cover; ask them.",
            "sources": [source("all_uninsured")],
        }
    if patient == "not_lebanese":
        return {
            "verdict": "cannot_confirm",
            "rule": "The ministry's statements on hospital cover are for uninsured Lebanese. We have no rule for "
                    "patients of other nationalities.",
            "patient_pays": "Unknown: ask the ministry on 1787.",
            "sources": [source("all_uninsured")],
        }
    if gov or hospital.listed:
        where = ("a government hospital" if gov else
                 "a private hospital on the ministry's list of hospitals that must give 100% cover (circular of 14 Mar 2026)")
        return {
            "verdict": "no_extra_charge",
            "rule": f"This is {where}. The ministry pays 100% for uninsured Lebanese, displaced or not, and the "
                    "hospital must not charge them differences.",
            "patient_pays": "Nothing for what the ministry covers.",
            "limits": EMERGENCY_AND_LISTED_CASES,
            "sources": [source("all_uninsured"), source("circular_8685")],
            "if_asked_to_pay": REPORT,
        }
    return {
        "verdict": "usual_share",
        "rule": "This private hospital is not on the ministry's published list of hospitals that must give 100% "
                "cover (circular of 14 Mar 2026). There the ministry pays its usual share, 65% at a private "
                "hospital, for a patient admitted at its expense, and the patient pays the rest.",
        "patient_pays": "The share the ministry does not pay (usually 35%), for a patient admitted at its expense.",
        "limits": "Since 2 Jul 2026 more private hospitals may have accepted the ministry's ceiling, but that list "
                  "is not published: 1787 can confirm whether this hospital is on it.",
        "sources": [source("circular_8685"), source("usual_rates"), source("all_uninsured")],
    }


def check(name: str, patient: PatientCover, injury: Injury) -> dict:
    hospital, candidates = match(name, hospitals())
    out: dict = {"hospital": hospital.card() if hospital else None}
    need = []
    if hospital is None:
        need.append(ASK_HOSPITAL)
        out["closest_hospitals"] = [h.card() for h in candidates]
    if patient == "unknown" and injury == "none":
        need.append(ASK_COVER)
    if need:
        return {**out, "need_to_know": need, "found": False}
    return {**out, "found": True, **rule(hospital, patient, injury),
            "rule_history": data()["timeline"], "list_note": data()["list"]["note"]}
