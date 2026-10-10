"""End-to-end smoke test of every step against a fake moph.gov.lb (httpx.MockTransport). No network needed.
Run:  python crawler/tests/e2e_mock.py
"""
import asyncio
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = tempfile.mkdtemp(prefix="wasel_e2e_")
os.environ["WASEL_ROOT"] = ROOT
os.environ["WASEL_DELAY"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402

FX = Path(__file__).parent / "fixtures"


def fx(name):
    return (FX / name).read_text(encoding="utf-8")


def make_xlsx() -> bytes:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AMAN"
    ws.append(["لائحة أدوية الأمراض المستعصية"])
    ws.append([])
    ws.append(["Brand Name", "Ingredient", "Dosage", "Form", "Indication"])
    ws.append(["HUMIRA", "Adalimumab", "40mg", "Syringe", "RA"])
    ws.append(["AVONEX", "Interferon beta-1a", "30mcg", "Syringe", "MS"])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


def make_pdf() -> bytes:
    # minimal valid one-page PDF with a text layer
    content = b"BT /F1 12 Tf 72 720 Td (IVIG request form AK010) Tj ET"
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>stream\n" % len(content) + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    return out


XLSX = make_xlsx()
PDF = make_pdf()
calls = []


def handler(req: httpx.Request) -> httpx.Response:
    p = req.url.path
    calls.append(str(req.url))
    assert req.headers["user-agent"].startswith("WaselHackathonBot")
    assert "intouchmena" not in str(req.url) and "sort:" not in p.replace("sort:Drug", "")
    html = lambda s: httpx.Response(200, text=s, headers={"content-type": "text/html; charset=utf-8"})
    if re.search(r"/AdministrativeServices/index$", p):
        return html('<div id="paginatedContent"><div class="lawCatRow" onclick="openAsCat(1,0);">\n <div class="lawCatRowTitle">General Directorate</div></div></div>')
    if re.search(r"/AdministrativeServices/view/1/0$", p):
        return html('<table><tr class="lawCatId"><td class="interestCol">مصلحة الديوان</td><td><table><tr><td class="sectionCol">دائرة التجهيز</td><td><table>'
                    '<tr><td class="nbCol">MPH12</td><td class="subjectCol"><a href="/en/AdministrativeServices/details/1">x</a></td></tr>'
                    '<tr><td class="nbCol"></td><td class="subjectCol"><a href="/en/AdministrativeServices/details/185">y</a></td></tr></table></td></tr></table></td></tr></table>')
    if "/AdministrativeServices/view/" in p:
        return html("<table></table>")
    m = re.search(r"/AdministrativeServices/details/(\d+)$", p)
    if m:
        return html({"1": fx("service_1_ar.html"), "185": fx("service_185_en.html")}.get(m.group(1), fx("service_missing.html")))
    if "/AdministrativeServices/download/" in p:
        return httpx.Response(200, content=PDF, headers={"content-type": "application/pdf",
                                                         "content-disposition": 'attachment; filename="AK010IVIG-4.pdf"'})
    if "/HealthFacilities/index/" in p:
        return html(fx("facilities_en.html").replace("page:23", "page:2"))
    if "/HealthFacilities/view/" in p:
        return html('<div id="paginatedContent"><div class="facilityRowDetails"><div class="infoTitle">Address</div><div class="infoContent">Hamra</div></div></div>')
    if "/Drugs/index/" in p:
        return html(fx("drugs_en.html").replace("page:61", "page:3"))
    if "/Drugs/view/" in p:
        return html(fx("drug_view.html"))
    if p.endswith(".xlsx"):
        return httpx.Response(200, content=XLSX)
    if p.endswith(".pdf"):
        return httpx.Response(200, content=PDF)
    if "/DynamicPages/listing/16" in p:
        return html(fx("listing_ar.html").replace("page:43", "page:2"))
    if "view_page" in p or "/Media/view/" in p:
        return html(fx("news_ar.html") if p.startswith("/ar/") else fx("news_en.html"))
    if "/Pages/3/77224" in p or p in ("/ar/", "/en/"):
        return html(fx("page_ar_77224.html"))
    if "/Laws/view/" in p:
        return html('<table><tr><td><a href="/Laws/download_file/12">Law 1</a></td></tr></table>')
    if "/Laws/download_file/" in p:
        return httpx.Response(200, content=PDF, headers={"content-type": "application/pdf"})
    if "/about" in p:
        return httpx.Response(503, text="flaky")
    return httpx.Response(404, text="")


_orig = httpx.AsyncClient.__init__


def _patched(self, *a, **kw):
    kw["transport"] = httpx.MockTransport(handler)
    _orig(self, *a, **kw)


def test_full_pipeline(monkeypatch=None):
    httpx.AsyncClient.__init__ = _patched
    from crawler import config as C
    C.RETRIES = 1
    C.BACKOFF_BASE = 0.01
    from crawler import run
    run.main(["priority", "full"])
    root = Path(ROOT) / "data"
    services = json.loads((root / "structured/services.json").read_text(encoding="utf-8"))
    assert {s["id"] for s in services} == {1, 185}
    s185 = [s for s in services if s["id"] == 185][0]
    assert s185["listing_unit"] == "مصلحة الديوان" and s185["department_en"] == "General Directorate"
    assert s185["apply_online"] is True and s185["documents"]
    fac = (root / "structured/facilities.csv").read_text(encoding="utf-8-sig")
    assert "American University of Beirut Medical Center" in fac and "84535" in fac
    drugs = (root / "structured/drugs.csv").read_text(encoding="utf-8-sig").splitlines()
    assert len(drugs) == 3, drugs
    fm = (root / "structured/free_meds.csv").read_text(encoding="utf-8-sig")
    assert "HUMIRA" in fm and "Brand Name" in fm and "Active medications in AMAN_final.xlsx" in fm
    pages = [json.loads(l) for l in (root / "raw/pages.jsonl").open(encoding="utf-8")]
    keys = [p["dedup_key"] for p in pages]
    assert len(keys) == len(set(keys))
    secs = {p["section"] for p in pages}
    assert {"service", "page", "news", "facility"} <= secs, secs
    news = [p for p in pages if p["section"] == "news"]
    assert all(p["date"] == "2026-10-08" for p in news)
    files = [json.loads(l) for l in (root / "raw/files.jsonl").open(encoding="utf-8")]
    assert any(f["local_path"].endswith("AK010IVIG-4.pdf") for f in files), [f["local_path"] for f in files]
    assert any(f["local_path"].endswith("userfiles/files/News/23-10-2024 List of Medications Provided By MoPH/Active medications in AMAN_final.xlsx") for f in files)
    pdf = [f for f in files if f["type"] == "pdf" and f.get("text_path")]
    assert pdf and "IVIG request form" in (Path(ROOT) / pdf[0]["text_path"]).read_text(encoding="utf-8")
    hot = (root / "structured/hotlines.csv").read_text(encoding="utf-8-sig")
    assert "1214" in hot and "1787" in hot
    rep = (root / "report.md").read_text(encoding="utf-8")
    assert "HealthFacilities/index/3/188" in rep and "spot-checks" in rep
    failed = (root / "failed_urls.txt").read_text(encoding="utf-8")
    assert "/about" in failed  # flaky page logged and retried, still failing
    # resumability: second run makes no new network requests for cached pages
    n_before = len(calls)
    run.main(["services", "facilities"])
    assert len(calls) - n_before <= 6, calls[n_before:]  # only nothing / tiny (index pages are cached too)
    print("e2e ok:", len(calls), "requests")


if __name__ == "__main__":
    test_full_pipeline()
