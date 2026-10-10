"""Offline parser tests against real moph.gov.lb markup captured on 10 Oct 2026.
Run:  python -m pytest crawler/tests -q     (or: python crawler/tests/test_parsers.py)
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("WASEL_ROOT", tempfile.mkdtemp(prefix="wasel_test_"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from crawler import parse as P  # noqa: E402

FX = Path(__file__).parent / "fixtures"


def fx(name):
    return (FX / name).read_text(encoding="utf-8")


def test_service_full():
    rec = P.parse_service(fx("service_185_en.html"), "https://www.moph.gov.lb/en/AdministrativeServices/details/185")
    assert rec["title"].startswith("طلب الحصول على مساعدة أدوية")
    assert rec["responsible_unit"] == "مصلحة الديوان - دائرة التجهيز والتموين"
    assert rec["office_address"] == "بئر حسن، الجناح، قرب أوجيرو"
    assert rec["email"] == "drugs@moph.gov.lb"
    assert rec["duration"] == "أسبوعان"
    assert rec["hours"].startswith("من الأثنين حتى الجمعة")
    docs = rec["documents"]
    assert docs[0] == "صورة الهوية او اخراج القيد"
    assert any("Physician’s prescription" in d and "الوصفة الطبية" in d for d in docs), docs
    assert any(d.startswith("صورة عن بطاقة مركز توزيع الأدوية") for d in docs), docs
    assert any("For ITP" in d for d in docs)
    assert "أن يكون المريض لبنانياً" in rec["eligibility_items"]
    assert rec["form_urls"][0]["url"] == "https://www.moph.gov.lb/AdministrativeServices/download/1359"
    assert rec["apply_online"] is True
    assert rec["track_transaction"] is False
    assert rec.get("fees", "") == ""


def test_service_cf_email_and_forms():
    rec = P.parse_service(fx("service_1_ar.html"), "https://www.moph.gov.lb/ar/AdministrativeServices/details/1")
    assert rec["email"] == "drugs@moph.gov.lb", rec["email"]
    assert rec["form_number"] == "MPH12"
    assert len(rec["form_urls"]) == 2
    assert rec["apply_online"] is False


def test_service_missing():
    assert P.parse_service(fx("service_missing.html"), "x") is None


def test_facilities():
    rows = P.parse_facility_rows(fx("facilities_en.html"), "en")
    assert len(rows) == 2
    r = rows[0]
    assert r["facility_id"] == "84535"
    assert r["name_en"] == "American University of Beirut Medical Center"
    assert r["name_ar"] == "المركز الطبي في الجامعة الأميركية في بيروت"
    assert r["type"] == "Private Hospitals" and r["caza"] == "Beirut"
    assert r["investment_auth_no"] == "" and r["phone"] == "01-350000/01-340460"
    assert P.max_page(fx("facilities_en.html")) == 23 or P.max_page(fx("facilities_en.html")) >= 23


def test_drugs():
    rows = P.parse_drug_rows(fx("drugs_en.html"))
    assert len(rows) == 2
    assert rows[0] == {**rows[0], "atc": "B05XA03", "brand_name": "0.45% SODIUM CHLORIDE INJECTION USP",
                       "brand_or_generic": "G", "dosage": "0.45%", "form": "Injectable solution",
                       "price": "176,974 L.L", "price_lbp": 176974.0, "drug_id": "1261"}
    assert P.max_page(fx("drugs_en.html")) == 61
    v = P.parse_drug_view(fx("drug_view.html"))
    assert v["Agent"] == "A Pharma Solutions SAL" and v["Presentation"] == "1000ml" and v["Country"] == "Lebanon"


def test_news_detail_en_ar():
    doc = P.soup(fx("news_en.html"))
    assert P.page_date(doc) == "2026-10-08"
    assert P.page_title(doc) == "Public Tender for the Procurement of Medicines for the Ministry of Public Health"
    text = P.block_text(P.clean_main(doc))
    assert "تعتزم وزارة الصحة العامة" in text
    assert "About MOPH" not in text and "Back" not in text and ".bluePageTitle" not in text and "$(" not in text
    _, atts = P.extract_links(fx("news_en.html"), "https://www.moph.gov.lb/en/DynamicPages/view_page/87285/16/x")
    assert atts[0][0] == "https://www.moph.gov.lb/userfiles/files/News/2026/Tender%20388.pdf"
    doc = P.soup(fx("news_ar.html"))
    assert P.page_date(doc) == "2026-10-08"
    assert P.page_title(doc) == "مناقصة عمومية لتلزيم ادوية لزوم وزارة الصحة العامة"


def test_listing():
    items = P.parse_news_listing(fx("listing_ar.html"), "https://www.moph.gov.lb/ar/DynamicPages/listing/16/limit:100")
    assert [i["content_id"] for i in items] == ["87271", "87285"]
    assert items[0]["date"] == "2026-10-08"
    assert items[0]["key"] == "ar:item:87271"
    assert P.max_page(fx("listing_ar.html")) == 43


def test_keys_and_dedupe():
    a = P.content_key("https://www.moph.gov.lb/en/Media/view/87285/public-tender")[0]
    b = P.content_key("https://www.moph.gov.lb/en/DynamicPages/view_page/87285/16/public-tender")[0]
    c = P.content_key("https://www.moph.gov.lb/en/DynamicPages/view/87285/x")[0]
    assert a == b == c == "en:item:87285"
    assert P.content_key("https://www.moph.gov.lb/ar/Media/view/87285/x")[0] == "ar:item:87285"
    assert P.content_key("/en/Pages/3/3010/pharmaceuticals")[0] == "en:page:3010"
    assert P.content_key("/en/Pages/3/3010/page:2")[0] == "en:page:3010#p2"


def test_url_rules():
    base = "https://www.moph.gov.lb/ar/Pages/3/77224/x"
    pages, atts = P.extract_links(fx("page_ar_77224.html"), base)
    allu = pages + [a for a, _ in atts]
    assert not any("intouchmena" in u or "track_document" in u or "orderField" in u or "/files/" in u.replace("/userfiles/", "") for u in allu), allu
    assert "https://www.moph.gov.lb/ar/HealthFacilities/index/3/188/8/page:2" in pages  # lang added, '?' dropped
    assert "https://www.moph.gov.lb/ar/Laws/view/4" in pages
    assert len(atts) == 3 and all(a.endswith(".xlsx") for a, _ in atts)
    assert P.normalize_url("http://moph.gov.lb/en/Pages/3/3010/pharmaceuticals#/en/DynamicPages/view/5304/drugs", base) \
        == "https://www.moph.gov.lb/en/DynamicPages/view/5304/drugs"
    assert P.normalize_url("/en/Drugs/index/3/4848/page:2/sort:Drug.brand_name/direction:ASC", base) is None
    assert P.normalize_url("https://mophnew.intouchmena.com/en/x", base) is None
    assert P.section_of("https://www.moph.gov.lb/en/Media/view/1/x") == "news"
    assert P.section_of("https://www.moph.gov.lb/ar/Pages/3/77224/x") == "page"


def test_dates():
    assert P.parse_date("Date: 08/10/2026") == "2026-10-08"
    assert P.parse_date("٢٠٢٦/١٠/٨") == "2026-10-08"
    assert P.parse_date("05/10/20") == "2020-10-05"
    assert P.parse_date("nothing") is None


if __name__ == "__main__":
    n = 0
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
            n += 1
    print(f"{n} tests passed")
