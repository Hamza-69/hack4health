"""Retrieval checks on the real crawl data: questions the way the agent would phrase its searches,
and what must come back. Skipped when sandpit/data/ is missing. Add a case whenever a search goes wrong.

Drug and facility lookups run on the files alone. Search cases query the Pinecone index, so they
need OPENAI_API_KEY and PINECONE_API_KEY and an index loaded with `uv run python -m app.ingest`.
They only read the index.
"""

import pytest

from app import search_index
from app.catalog import Catalog
from app.ingest import data_dir, load_files
from app.text import normalize

pytestmark = pytest.mark.skipif(
    not (data_dir() / "structured" / "services_clean.json").exists(), reason="no crawl data"
)


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    return Catalog(load_files())


# Drugs and facilities


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


def test_exact_area_name_wins_over_a_longer_one(catalog):
    for area in ("Jbeil", "جبيل"):
        result = catalog.find_facilities(type="government_hospital", area=area)
        assert result["total"] >= 1
        assert all(f["caza"] == "Jbeil" for f in result["facilities"]), area  # not Bint Jbeil


def test_neighbourhood_is_matched_on_the_official_address(catalog):
    result = catalog.find_facilities(type="pharmacy", area="hamra", limit=25)
    names = [f["name"] for f in result["facilities"]]
    assert "صيدلية الحمرا" in names
    assert "PHARMACIA" not in names  # Beirut, but its address is Zqaq el Blat
    assert all("حمرا" in normalize(f.get("address") or f["name"]) for f in result["facilities"])


def test_empty_result_warns_list_is_incomplete(catalog):
    result = catalog.find_facilities(type="pharmacy", area="Akkar")
    assert result["total"] == 0 and "incomplete" in result["note"]


def test_unknown_area_says_so(catalog):
    result = catalog.find_facilities(area="Atlantis")
    assert result["total"] == 0 and result["unknown_area"] == "Atlantis"


# Search: any language, any phrasing.


@pytest.fixture(scope="session")
async def live(catalog):
    if not search_index.configured():
        pytest.skip("OPENAI_API_KEY and PINECONE_API_KEY not set")
    try:
        counts = await search_index.counts()
    except search_index.SearchUnavailable as e:
        pytest.skip(str(e))
    if not (counts.get(search_index.SERVICES) and counts.get(search_index.SITE)):
        pytest.skip("search index is empty; run `uv run python -m app.ingest`")
    yield catalog
    await search_index.close()


# Queries are mostly Arabic, as the agent is told to search (the ministry's content is Arabic);
# a few English ones check that English still finds the Arabic data.
SERVICES = [
    # (query, any of these service ids in the top 5)
    ("استلام أدوية السرطان cancer medication collect", {6}),
    ("بدي جيب دوا السرطان", {6, 180}),
    ("how do I get my cancer medication from the ministry", {6, 180}),
    ("كيف بجيب دوا السرطان من الوزارة", {6, 180}),  # the agent's Arabic for "kif bjib dawa el sarataan..."
    ("nursing license", {164, 250, 225, 251}),
    ("my father needs dialysis, how does he register", {87}),
    ("مساعدة أدوية medicine assistance", {1, 177, 185, 187, 188, 206}),
    ("bone marrow transplant", {181}),
    ("bring medicine from abroad for personal use", {62}),
    ("علاج بديل للادمان مخدرات substitution treatment", {72}),
    ("rabies shots after a dog bite", {138, 139}),
    ("growth hormone", {192}),
    ("بدي افتح صيدلية", {38}),
    ("malaria", {140, 141}),
    ("kidney transplant", {195}),
]


@pytest.mark.parametrize(("query", "expected"), SERVICES)
async def test_service_search(live, query, expected):
    found = [s["service_id"] for s in await live.search_services(query)]
    assert expected & set(found), f"{query!r} returned {found}"


SITE = [
    # (query, any of these strings in the URL of a top-5 result)
    ("كم تدفع وزارة الصحة عن جلسة غسيل الكلى", {"87216"}),
    ("how much does the ministry pay for one dialysis session", {"87216"}),
    ("المستشفى يطلب مني دفع فروقات مع أنني غير مضمون", {"83157", "87216"}),
    ("صورة الثدي الشعاعية مجانا", {"87271"}),
    ("هل تغطي وزارة الصحة الاستشفاء للبنانيين غير المضمونين", {"85973", "82829", "82424"}),
    ("توقيف شركة مياه تنورين عن التعبئة", {"Decision1931-2025"}),
    ("Tannourine water company stopped from bottling water", {"Decision1931-2025"}),
    ("تعميم تغطية النازحين من القرى الحدودية في المستشفيات الحكومية", {"letter26-1-3165", "82424"}),
    ("شروط الحصول على المخدرات لمرضى السرطان دائرة المخدرات", {"534", "80"}),  # OCR'd narcotics guideline
]


@pytest.mark.parametrize(("query", "expected"), SITE)
async def test_site_search(live, query, expected):
    urls = [r["url"] for r in await live.search_site(query)]
    assert any(e in u for u in urls for e in expected), f"{query!r} returned {urls}"


async def test_site_results_carry_sources(live):
    results = await live.search_site("vaccination calendar children التلقيح")
    assert results and all(r["url"].startswith("https://www.moph.gov.lb") for r in results)
    assert all(r["kind"] in {"page", "news", "other", "document"} for r in results)


async def test_documents_say_where_they_are_linked(live):
    results = await live.search_site("ministerial decision Karar")
    documents = [r for r in results if r["kind"] == "document"]
    assert documents and all(r["found_on"].startswith("https://www.moph.gov.lb") for r in documents)


async def test_unrelated_question_is_a_weak_match(live):
    results = await live.search_services("best pizza place in Beirut")
    assert all(r["match"] == "weak" for r in results)
