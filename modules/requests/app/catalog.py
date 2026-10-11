"""The service catalog (catalog.json): what each service needs and which desk decides it.

Adding a service means adding an entry there, not writing code. Facts come from the ministry's
own service pages (source_urls).
"""

import json
from functools import cache
from pathlib import Path

from h4h import ToolError

CATALOG = Path(__file__).with_name("catalog.json")


@cache
def services() -> dict[str, dict]:
    return {s["key"]: s for s in json.loads(CATALOG.read_text())}


def get(key: str) -> dict:
    service = services().get(key)
    if service is None:
        raise ToolError(f"unknown service {key!r}; services are: {', '.join(services())}")
    return service


def missing(service: dict, fields: dict[str, str], kinds: set[str]) -> dict:
    """What a request still lacks: required documents not among `kinds`, and empty fields.

    A field marked "confirm" (no other cover) is asked together with the summary, so it only
    counts as missing once everything else is in.
    """
    documents = [
        {"key": d["key"], "label_en": d["label_en"], "label_ar": d["label_ar"]}
        for d in service["documents"] if d["required"] and d["key"] not in kinds
    ]
    empty = [f for f in service["fields"] if not str(fields.get(f["key"]) or "").strip()]
    if documents or any(not f.get("confirm") for f in empty):
        empty = [f for f in empty if not f.get("confirm")]
    return {
        "missing_documents": documents,
        "missing_fields": [{"key": f["key"], "label_en": f["label_en"], "label_ar": f["label_ar"]} for f in empty],
    }


def check_kinds(service: dict, kinds: set[str]) -> None:
    known = {d["key"] for d in service["documents"]}
    if unknown := kinds - known:
        raise ToolError(f"unknown document kinds {sorted(unknown)}; this service takes: {', '.join(sorted(known))}")
