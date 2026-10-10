"""HTML parsing helpers for moph.gov.lb (CakePHP site, jQuery AJAX pagination)."""
from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit, quote

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from . import config as C

AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

# --------------------------------------------------------------------------- URLs

ITEM_RE = re.compile(r"^/(ar|en)/(?:Media/view|DynamicPages/view_page|DynamicPages/view|view)/(\d+)(?:/(\d+))?")
PAGE_RE = re.compile(r"^/(ar|en)/(?:Pages|DynamicPages/index)/(\d+)/(\d+)")
LANDING_RE = re.compile(r"^/(ar|en)/DynamicPages/landing_page/(\d+)")
SERVICE_RE = re.compile(r"^/(ar|en)/AdministrativeServices/details/(\d+)")
FAC_VIEW_RE = re.compile(r"^/(ar|en)/HealthFacilities/view/\d+/\d+/(\d+)")
DRUG_VIEW_RE = re.compile(r"^/(ar|en)/Drugs/view/(\d+)")
PAGENUM_RE = re.compile(r"/page:(\d+)")
LANG_RE = re.compile(r"^/(ar|en)(/|$)")

# routes that only exist without a language prefix (served regardless of language)
NO_LANG_PREFIX = ("/userfiles/", "/AdministrativeServices/download/", "/Laws/download_file/",
                  "/DynamicPages/download_file/", "/Publications/download_file/", "/img/", "/js/", "/css/")


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "lxml")


def to_ascii_digits(s: str) -> str:
    return (s or "").translate(AR_DIGITS)


def is_attachment(url: str) -> bool:
    p = urlsplit(url).path
    if any(x in p for x in C.ATTACHMENT_PATH_PATTERNS):
        return True
    return unquote(p).lower().endswith(C.ATTACHMENT_EXTS)


def normalize_url(href: str, base_url: str, lang_hint: Optional[str] = None) -> Optional[str]:
    """Absolute, on-site, canonical-ish URL or None if it must not be crawled."""
    if not href:
        return None
    href = href.strip()
    if href.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None
    # jQuery-address style links: http://moph.gov.lb/en/Pages/3/3010/x#/en/DynamicPages/view/5304/y
    if "#/" in href:
        frag = href.split("#", 1)[1]
        if LANG_RE.match(frag):
            href = frag
    absu = urljoin(base_url, href)
    parts = urlsplit(absu)
    if parts.scheme not in ("http", "https"):
        return None
    if parts.hostname not in C.ALLOWED_HOSTS:
        return None
    path = parts.path or "/"
    path = re.sub(r"/{2,}", "/", path)
    if any(path.startswith(p) for p in C.ROBOTS_DISALLOW_PREFIXES):
        return None
    full = path + ("?" + parts.query if parts.query else "")
    if any(s in full for s in C.SKIP_SUBSTRINGS):
        return None
    is_att = is_attachment(path)
    if not is_att:
        # drop query strings (filters, ?facility_type=, empty "?") - they are variants, not content
        query = ""
        # give un-prefixed page routes a language so the cookie never decides the language
        if not LANG_RE.match(path) and lang_hint and not path.startswith(NO_LANG_PREFIX) and path != "/":
            path = f"/{lang_hint}{path}"
        if path in ("/", ""):
            path = f"/{lang_hint or 'ar'}/"
    else:
        query = parts.query
    # percent-encode consistently (keeps Arabic slugs stable)
    path = quote(unquote(path), safe="/:%-_.~()!*'@,;=+$")
    return urlunsplit(("https", C.HOST, path, query, ""))


def url_lang(url: str) -> Optional[str]:
    m = LANG_RE.match(urlsplit(url).path)
    return m.group(1) if m else None


def section_of(url: str) -> str:
    p = urlsplit(url).path
    if SERVICE_RE.match(p) or "/AdministrativeServices/" in p:
        return "service"
    if "/HealthFacilities/" in p:
        return "facility"
    if "/Drugs/index" in p or "/Drugs/view" in p:
        return "drug"
    if re.match(r"^/(ar|en)/(Media/view|DynamicPages/view_page|DynamicPages/listing|Media/)", p):
        return "news"
    if re.match(r"^/(ar|en)/(Pages|DynamicPages|view|laws|Laws|publications|Publications|faq|about|"
                r"health_awareness|health_care|quality|campaigns|programs_projects|governance|statistics|"
                r"e-services|administrative_services|complaints|contact|Drugs/recalls)", p):
        return "page"
    return "other"


