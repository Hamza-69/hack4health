"""Attachments: download (keeping the original path) and text extraction (PDF/DOCX -> .txt, XLSX/XLS -> .csv)."""
from __future__ import annotations

import json
import mimetypes
import re
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlsplit

from . import config as C
from .fetch import Fetcher
from .progress import log
from .store import JsonlSet, now_iso

CT_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/zip": ".zip",
    "text/csv": ".csv",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

_files: Optional[JsonlSet] = None


def files_store() -> JsonlSet:
    global _files
    if _files is None:
        _files = JsonlSet(C.FILES_JSONL, "url")
    return _files


def local_path_for(url: str) -> Path:
    """/userfiles/files/A%20B/c.pdf -> data/raw/files/userfiles/files/A B/c.pdf (original path kept)."""
    path = unquote(urlsplit(url).path).lstrip("/")
    path = re.sub(r"[\x00-\x1f<>:\"|?*]", "_", path)
    parts = [p[:180] for p in path.split("/") if p not in ("", ".", "..")]
    return C.FILES_DIR.joinpath(*parts)


def P_is_endpoint(url: str) -> bool:
    return any(x in url for x in ("/AdministrativeServices/download/", "/Laws/download_file/", "/DynamicPages/download_file/", "/Publications/download_file/"))


def _ftype(p: Path) -> str:
    return p.suffix.lower().lstrip(".") or "bin"


async def download_one(f: Fetcher, url: str, source_page: str) -> Optional[Dict]:
    fs = files_store()
    if url in fs:
        # already downloaded in an earlier run: find record
        for line in C.FILES_JSONL.open(encoding="utf-8"):
            r = json.loads(line)
            if r["url"] == url:
                return r
    dest = local_path_for(url)
    is_endpoint = not Path(dest.name).suffix  # /AdministrativeServices/download/1359 has no extension
    if is_endpoint:
        dest = dest.with_name(dest.name + ".download")
    r = await f.download(url, dest)
    if not r.ok:
        return None
    if is_endpoint and dest.exists():
        ext = ""
        cd = r.final_url.split("|", 1)[1] if "|" in r.final_url else ""
        m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd)
        fname = unquote(m.group(1)) if m else ""
        if fname and Path(fname).suffix:
            ext = Path(fname).suffix.lower()
        elif r.text:
            ext = CT_EXT.get(r.text.split(";")[0].strip(), "") or (mimetypes.guess_extension(r.text.split(";")[0].strip()) or "")
        if not ext:
            head = dest.read_bytes()[:8]
            ext = ".pdf" if head.startswith(b"%PDF") else (".zip" if head.startswith(b"PK") else ".bin")
            if ext == ".zip":
                try:
                    names = zipfile.ZipFile(dest).namelist()
                    ext = ".docx" if any(n.startswith("word/") for n in names) else ".xlsx" if any(n.startswith("xl/") for n in names) else ".zip"
                except Exception:
                    pass
        safe = re.sub(r"[\\/\x00-\x1f<>:\"|?*]", "_", Path(fname).stem)[:120] if fname else ""
        final = dest.with_name(dest.name.replace(".download", "") + (("__" + safe) if safe else "") + ext)
        dest.replace(final)
        dest = final
    elif not dest.exists():
        # downloaded in an earlier run under a renamed endpoint name
        cands = list(dest.parent.glob(dest.name.replace(".download", "") + "*")) if dest.parent.exists() else []
        if not cands:
            return None
        dest = cands[0]
    rec = {"url": url, "local_path": str(dest.relative_to(C.ROOT)), "type": _ftype(dest),
           "size": dest.stat().st_size, "source_page_url": source_page, "text_path": None, "fetched_at": now_iso()}
    fs.add(rec)
    return rec


