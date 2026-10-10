"""Cleaning pass over data/structured/* (offline, no network). Run: python -m crawler.run clean

Writes cleaned copies next to the raw ones (raw files are never modified):
  facilities_clean.csv     caza normalised to one English spelling + Arabic name + governorate; English-name flag
  services_clean.json      ordered document lists, empty fields dropped, english_available flag
  free_meds_unified.csv    the three Excel lists mapped to one schema (list_type, brand, generic, strength, ...)
  drugs_clean.csv          numeric price, ingredient list, duplicate-group id
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from typing import Dict, Optional

from . import config as C
from .progress import log

# (English canonical, Arabic, governorate)
CAZAS = [
    ("Beirut", "بيروت", "Beirut"),
    ("Baabda", "بعبدا", "Mount Lebanon"), ("Aley", "عاليه", "Mount Lebanon"), ("El Meten", "المتن", "Mount Lebanon"),
    ("Kesrouane", "كسروان", "Keserwan-Jbeil"), ("Jbeil", "جبيل", "Keserwan-Jbeil"), ("Chouf", "الشوف", "Mount Lebanon"),
    ("Zahle", "زحلة", "Bekaa"), ("West Bekaa", "البقاع الغربي", "Bekaa"), ("Rachaya", "راشيا", "Bekaa"),
    ("Baalbek", "بعلبك", "Baalbek-Hermel"), ("Hermel", "الهرمل", "Baalbek-Hermel"),
    ("Tripoli", "طرابلس", "North"), ("Zgharta", "زغرتا", "North"), ("El Koura", "الكورة", "North"),
    ("Bcharre", "بشري", "North"), ("El Batroun", "البترون", "North"), ("El Minieh-Dennie", "المنية-الضنية", "North"),
    ("Akkar", "عكار", "Akkar"),
    ("Saida", "صيدا", "South"), ("Sour", "صور", "South"), ("Jezzine", "جزين", "South"),
    ("El Nabatieh", "النبطية", "Nabatieh"), ("Marjaayoun", "مرجعيون", "Nabatieh"), ("Hasbaya", "حاصبيا", "Nabatieh"),
    ("Bint Jbeil", "بنت جبيل", "Nabatieh"),
]
# spelling variants seen on the site -> canonical English caza
ALIASES = {
    "beirut": "Beirut", "baabda": "Baabda", "aley": "Aley", "aaley": "Aley", "el meten": "El Meten", "meten": "El Meten",
    "metn": "El Meten", "el metn": "El Meten", "kesseroune": "Kesrouane", "kesrouane": "Kesrouane", "keserwan": "Kesrouane",
    "kesserwan": "Kesrouane", "jbeil": "Jbeil", "jbail": "Jbeil", "byblos": "Jbeil", "ech chouf": "Chouf", "al chouf": "Chouf",
    "el chouf": "Chouf", "chouf": "Chouf", "shouf": "Chouf", "zahle": "Zahle", "zahleh": "Zahle", "west bekaa": "West Bekaa",
    "bekaa west": "West Bekaa", "rachaya": "Rachaya", "rashaya": "Rachaya", "baalbek": "Baalbek", "baalabak": "Baalbek",
    "baalbeck": "Baalbek", "hermel": "Hermel", "el hermel": "Hermel", "tripoli": "Tripoli", "trablous": "Tripoli",
    "zgharta": "Zgharta", "el koura": "El Koura", "koura": "El Koura", "bcharre": "Bcharre", "bsharri": "Bcharre",
    "el batroun": "El Batroun", "batroun": "El Batroun", "el minieh-dennie": "El Minieh-Dennie", "minieh-dennie": "El Minieh-Dennie",
    "el minieh dennie": "El Minieh-Dennie", "akkar": "Akkar", "saida": "Saida", "sidon": "Saida", "sour": "Sour", "tyre": "Sour",
    "jezzine": "Jezzine", "el nabatieh": "El Nabatieh", "nabatieh": "El Nabatieh", "marjaayoun": "Marjaayoun",
    "marjayoun": "Marjaayoun", "hasbaya": "Hasbaya", "hasbaiya": "Hasbaya", "bint jbeil": "Bint Jbeil", "bent jbeil": "Bint Jbeil",
    "bcharreh": "Bcharre", "el maten": "El Meten", "nabatiye": "El Nabatieh", "المنية": "El Minieh-Dennie", "الضنية": "El Minieh-Dennie", "المنية الضنية": "El Minieh-Dennie", "المنية - الضنية": "El Minieh-Dennie",
    "كسروان": "Kesrouane", "المتن الشمالي": "El Meten", "بعلبك الهرمل": None, "بعلبك-الهرمل": None,
}
# values that are a governorate, not a caza
GOVERNORATES = {"جبل لبنان": "Mount Lebanon", "mount lebanon": "Mount Lebanon", "الشمال": "North", "north": "North",
                "الجنوب": "South", "south": "South", "البقاع": "Bekaa", "bekaa": "Bekaa", "بعلبك الهرمل": "Baalbek-Hermel",
                "بعلبك-الهرمل": "Baalbek-Hermel", "baalbek-hermel": "Baalbek-Hermel", "كسروان جبيل": "Keserwan-Jbeil"}
_EN = {c[0]: c for c in CAZAS}
_AR = {c[1]: c[0] for c in CAZAS}
LATIN = re.compile(r"[A-Za-z]")
ARABIC = re.compile(r"[؀-ۿ]")


def _norm_key(s: str) -> str:
    s = (s or "").strip().replace("ـ", "")
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def norm_caza(raw: str):
    """-> (caza_en, caza_ar, governorate) ; caza may be '' when the raw value is a governorate or unknown."""
    k = _norm_key(raw)
    if not k:
        return "", "", ""
    if k in GOVERNORATES:
        return "", "", GOVERNORATES[k]
    en = None
    if raw.strip() in _AR:
        en = _AR[raw.strip()]
    elif k in ALIASES:
        en = ALIASES[k]
    else:
        for e in _EN:
            if k == e.lower():
                en = e
    if not en:
        return "", "", ""
    c = _EN[en]
    return c[0], c[1], c[2]


def clean_facilities() -> None:
    src = C.STRUCT / "facilities.csv"
    if not src.exists():
        return
    rows = list(csv.DictReader(src.open(encoding="utf-8-sig")))
    unmapped = Counter()
    for r in rows:
        en, ar, gov = norm_caza(r.get("caza", ""))
        if not en and not gov:
            unmapped[r.get("caza", "")] += 1
        r["caza_en"], r["caza_ar"], r["governorate"] = en, ar, gov
        ne = (r.get("name_en") or "").strip()
        r["name_en_is_english"] = "yes" if LATIN.search(ne) and not ARABIC.search(ne) else "no"
        r["investment_auth_no"] = re.sub(r"\s+", " ", (r.get("investment_auth_no") or "").replace("____", "")).strip(" -")
        r["phone"] = re.sub(r"\s+", " ", (r.get("phone") or "")).strip()
    cols = ["facility_id", "name_en", "name_ar", "name_en_is_english", "type", "type_ar", "caza_en", "caza_ar",
            "governorate", "caza", "phone", "investment_auth_no", "url", "url_ar"]
    with (C.STRUCT / "facilities_clean.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    log(f"clean: facilities_clean.csv {len(rows)} rows; caza unmapped for {sum(unmapped.values())} rows: "
        f"{dict(unmapped.most_common(15))}")


def clean_services() -> None:
    src = C.STRUCT / "services.json"
    if not src.exists():
        return
    S = json.loads(src.read_text(encoding="utf-8"))
    out = []
    for s in S:
        same = s.get("fields_ar") == s.get("fields_en")
        rec = {k: v for k, v in s.items() if k not in ("fields_en",) and v not in ("", [], None)}
        rec["english_available"] = not same
        if same:
            rec.pop("title_en", None)  # the English page shows the same Arabic text
        rec["title"] = s.get("title_ar") or s.get("title_en")
        rec["documents"] = [d for d in s.get("documents", []) if d.strip(" :.-")]
        out.append(rec)
    (C.STRUCT / "services_clean.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"clean: services_clean.json {len(out)} services ({sum(1 for r in out if r['english_available'])} with real English)")


FM_MAP = {
    "code": ["Code"], "registration_number": ["Registration number"], "brand_name": ["Brand name", "Medication name"],
    "generic_composition": ["Chemical Composition"], "therapeutic_class": ["Medication Class"],
    "strength": ["Strength", "Dosage LNDI"], "presentation": ["Presentation", "PresentationLNDI"],
    "form": ["Form", "Form LNDI"], "agent": ["Agent"], "manufacturer": ["Manufacturer"], "country": ["Country"],
    "price_lbp": ["public price LL (1$=89500LL)", "public price LL"], "stratum": ["Stratum"],
}


def _list_type(fname: str) -> str:
    f = fname.lower()
    if "aman" in f:
        return "aman_intractable_diseases"
    if "tender" in f:
        return "tender_388_2024"
    if "allocation" in f:
        return "allocation_free"
    return "other"


def clean_free_meds() -> None:
    import pandas as pd
    src = C.STRUCT / "free_meds.csv"
    if not src.exists():
        return
    df = pd.read_csv(src, encoding="utf-8-sig", dtype=str)
    out = pd.DataFrame({"source_file": df["source_file"], "list_type": df["source_file"].map(_list_type)})
    lower = {re.sub(r"\s+", " ", str(c)).strip().lower(): c for c in df.columns}
    for col, cands in FM_MAP.items():
        s = pd.Series([None] * len(df), dtype=object)
        for c in cands:
            real = lower.get(c.lower())
            if real is not None:
                s = s.fillna(df[real])
        out[col] = s.map(lambda v: re.sub(r"\s+", " ", v.replace("\xa0", " ")).strip() if isinstance(v, str) else v)
    out["price_lbp"] = pd.to_numeric(out["price_lbp"], errors="coerce").round(0)
    out["source_url"] = df.get("source_url")
    out = out.dropna(subset=["brand_name", "generic_composition"], how="all")
    out.to_csv(C.STRUCT / "free_meds_unified.csv", index=False, encoding="utf-8-sig")
    log(f"clean: free_meds_unified.csv {len(out)} rows {out['list_type'].value_counts().to_dict()}")


def clean_drugs() -> None:
    import pandas as pd
    src = C.STRUCT / "drugs.csv"
    if not src.exists():
        return
    d = pd.read_csv(src, encoding="utf-8-sig", dtype=str)
    d["brand_or_generic_label"] = d["brand_or_generic"].map({"G": "generic", "B": "brand", "BioTech": "biotech",
                                                             "BioHuman": "biohuman"}).fillna(d["brand_or_generic"])
    d["price_lbp"] = pd.to_numeric(d["price_lbp"], errors="coerce")
    d["price_missing"] = d["price_lbp"].isna()
    d["ingredients_list"] = d["ingredients"].fillna("").map(
        lambda s: "; ".join(x.strip() for x in re.split(r"\s*[,+/]\s*(?![^()]*\))", re.sub(r"\s+-\s+[\d.,]+\s*\w+(/\w+)?", "", s)) if x.strip()))
    d["dup_group"] = d.groupby(["brand_name", "dosage", "form"], dropna=False).ngroup()
    d.to_csv(C.STRUCT / "drugs_clean.csv", index=False, encoding="utf-8-sig")
    log(f"clean: drugs_clean.csv {len(d)} rows; missing price {int(d['price_missing'].sum())}; "
        f"rows sharing name+dosage+form with another row {int(d.duplicated(['brand_name', 'dosage', 'form'], keep=False).sum())}")


def step_clean() -> None:
    for fn in (clean_services, clean_facilities, clean_drugs, clean_free_meds, clean_drug_equivalence):
        try:
            fn()
        except Exception as e:  # noqa
            log(f"clean: {fn.__name__} failed: {type(e).__name__}: {e}")


# --------------------------------------------------------------------------- drug equivalence (for "suggest an alternative")
SALTS = {"hcl", "hydrochloride", "sodium", "potassium", "trihydrate", "monohydrate", "dihydrate", "anhydrous", "fumarate",
         "hemifumarate", "maleate", "besylate", "besilate", "mesylate", "mesilate", "succinate", "tartrate", "citrate",
         "sulfate", "sulphate", "phosphate", "acetate", "bromide", "hyclate", "dipropionate", "propionate", "hydrobromide",
         "magnesium", "calcium", "disodium", "dihydrochloride", "hemihydrate", "pentahydrate", "as", "base", "equivalent",
         "to", "valerate", "furoate", "xinafoate", "decanoate", "embonate", "pamoate", "lactate", "gluconate", "nitrate",
         "bitartrate", "tromethamine", "arginine", "lysine", "erbumine", "medoxomil", "cilexetil"}
ER_RX = re.compile(r"extended|prolonged|modified|sustained|controlled|\bxr\b|\bsr\b|\bcr\b|\bmr\b|\bxl\b|retard|\bla\b", re.I)
DR_RX = re.compile(r"delayed|gastro[- ]?resistant|enteric", re.I)
FORM_FAMILIES = [("inhal", "inhalation"), ("nebul", "inhalation"), ("inject", "injection"), ("infusion", "injection"),
                 ("tablet", "tablet"), ("capsule", "capsule"), ("caplet", "tablet"), ("syrup", "oral liquid"),
                 ("oral solution", "oral liquid"), ("suspension", "oral liquid"), ("elixir", "oral liquid"),
                 ("drops", "drops"), ("cream", "cream"), ("ointment", "ointment"), ("gel", "gel"), ("lotion", "lotion"),
                 ("suppositor", "suppository"), ("patch", "patch"), ("spray", "spray"), ("powder", "powder"),
                 ("sachet", "powder"), ("granule", "powder"), ("solution", "solution"), ("lozenge", "lozenge")]


def molecule_key(name: str) -> str:
    n = re.sub(r"\(.*?\)", " ", (name or "").lower())
    words = [w for w in re.split(r"[^a-z]+", n) if w]
    core = [w for w in words if w not in SALTS]
    return " ".join(core or words)


def strength_key(s: str) -> str:
    s = (s or "").lower().replace(" ", "")
    m = re.fullmatch(r"(\d{1,3})[.,](\d{3})(mg|mcg|µg|g)?(.*)", s)
    if m:
        s = m.group(1) + m.group(2) + (m.group(3) or "") + m.group(4)
    m = re.fullmatch(r"([\d.,]+)(mg|mcg|µg|g)$", s)
    if m:
        v = float(m.group(1).replace(",", "."))
        v = v * 1000 if m.group(2) == "g" else v / 1000 if m.group(2) in ("mcg", "µg") else v
        return f"{v:g}mg"
    return s


def split_ingredients(ing: str):
    parts = re.split(r",\s*(?=[A-Za-z])", ing or "")
    out = []
    for p in parts:
        if " - " in p:
            name, st = p.rsplit(" - ", 1)
        else:
            name, st = p, ""
        if name.strip():
            out.append((molecule_key(name), strength_key(st)))
    return sorted(out)


def form_family(form: str) -> str:
    f = (form or "").lower()
    for k, fam in FORM_FAMILIES:
        if k in f:
            return fam
    return f.split(",")[0].strip() or "unknown"


def release_type(form: str, brand: str) -> str:
    t = f"{form} {brand}"
    return "ER" if ER_RX.search(t) else "DR" if DR_RX.search(t) else "IR"


def clean_drug_equivalence() -> None:
    import pandas as pd
    p = C.STRUCT / "drugs_clean.csv"
    if not p.exists():
        return
    d = pd.read_csv(p, encoding="utf-8-sig", dtype=str)
    for col in ("form", "brand_name", "atc", "ingredients"):
        d[col] = d[col].fillna("")
    comps = d["ingredients"].fillna("").map(split_ingredients)
    d["molecule_key"] = comps.map(lambda c: " + ".join(m for m, _ in c))
    d["strength_key"] = comps.map(lambda c: " + ".join(s for _, s in c))
    d["form_family"] = d["form"].map(form_family)
    d["release"] = [release_type(f if isinstance(f, str) else "", b if isinstance(b, str) else "") for f, b in zip(d["form"], d["brand_name"])]
    # tier 1: interchangeable (same molecules, same strengths, same form family and release) -> pharmacist-level substitution
    d["equiv_key"] = d["molecule_key"] + " | " + d["strength_key"] + " | " + d["form_family"] + " | " + d["release"]
    # tier 2: same molecules, any strength/form -> needs a doctor/pharmacist to adjust dose
    d["molecule_group"] = d["molecule_key"]
    # tier 3: same pharmacological subgroup (ATC level 4, e.g. C07AB = selective beta-blockers) -> doctor decision only
    d["atc4"] = d["atc"].fillna("").str[:5]
    d["n_equivalents"] = d.groupby("equiv_key")["drug_id"].transform("count") - 1
    # is the molecule on a MoPH free/AMAN list?
    fm = C.STRUCT / "free_meds_unified.csv"
    if fm.exists():
        m = pd.read_csv(fm, encoding="utf-8-sig", dtype=str)
        free_mol = set(m["generic_composition"].dropna().map(lambda s: molecule_key(re.split(r"\d", s)[0])))
        free_brand = set(m["brand_name"].dropna().str.upper().str.split().str[0])
        d["on_moph_free_list"] = [
            (mk in free_mol) or (str(b).upper().split()[0] in free_brand if isinstance(b, str) and b.strip() else False)
            for mk, b in zip(d["molecule_key"], d["brand_name"])]
    d.to_csv(p, index=False, encoding="utf-8-sig")
    log(f"clean: drug equivalence -> {int((d['n_equivalents'] > 0).sum())} of {len(d)} drugs have >=1 interchangeable "
        f"alternative; {d['equiv_key'].nunique()} equivalence groups; on MoPH free list: "
        f"{int(d.get('on_moph_free_list', pd.Series(dtype=bool)).sum())}")