def content_key(url: str) -> Tuple[str, Optional[str]]:
    """Dedup key. Same content under different routes collapses to one key.
    Media/view/{id} == DynamicPages/view_page/{id}/16 == DynamicPages/view/{id} == /view/{id}."""
    p = urlsplit(urljoin(C.BASE, url)).path
    p_dec = unquote(p)
    pg = PAGENUM_RE.search(p_dec)
    pg_s = f"#p{pg.group(1)}" if pg and pg.group(1) != "1" else ""
    for rx, kind in ((ITEM_RE, "item"), (SERVICE_RE, "service"), (FAC_VIEW_RE, "facility"), (DRUG_VIEW_RE, "drug")):
        m = rx.match(p_dec)
        if m:
            return f"{m.group(1)}:{kind}:{m.group(2)}", m.group(2)
    m = PAGE_RE.match(p_dec)
    if m:
        return f"{m.group(1)}:page:{m.group(3)}{pg_s}", m.group(3)
    m = LANDING_RE.match(p_dec)
    if m:
        return f"{m.group(1)}:landing:{m.group(2)}{pg_s}", m.group(2)
    return "url:" + p_dec.rstrip("/"), None


# --------------------------------------------------------------------------- text

BLOCK_TAGS = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table",
              "section", "article", "blockquote", "dd", "dt", "pre", "td", "th"}
DROP_SELECTORS = ["script", "style", "noscript", "form", "select", "iframe", ".pageDetailsTop", ".socaialLink",
                  "#usersLogin", "#doctorsLogin", ".loginFormBox", ".paginationDiv", ".pagination",
                  ".PaginatorajaxLoader", "#applyOnlineForm", ".pageFormBox", "#contentLoader", ".learnMoreBtn",
                  ".jcarousel-control", "img"]


def decode_cfemail(hexstr: str) -> str:
    try:
        b = bytes.fromhex(hexstr)
        k = b[0]
        return "".join(chr(x ^ k) for x in b[1:])
    except Exception:
        return ""


def fix_cf_emails(node: Tag) -> None:
    for sp in node.select("[data-cfemail]"):
        sp.replace_with(decode_cfemail(sp.get("data-cfemail", "")))
    for a in node.select('a[href*="/cdn-cgi/l/email-protection"]'):
        h = a.get("href", "")
        if "#" in h:
            em = decode_cfemail(h.split("#", 1)[1])
            if em:
                a["href"] = "mailto:" + em


def block_text(node) -> str:
    """Text with newlines only at block boundaries / <br>, so inline <span>s don't split words."""
    if node is None:
        return ""
    out: List[str] = []

    def walk(n):
        for ch in n.children:
            if isinstance(ch, Comment):
                continue
            if isinstance(ch, NavigableString):
                out.append(str(ch))
            elif isinstance(ch, Tag):
                if ch.name == "br":
                    out.append("\n")
                    continue
                if ch.name in ("td", "th"):
                    out.append(" | " if out and not out[-1].endswith("\n") else "")
                walk(ch)
                if ch.name in BLOCK_TAGS and ch.name not in ("td", "th"):
                    out.append("\n")

    walk(node)
    txt = "".join(out).replace("\xa0", " ")
    lines = []
    for ln in txt.split("\n"):
        ln = re.sub(r"[ \t\r\f\v]+", " ", ln).strip(" |")
        if ln:
            lines.append(ln.strip())
    return "\n".join(lines)


def main_node(doc: BeautifulSoup) -> Optional[Tag]:
    """Main content container (menus/footer excluded)."""
    nodes = doc.select("#paginatedContent")
    if nodes:
        # the outermost one (they are often nested)
        return nodes[0]
    for sel in (".col-lg-9", "#body", "body"):
        n = doc.select_one(sel)
        if n is not None:
            return n
    return None