async def step_attachments(f: Fetcher, st, sections: Optional[Tuple[str, ...]] = None,
                           max_files: Optional[int] = None, exts: Optional[Tuple[str, ...]] = None,
                           since: Optional[str] = None) -> None:
    """Download every queued attachment (optionally only those found on pages of the given sections)."""
    import asyncio
    if not C.ATTACH_QUEUE.exists():
        log("attachments: queue empty")
        return
    todo = []
    fs = files_store()
    for line in C.ATTACH_QUEUE.open(encoding="utf-8"):
        q = json.loads(line)
        if q["url"] in fs:
            continue
        if sections and q.get("section") not in sections:
            continue
        if exts and not (P_is_endpoint(q["url"]) or unquote(q["url"]).lower().split("?")[0].endswith(exts)):
            continue
        todo.append(q)
    if since:
        # keep attachments of pages dated >= since (or undated pages / services / forms)
        dates = {}
        if C.PAGES_JSONL.exists():
            for line in C.PAGES_JSONL.open(encoding="utf-8"):
                try:
                    r = json.loads(line)
                    dates[r["url"]] = r.get("date") or ""
                except Exception:
                    pass
        todo = [q for q in todo if (dates.get(q["source_page_url"]) or "9999") >= since]
    # newest / most useful first: forms and spreadsheets, then PDFs
    prio = lambda q: (0 if P_is_endpoint(q["url"]) else 1 if unquote(q["url"]).lower().endswith((".xlsx", ".xls")) else 2)
    todo.sort(key=prio)
    if max_files is not None:
        todo = todo[:max_files]
    log(f"attachments: {len(todo)} to download (sections={sections or 'all'})")
    done = 0
    for i in range(0, len(todo), 30):
        batch = todo[i:i + 30]
        res = await asyncio.gather(*[download_one(f, q["url"], q["source_page_url"]) for q in batch])
        done += sum(1 for r in res if r)
        if (i // 30) % 10 == 0:
            log(f"attachments: {i + len(batch)}/{len(todo)} processed, {done} ok ({f.stats()})")
    log(f"attachments: finished, {done}/{len(todo)} downloaded")


# --------------------------------------------------------------------------- extraction

def excel_to_frames(path: Path):
    """Yield (sheet_name, DataFrame) with a detected header row (MoPH sheets often start with title rows)."""
    import pandas as pd
    try:
        sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
    except Exception as e:  # noqa
        log(f"  excel read failed {path.name}: {e}")
        return
    for name, raw in sheets.items():
        raw = raw.dropna(how="all").dropna(axis=1, how="all")
        if raw.empty:
            continue
        if raw.shape[1] < 2:
            continue  # single-column sheets are notes, not tables
        hdr_idx = raw.index[0]
        best = None
        for idx in list(raw.index[:20]):
            row = raw.loc[idx]
            vals = [v for v in row if isinstance(v, str) and v.strip()]
            numeric = sum(1 for v in vals if re.fullmatch(r"[\d.,\s/%-]+", v.strip()))
            texty = len(vals) - numeric
            if len(vals) < max(2, 0.5 * raw.shape[1]):
                continue
            score = texty - 2 * numeric + 0.1 * len(vals)
            if best is None or score > best:
                best, hdr_idx = score, idx
        header = [str(v).strip() if isinstance(v, str) and v.strip() else f"col_{i + 1}" for i, v in enumerate(raw.loc[hdr_idx])]
        seen = {}
        cols = []
        for h in header:
            h = re.sub(r"\s+", " ", h)
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 0
            cols.append(h)
        df = raw.loc[raw.index > hdr_idx].copy()
        df.columns = cols
        df = df.dropna(how="all")
        yield str(name), df


def _extract_worker(local_path: str) -> Dict:
    p = C.ROOT / local_path
    ext = p.suffix.lower()
    rel = Path(local_path).relative_to("data/raw/files") if local_path.startswith("data/raw/files") else Path(p.name)
    out: Dict = {"local_path": local_path, "text_path": None, "note": ""}
    try:
        if ext == ".pdf":
            import pdfplumber
            texts, empty = [], 0
            with pdfplumber.open(str(p)) as pdf:
                n = len(pdf.pages)
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    if len(t.strip()) < 20:
                        empty += 1
                    texts.append(t)
                    page.flush_cache()
            txt = "\n\n".join(texts).strip()
            dest = C.TEXT_DIR / rel.with_suffix(rel.suffix + ".txt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(txt, encoding="utf-8")
            out["text_path"] = str(dest.relative_to(C.ROOT))
            out["pages"] = n
            if n and empty / n > 0.6:
                out["note"] = "scanned_or_no_text"
        elif ext == ".docx":
            import docx
            d = docx.Document(str(p))
            parts = [para.text for para in d.paragraphs if para.text.strip()]
            for t in d.tables:
                for row in t.rows:
                    parts.append(" | ".join(c.text.strip() for c in row.cells))
            dest = C.TEXT_DIR / rel.with_suffix(rel.suffix + ".txt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("\n".join(parts), encoding="utf-8")
            out["text_path"] = str(dest.relative_to(C.ROOT))
        elif ext in (".xlsx", ".xls", ".xlsm"):
            paths = []
            for sheet, df in excel_to_frames(p):
                safe = re.sub(r"[^\w\-]+", "_", sheet)[:60]
                dest = C.TEXT_DIR / rel.parent / f"{rel.name}__{safe}.csv"
                dest.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(dest, index=False, encoding="utf-8-sig")
                paths.append(str(dest.relative_to(C.ROOT)))
            out["text_path"] = paths[0] if len(paths) == 1 else (paths or None)
        elif ext == ".csv":
            out["text_path"] = local_path
        else:
            out["note"] = f"no_extractor_for_{ext or 'unknown'}"
    except Exception as e:  # noqa
        out["note"] = f"extract_error: {type(e).__name__}: {str(e)[:120]}"
    return out


def step_extract(workers: int = 3) -> None:
    if not C.FILES_JSONL.exists():
        log("extract: no files.jsonl yet")
        return
    recs = [json.loads(l) for l in C.FILES_JSONL.open(encoding="utf-8")]
    todo = [r for r in recs if not r.get("text_path") and not r.get("extract_note")]
    log(f"extract: {len(todo)} files to extract ({len(recs)} total)")
    results = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_extract_worker, r["local_path"]): r["local_path"] for r in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            try:
                res = fu.result()
            except Exception as e:  # noqa
                res = {"local_path": futs[fu], "text_path": None, "note": f"worker_crash: {e}"}
            results[res["local_path"]] = res
            if i % 100 == 0:
                log(f"extract: {i}/{len(todo)}")
    for r in recs:
        res = results.get(r["local_path"])
        if res:
            r["text_path"] = res["text_path"]
            if res.get("note"):
                r["extract_note"] = res["note"]
            if res.get("pages"):
                r["pages"] = res["pages"]
    _write_files(recs)
    log(f"extract: done ({sum(1 for r in results.values() if r['text_path'])} with text)")


def _write_files(recs: List[Dict]) -> None:
    """Rewrite files.jsonl with updated records."""
    tmp = C.FILES_JSONL.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    global _files
    if _files is not None:
        _files.close()
        _files = None
    tmp.replace(C.FILES_JSONL)


# --------------------------------------------------------------------------- OCR

OCR_PROMPT = (
    "This is a scanned page from a document of Lebanon's Ministry of Public Health. Transcribe all of its "
    "text exactly, in its original language (usually Arabic), in reading order. Keep numbers, dates and "
    "article numbers as written. Write tables as rows with ' | ' between cells. Leave out stamps and "
    "signatures unless they contain readable text. Output only the transcription."
)
OCR_BATCH = 10  # files rendered at a time
ARABIC_SHARE = 0.3  # PDF text layers this Arabic are in visual order with broken glyphs: unusable


def _needs_ocr(r: Dict) -> bool:
    """Scanned PDFs, and PDFs whose text layer is mostly Arabic."""
    note = r.get("extract_note") or ""
    if not r.get("text_path") or note.startswith("ocr:"):
        return False
    if note == "scanned_or_no_text":
        return True
    if r.get("type") != "pdf" or note:
        return False
    text = (C.ROOT / r["text_path"]).read_text(encoding="utf-8", errors="ignore")
    return len(text) > 200 and len(re.findall(r"[\u0600-\u06FF]", text)) / len(text) > ARABIC_SHARE


def _render_pages(path: Path) -> List[bytes]:
    """Each page as a PNG. pdfium is not thread-safe, so this runs on the main thread only."""
    import io
    import pdfplumber
    pngs = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            buf = io.BytesIO()
            page.to_image(resolution=C.OCR_DPI).original.save(buf, format="PNG")
            pngs.append(buf.getvalue())
            page.flush_cache()
    return pngs


def _ocr_page(client, png: bytes) -> str:
    import base64
    resp = client.responses.create(
        model=C.OCR_MODEL,
        reasoning={"effort": "low"},
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": OCR_PROMPT},
            {"type": "input_image", "detail": "high",
             "image_url": "data:image/png;base64," + base64.b64encode(png).decode()},
        ]}],
    )
    return resp.output_text.strip()


