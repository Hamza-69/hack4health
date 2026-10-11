"""The registries: modules.toml and clients.toml at the repo root. Read on every use, so edits apply live."""

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


@dataclass(frozen=True)
class ClientConfig:
    app: str  # wa | tg | web
    url: str  # the client's service; the core POSTs replies to /messages

    @property
    def messages_url(self) -> str:
        return f"{self.url}/messages"


def clients_config_path() -> Path:
    return Path(os.environ.get("CLIENTS_CONFIG", "clients.toml"))


def load_clients() -> dict[str, ClientConfig]:
    path = clients_config_path()
    if not path.exists():
        return {}
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return {app: ClientConfig(app=app, url=entry["url"].rstrip("/")) for app, entry in raw.items()}