def clean_main(doc: BeautifulSoup) -> Optional[Tag]:
    node = main_node(doc)
    if node is None:
        return None
    node = BeautifulSoup(str(node), "lxml")  # copy
    for c in node.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    fix_cf_emails(node)
    for sel in DROP_SELECTORS:
        for el in node.select(sel):
            el.decompose()
    return node


def page_title(doc: BeautifulSoup) -> str:
    m = main_node(doc)
    scope = m if m is not None else doc
    for sel in ("h1.pageTitleDiv", ".asFormTitle", "h6", "h1", "h2", ".bluePageTitle", ".facilityTitle"):
        el = scope.select_one(sel)
        if el and el.get_text(strip=True):
            return re.sub(r"\s+", " ", el.get_text(" ", strip=True))
    og = doc.select_one('meta[property="og:title"]')
    if og and og.get("content") and og["content"].strip().lower() != "moph":
        return og["content"].strip()
    t = doc.title.get_text(strip=True) if doc.title else ""
    return t


DATE_RE = re.compile(r"(\d{1,4})\s*[/.\-]\s*(\d{1,2})\s*[/.\-]\s*(\d{1,4})")


def parse_date(s: str) -> Optional[str]:
    """'08/10/2026' (D/M/Y, English side) or '٢٠٢٦/١٠/٨' (Y/M/D, Arabic side) -> '2026-10-08'."""
    if not s:
        return None
    m = DATE_RE.search(to_ascii_digits(s))
    if not m:
        return None
    a, b, c = m.groups()
    try:
        if len(a) == 4:
            y, mo, d = int(a), int(b), int(c)
        else:
            d, mo, y = int(a), int(b), int(c)
            if y < 100:
                y += 2000
        return date(y, mo, d).isoformat()
    except ValueError:
        return None


def page_date(doc: BeautifulSoup) -> Optional[str]:
    m = main_node(doc)
    scope = m if m is not None else doc
    for el in scope.select(".newsBlockDate, .listingBlockDate, .eventDate, .newsDate"):
        txt = el.get_text(" ", strip=True)
        if "date" in txt.lower() or "تاريخ" in txt or DATE_RE.search(to_ascii_digits(txt)):
            d = parse_date(txt)
            if d:
                return d
    return None


