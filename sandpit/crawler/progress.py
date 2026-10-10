"""Timestamped progress log: stdout + data/state/progress.log (so teammates can `tail -f` it)."""
from __future__ import annotations

import time

from . import config as C

_LOG = C.STATE / "progress.log"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with _LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
