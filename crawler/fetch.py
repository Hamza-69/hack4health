"""Polite, resumable async HTTP layer.

* at most MAX_CONCURRENCY requests in flight, DELAY_SECONDS pause per request
* 30 s timeout, 3 retries with exponential backoff
* every successful HTML response is cached (gzip) under data/state/cache/,
  and its URL is appended to data/state/visited.txt -> re-running never refetches
* failures go to data/failed_urls.txt (url<TAB>reason<TAB>time)
"""
from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import config as C


@dataclass
class Resp:
    url: str
    status: int
    text: str = ""
    final_url: str = ""
    from_cache: bool = False
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status == 200 and not self.error


def _key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _cache_path(url: str) -> Path:
    k = _key(url)
    return C.CACHE_DIR / k[:2] / (k + ".json.gz")


def is_cloudflare_block(status: int, text: str) -> bool:
    if status in (403, 429, 503):
        t = text[:5000].lower()
        return "cloudflare" in t or "just a moment" in t or "cf-chl" in t or "attention required" in t
    return False


class Fetcher:
    def __init__(self) -> None:
        self.sem = asyncio.Semaphore(C.MAX_CONCURRENCY)
        self.client: Optional[httpx.AsyncClient] = None
        self.visited = set()
        if C.VISITED_TXT.exists():
            self.visited = set(l.strip() for l in C.VISITED_TXT.open(encoding="utf-8") if l.strip())
        self.n_net = 0
        self.n_cache = 0
        self.n_fail = 0
        self.cf_streak = 0
        self._vis_fh = C.VISITED_TXT.open("a", encoding="utf-8")
        self._fail_fh = C.FAILED_TXT.open("a", encoding="utf-8")

    async def __aenter__(self) -> "Fetcher":
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": C.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ar,en;q=0.8",
            },
            timeout=httpx.Timeout(C.TIMEOUT_SECONDS),
            follow_redirects=True,
            http2=False,
        )
        return self

    async def __aexit__(self, *exc) -> None:
        if self.client:
            await self.client.aclose()
        self._vis_fh.close()
        self._fail_fh.close()

    # ------------------------------------------------------------------ cache
    def cached(self, url: str) -> Optional[Resp]:
        p = _cache_path(url)
        if p.exists():
            try:
                d = json.loads(gzip.decompress(p.read_bytes()).decode("utf-8"))
                return Resp(url=url, status=d["status"], text=d["text"], final_url=d.get("final_url", url), from_cache=True)
            except Exception:
                return None
        return None

    def _store(self, r: Resp) -> None:
        p = _cache_path(r.url)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(gzip.compress(json.dumps({"status": r.status, "text": r.text, "final_url": r.final_url}).encode("utf-8")))
        if r.url not in self.visited:
            self.visited.add(r.url)
            self._vis_fh.write(r.url + "\n")
            self._vis_fh.flush()

    def log_failure(self, url: str, reason: str) -> None:
        self.n_fail += 1
        self._fail_fh.write(f"{url}\t{reason}\t{time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        self._fail_fh.flush()

    # ------------------------------------------------------------------ fetch
    async def get(self, url: str, *, ajax: bool = False, use_cache: bool = True, log_fail: bool = True) -> Resp:
        if use_cache:
            c = self.cached(url)
            if c is not None:
                self.n_cache += 1
                return c
        headers = {"X-Requested-With": "XMLHttpRequest"} if ajax else {}
        last_err = ""
        for attempt in range(C.RETRIES + 1):
            async with self.sem:
                try:
                    assert self.client is not None
                    self.client.cookies.clear()
                    r = await self.client.get(url, headers=headers)
                    text = r.text
                    status = r.status_code
                    final = str(r.url)
                except (httpx.TimeoutException, httpx.TransportError) as e:
                    status, text, final = 0, "", url
                    last_err = type(e).__name__
                finally:
                    await asyncio.sleep(C.DELAY_SECONDS + random.random() * 0.2)
            self.n_net += 1
            if status == 200:
                self.cf_streak = 0
                resp = Resp(url=url, status=200, text=text, final_url=final)
                self._store(resp)
                return resp
            if status == 404:
                # a real "not found" is a result, not a failure; cache it so we never ask again
                resp = Resp(url=url, status=404, text="", final_url=final)
                self._store(resp)
                return resp
            if status and is_cloudflare_block(status, text):
                self.cf_streak += 1
                last_err = f"cloudflare_{status}"
                if self.cf_streak >= 10:
                    print(f"  ! {self.cf_streak} Cloudflare blocks in a row - pausing 90 s")
                    await asyncio.sleep(90)
            elif status:
                last_err = f"http_{status}"
            if attempt < C.RETRIES:
                await asyncio.sleep(C.BACKOFF_BASE * (2 ** attempt) + random.random())
        if log_fail:
            self.log_failure(url, last_err or "unknown")
        return Resp(url=url, status=status or 0, error=last_err or "failed")

    async def download(self, url: str, dest: Path) -> Resp:
        """Stream a binary file to dest (skips if already there). Returns Resp with text=content-type."""
        if dest.exists() and dest.stat().st_size > 0:
            self.n_cache += 1
            return Resp(url=url, status=200, text="", final_url=url, from_cache=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        last_err = ""
        for attempt in range(C.RETRIES + 1):
            async with self.sem:
                tmp = dest.with_name(dest.name + ".part")
                try:
                    assert self.client is not None
                    async with self.client.stream("GET", url, timeout=httpx.Timeout(120.0, connect=C.TIMEOUT_SECONDS)) as r:
                        if r.status_code != 200:
                            last_err = f"http_{r.status_code}"
                            status = r.status_code
                        else:
                            size = 0
                            with tmp.open("wb") as fh:
                                async for chunk in r.aiter_bytes(65536):
                                    size += len(chunk)
                                    if size > C.MAX_FILE_BYTES:
                                        raise ValueError("too_large")
                                    fh.write(chunk)
                            tmp.replace(dest)
                            self.n_net += 1
                            return Resp(url=url, status=200, text=r.headers.get("content-type", ""),
                                        final_url=str(r.url) + "|" + r.headers.get("content-disposition", ""))
                except ValueError:
                    tmp.unlink(missing_ok=True)
                    self.log_failure(url, "too_large")
                    return Resp(url=url, status=0, error="too_large")
                except (httpx.TimeoutException, httpx.TransportError) as e:
                    last_err = type(e).__name__
                    status = 0
                finally:
                    await asyncio.sleep(C.DELAY_SECONDS + random.random() * 0.2)
            if status == 404:
                break
            if attempt < C.RETRIES:
                await asyncio.sleep(C.BACKOFF_BASE * (2 ** attempt) + random.random())
        self.log_failure(url, last_err or "download_failed")
        return Resp(url=url, status=0, error=last_err or "download_failed")

    def stats(self) -> str:
        return f"net={self.n_net} cache={self.n_cache} failed={self.n_fail}"