def extract_links(html: str, base_url: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """(page_links, [(attachment_url, anchor_text)]) - on-site only, filtered."""
    lang = url_lang(base_url) or "ar"
    doc = soup(html)
    pages, atts = [], []
    seen = set()
    hrefs: List[Tuple[str, str]] = [(a.get("href", ""), a.get_text(" ", strip=True)) for a in doc.find_all("a")]
    # jQuery AJAX pagination urls in inline scripts: url:"\/en\/DynamicPages\/listing\/16\/page:2"
    for m in re.finditer(r'url:\s*"([^"]+)"', html):
        hrefs.append((m.group(1).replace("\\/", "/"), ""))
    # tree widgets loaded by AJAX
    for m in re.finditer(r"openLawCat\(['\"]?(\d+)", html):
        hrefs.append((f"/{lang}/Laws/view/{m.group(1)}", ""))
    for m in re.finditer(r"openAsCat\((\d+)\s*,\s*(\d+)\)", html):
        hrefs.append((f"/{lang}/AdministrativeServices/view/{m.group(1)}/{m.group(2)}", ""))
    for href, text in hrefs:
        u = normalize_url(href, base_url, lang)
        if not u or u in seen:
            continue
        seen.add(u)
        if is_attachment(u):
            atts.append((u, text))
        else:
            pages.append(u)
    return pages, atts


def max_page(html: str) -> int:
    nums = [int(x) for x in re.findall(r"page:(\d+)", html)]
    return max(nums) if nums else 1


# --------------------------------------------------------------------------- administrative services

SERVICE_LABELS = [
    # (field, [label keywords ar/en])
    ("directorate", ["المسؤول في الوزارة", "Responsible in the Ministry", "Directorate"]),
    ("responsible_unit", ["الوحدة المختصة", "Concerned Unit", "Responsible Unit", "Unit"]),
    ("office_address", ["العنوان", "Address"]),
    ("email", ["البريد الالكتروني", "البريد الإلكتروني", "Email", "E-mail"]),
    ("transaction_name", ["اسم المعاملة", "Transaction Name", "Service Name"]),
    ("form_number", ["رقم الإستمارة", "رقم الاستمارة", "Form Number", "Form Nb"]),
    ("documents", ["المستندات المطلوبة", "Required Documents", "Documents"]),
    ("eligibility", ["الشروط المطلوبة", "Required Conditions", "Conditions", "Eligibility"]),
    ("fees", ["الرسوم المتوجبة", "الرسوم", "Fees"]),
    ("hours", ["أيام تقديم الطلبات", "أيام وساعات", "Submission Days", "Working Hours", "Days"]),
    ("duration", ["مدة انتهاء المعاملة", "مدة إنجاز المعاملة", "Duration", "Processing Time"]),
    ("steps", ["آلية سير الملف", "آلية سير المعاملة", "Procedure", "Steps", "Process"]),
    ("form_files", ["نموذج الإستمارة", "نموذج الاستمارة", "Form Template", "Form"]),
]


def _label_field(label: str) -> Optional[str]:
    lab = re.sub(r"\s+", " ", label).strip().rstrip(":")
    for field, keys in SERVICE_LABELS:
        for k in keys:
            if lab == k:
                return field
    for field, keys in SERVICE_LABELS:
        for k in keys:
            if k.lower() in lab.lower():
                return field
    return None


def list_items(node: Tag) -> List[str]:
    """Items of a field in page order: each <li> is one item, other text is split on line breaks."""
    if node is None:
        return []
    node = BeautifulSoup(str(node), "lxml")
    for li in node.find_all("li"):
        txt = re.sub(r"\s+", " ", li.get_text(" ", strip=True)).strip()
        li.clear()
        li.append(txt)
    items = []
    for ln in block_text(node).split("\n"):
        ln = re.sub(r"^\s*(?:[-•*·]|\d+\s*[.)\-])\s*", "", ln).strip()
        if ln and ln not in (":", "-"):
            items.append(ln)
    return items


def parse_service(html: str, url: str) -> Optional[Dict]:
    doc = soup(html)
    pc = doc.select_one("#paginatedContent") or doc
    fix_cf_emails(pc)
    title_el = pc.select_one(".asFormTitle")
    title = re.sub(r"\s+", " ", title_el.get_text(" ", strip=True)) if title_el else ""
    rows = pc.select(".asRowDetails")
    if not title and not any(r.select_one(".infoContent") and r.select_one(".infoContent").get_text(strip=True) for r in rows):
        return None  # empty template = id does not exist
    rec: Dict = {"title": title, "fields": {}}
    form_urls: List[Dict] = []
    for r in rows:
        lab_el, val_el = r.select_one(".infoTitle"), r.select_one(".infoContent")
        if not lab_el or not val_el:
            continue
        label = re.sub(r"\s+", " ", lab_el.get_text(" ", strip=True))
        for a in val_el.find_all("a"):
            h = a.get("href", "")
            if is_attachment(urljoin(C.BASE, h)) or "download" in h:
                form_urls.append({"url": urljoin(C.BASE, h), "label": re.sub(r"\s+", " ", a.get_text(" ", strip=True))})
        field = _label_field(label)
        text = block_text(val_el)
        rec["fields"][label] = text
        if field in ("documents", "steps"):
            rec[field] = list_items(val_el)
        elif field == "eligibility":
            rec[field] = text
            rec["eligibility_items"] = list_items(val_el)
        elif field and field != "form_files":
            rec[field] = re.sub(r"\s*\n\s*", " ", text).strip()
    rec["form_urls"] = form_urls
    rec["links"] = sorted({urljoin(C.BASE, a.get("href")) for a in pc.select(".facilityContent a[href]")
                           if not a.get("href", "").startswith("mailto:")})
    rec["apply_online"] = bool(pc.select_one("#applyOnlineTitle, .applyOnlineTitle"))
    page_txt = pc.get_text(" ", strip=True)
    rec["track_transaction"] = bool(re.search(r"Track Transaction|Track your transaction|تتبع المعاملة|متابعة المعاملة", page_txt, re.I))
    return rec


# --------------------------------------------------------------------------- facility locator

def parse_facility_rows(html: str, lang: str) -> List[Dict]:
    doc = soup(html)
    out = []
    table = doc.select_one("#paginatedContent table") or doc.select_one("table")
    if not table:
        return out
    for tr in table.select("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 6:
            continue
        a = tr.select_one('a[href*="/HealthFacilities/view/"]')
        href = a["href"] if a else ""
        m = re.search(r"/HealthFacilities/view/\d+/\d+/(\d+)", href)
        vals = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)).strip() for td in tds]
        out.append({
            "facility_id": m.group(1) if m else "",
            "name_en": vals[0], "type": vals[1], "name_ar": vals[2], "caza": vals[3],
            "investment_auth_no": vals[4].replace("____", "").strip(), "phone": vals[5],
            "url": urljoin(C.BASE, href.split("?")[0]) if href else "",
            "lang": lang,
        })
    return out


