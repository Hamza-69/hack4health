"""The module registry: modules.toml at the repo root. Read on every use, so edits apply live."""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModuleConfig:
    name: str
    url: str  # module backend: MCP at /mcp, admin API at /api
    ui_url: str  # admin UI embedded by the admin panel
    title: str

    @property
    def mcp_url(self) -> str:
        return f"{self.url}/mcp"


def config_path() -> Path:
    return Path(os.environ.get("MODULES_CONFIG", "modules.toml"))


def load_modules() -> dict[str, ModuleConfig]:
    path = config_path()
    if not path.exists():
        return {}
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return {
        name: ModuleConfig(
            name=name,
            url=entry["url"].rstrip("/"),
            ui_url=entry.get("ui_url") or f"{entry['url'].rstrip('/')}/ui/",
            title=entry.get("title") or name.replace("_", " ").title(),
        )
        for name, entry in raw.items()
    }
