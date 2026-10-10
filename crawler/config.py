"""Central settings for the Wasel MoPH crawler."""
from __future__ import annotations

import os
from pathlib import Path

BASE = "https://www.moph.gov.lb"
HOST = "www.moph.gov.lb"
ALLOWED_HOSTS = {"www.moph.gov.lb", "moph.gov.lb"}
LANGS = ("ar", "en")

USER_AGENT = os.environ.get("WASEL_UA", "WaselHackathonBot (AUB Hack for Health)")

# Politeness
MAX_CONCURRENCY = int(os.environ.get("WASEL_CONCURRENCY", "3"))
DELAY_SECONDS = float(os.environ.get("WASEL_DELAY", "0.5"))  # per worker, between requests
TIMEOUT_SECONDS = 30.0
RETRIES = 3
BACKOFF_BASE = 2.0  # 2s, 4s, 8s
MAX_FILE_BYTES = int(os.environ.get("WASEL_MAX_FILE_MB", "150")) * 1024 * 1024

# Paths (repo root = parent of crawler/)
ROOT = Path(os.environ.get("WASEL_ROOT", Path(__file__).resolve().parent.parent))
DATA = ROOT / "data"
RAW = DATA / "raw"
FILES_DIR = RAW / "files"
TEXT_DIR = DATA / "text"
STRUCT = DATA / "structured"
STATE = DATA / "state"          # resumability: HTTP cache + visited index
CACHE_DIR = STATE / "cache"
PAGES_JSONL = RAW / "pages.jsonl"
FILES_JSONL = RAW / "files.jsonl"
FAILED_TXT = DATA / "failed_urls.txt"
VISITED_TXT = STATE / "visited.txt"
ATTACH_QUEUE = STATE / "attachments_queue.jsonl"
REPORT_MD = DATA / "report.md"

for _p in (RAW, FILES_DIR, TEXT_DIR, STRUCT, STATE, CACHE_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# Skip rules (applied to every discovered URL)
SKIP_SUBSTRINGS = (
    "sort:", "direction:", "orderField=", "orderDir=",
    "/Users/", "/users/", "login", "register", "forgot_pwd", "track_document",
    "sharer", "intent/tweet", "cws/share",
    "/Search/", "/cdn-cgi/", "intouchmena.com",
    "/maps/",
)
ROBOTS_DISALLOW_PREFIXES = ("/files/",)

ATTACHMENT_EXTS = (".pdf", ".xlsx", ".xls", ".docx", ".doc", ".csv", ".ppt", ".pptx", ".pps", ".ppsx", ".zip", ".txt", ".rtf")
ATTACHMENT_PATH_PATTERNS = (
    "/userfiles/",
    "/AdministrativeServices/download/",
    "/Laws/download_file/",
    "/DynamicPages/download_file/",
    "/Publications/download_file/",
)

# Facility Locator
FACILITY_TYPES_EN = {
    "1": "Governmental Hospitals", "2": "Physiotherapy Centers", "3": "Radiology Lab",
    "4": "PHC Centers", "5": "Dental Lab", "6": "Nurseries", "7": "Pharmacies", "8": "Private Hospitals",
}