def parse_kv_details(html: str) -> Dict[str, str]:
    """Facility detail page: rows of .infoTitle / .infoContent."""
    doc = soup(html)
    pc = doc.select_one("#paginatedContent") or doc
    fix_cf_emails(pc)
    d: Dict[str, str] = {}
    for row in pc.select(".facilityRowDetails"):
        t, v = row.select_one(".infoTitle"), row.select_one(".infoContent")
        if t and v:
            k = re.sub(r"\s+", " ", t.get_text(" ", strip=True)).strip()
            if k and k not in d:
                d[k] = re.sub(r"\s+", " ", v.get_text(" ", strip=True)).strip()
    title = pc.select_one(".facilityTitle, h1, h2, .bluePageTitle")
    if title:
        d["_title"] = re.sub(r"\s+", " ", title.get_text(" ", strip=True))
    return d


# --------------------------------------------------------------------------- drugs

def price_to_number(p: str) -> Optional[float]:
    s = to_ascii_digits(p or "").replace(",", "")
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def parse_drug_rows(html: str) -> List[Dict]:
    doc = soup(html)
    out = []
    for tr in doc.select("table tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 7:
            continue
        a = tr.select_one('a[href*="/Drugs/view/"]')
        href = a["href"] if a else ""
        m = re.search(r"/Drugs/view/(\d+)", href)
        v = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)).strip() for td in tds]
        out.append({"drug_id": m.group(1) if m else "", "atc": v[0], "brand_name": v[1], "brand_or_generic": v[2],
                    "ingredients": v[3], "dosage": v[4], "form": v[5], "price": v[6],
                    "price_lbp": price_to_number(v[6]), "url": urljoin(C.BASE, href) if href else ""})
    return out


def parse_drug_view(html: str) -> Dict[str, str]:
    doc = soup(html)
    t = doc.select_one(".table-responsive table") or doc.select_one("table")
    if not t:
        return {}
    heads = [re.sub(r"\s+", " ", th.get_text(" ", strip=True)) for th in t.select("thead th")]
    row = t.select_one("tbody tr")
    if not row:
        return {}
    vals = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)) for td in row.find_all("td", recursive=False)]
    return dict(zip(heads, vals))


# --------------------------------------------------------------------------- news listing

def parse_news_listing(html: str, base_url: str) -> List[Dict]:
    doc = soup(html)
    out, seen = [], set()
    for li in doc.select("li.listingBlockListItem"):
        a = li.select_one("a.listingBlockListItemTitle") or li.select_one("a[href]")
        if not a:
            continue
        u = normalize_url(a.get("href", ""), base_url, url_lang(base_url))
        if not u:
            continue
        key, cid = content_key(u)
        if key in seen:
            continue
        seen.add(key)
        d = li.select_one(".listingBlockDate")
        out.append({"url": u, "key": key, "content_id": cid, "title": a.get_text(" ", strip=True),
                    "date": parse_date(d.get_text(" ", strip=True)) if d else None})
    return out
