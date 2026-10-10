"""Retrieval checks on the real crawl data: questions the way the agent would phrase its searches,
and what must come back. Skipped when data/ is missing. Add a case whenever a search goes wrong."""

import pytest

from app.catalog import Catalog
from app.ingest import data_dir, load_files

pytestmark = pytest.mark.skipif(
    not (data_dir() / "structured" / "services_clean.json").exists(), reason="no crawl data"
)


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    return Catalog(load_files())


SERVICES = [
    # (query, any of these service ids in the top 3)
    ("استلام أدوية السرطان cancer medication collect", {6}),
    ("بدي جيب دوا السرطان", {6}),
    ("اجازة مزاولة مهنة تمريض nursing license", {164, 250, 225, 251}),
    ("تسجيل مرضى غسيل الكلى القصور الكلوي dialysis", {87}),
    ("مساعدة أدوية medicine assistance", {1, 177, 185, 187, 188, 206}),
    ("زرع نخاع العظم bone marrow transplant", {181}),
    ("استيراد أدوية للاستعمال الشخصي import medicine personal use", {62}),
    ("علاج بديل للادمان مخدرات substitution treatment", {72}),
    ("عضة كلب داء الكلب rabies", {138, 139}),
    ("هرمون النمو growth hormone", {192}),
    ("فتح صيدلية open a pharmacy", {38}),
    ("الملاريا malaria", {140, 141}),
    ("زرع كلية kidney transplant", {195}),
]


@pytest.mark.parametrize(("query", "expected"), SERVICES)
def test_service_search(catalog, query, expected):
    found = [s["service_id"] for s in catalog.search_services(query)]
    assert expected & set(found), f"{query!r} returned {found}"


FACTS = [
    ("dialysis session price غسيل الكلى", "dialysis"),
    ("hospital asked me to pay difference extra charges", "no_extra_charges"),
    ("mental health psychological support hotline", "hotline"),
    ("mammography free breast cancer screening", "mammography"),
    ("hospitalization coverage uninsured 100%", "hospitalization_coverage"),
]


@pytest.mark.parametrize(("query", "topic"), FACTS)
def test_fact_search(catalog, query, topic):
    found = [f["topic"] for f in catalog.search_facts(query)[:3]]
    assert topic in found, f"{query!r} returned {found}"


def test_drug_lookup_exact_typo_and_ingredient(catalog):
    assert catalog.lookup_drug("panadol")["drugs"][0]["brand_name"].lower().startswith("panadol")
    typo = catalog.lookup_drug("panadool")["drugs"]
    assert typo and typo[0]["match"] == "similar_name"
    assert catalog.lookup_drug("paracetamol")["drugs"]


def test_drug_card_lists_cheaper_equivalents_only(catalog):
    for drug in catalog.lookup_drug("augmentin", limit=10)["drugs"]:
        for e in drug.get("cheaper_equivalents", []):
            assert e["public_price"]


def test_free_list_lookup(catalog):
    assert catalog.lookup_drug("humira")["free_lists"]


def test_facilities_by_type_and_area(catalog):
    result = catalog.find_facilities(type="government_hospital", area="Akkar")
    assert result["total"] >= 1
    assert all(f["type"] == "Governmental Hospitals" for f in result["facilities"])
    assert catalog.find_facilities(type="primary_care_center", area="عكار")["total"] >= 1
    assert catalog.find_facilities(area="zahle")["total"] >= 1


def test_empty_result_warns_list_is_incomplete(catalog):
    result = catalog.find_facilities(type="pharmacy", area="Akkar")
    assert result["total"] == 0 and "incomplete" in result["note"]


def test_unknown_area_says_so(catalog):
    result = catalog.find_facilities(area="Atlantis")
    assert result["total"] == 0 and result["unknown_area"] == "Atlantis"


def test_page_search_returns_sources(catalog):
    results = catalog.search_pages("vaccination calendar children التلقيح")
    assert results and all(r["url"].startswith("https://www.moph.gov.lb") for r in results)