def step_ocr() -> None:
    """OCR scanned PDFs and Arabic PDFs (see _needs_ocr) with an OpenAI vision model. Needs OPENAI_API_KEY.
    The transcription replaces the .txt; a file that fails is left as it was and retried next run."""
    import os
    from concurrent.futures import ThreadPoolExecutor
    if not os.environ.get("OPENAI_API_KEY"):
        log("ocr: OPENAI_API_KEY not set, skipping")
        return
    if not C.FILES_JSONL.exists():
        log("ocr: no files.jsonl yet")
        return
    from openai import OpenAI
    client = OpenAI(max_retries=4, timeout=180)
    recs = [json.loads(l) for l in C.FILES_JSONL.open(encoding="utf-8")]
    todo = [r for r in recs if _needs_ocr(r)]
    log(f"ocr: {len(todo)} files with {C.OCR_MODEL}")
    done = pages = 0
    with ThreadPoolExecutor(max_workers=C.OCR_WORKERS) as pool:
        for start in range(0, len(todo), OCR_BATCH):
            batch = []
            for r in todo[start:start + OCR_BATCH]:
                try:
                    pngs = _render_pages(C.ROOT / r["local_path"])
                except Exception as e:  # noqa
                    log(f"  ocr: cannot render {r['local_path']}: {e}")
                    continue
                batch.append((r, [pool.submit(_ocr_page, client, png) for png in pngs]))
            for r, futs in batch:
                try:
                    texts = [fu.result() for fu in futs]
                except Exception as e:  # noqa
                    log(f"  ocr failed {r['local_path']}: {type(e).__name__}: {str(e)[:120]}")
                    continue
                (C.ROOT / r["text_path"]).write_text("\n\n".join(texts).strip(), encoding="utf-8")
                r["extract_note"] = f"ocr:{C.OCR_MODEL}"
                done += 1
                pages += len(texts)
            _write_files(recs)
            log(f"ocr: {start + len(batch)}/{len(todo)} files, {pages} pages")
    log(f"ocr: done ({done}/{len(todo)} files, {pages} pages)")
