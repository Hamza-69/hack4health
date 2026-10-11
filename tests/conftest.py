import os
import tempfile
from pathlib import Path

import pytest

# Throwaway signing keys and one-entry registries, set before the core reads them.
_tmp = Path(tempfile.mkdtemp())
os.environ["KEYS_DIR"] = str(_tmp / "keys")
os.environ["MODULES_CONFIG"] = str(_tmp / "modules.toml")
os.environ["CLIENTS_CONFIG"] = str(_tmp / "clients.toml")
(_tmp / "modules.toml").write_text('[testmod]\nurl = "http://localhost:9999"\n')
(_tmp / "clients.toml").write_text('[wa]\nurl = "http://client.test"\n')
from sqlalchemy import make_url, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import core.models  # noqa: F401
from core import runs, tokens
from core.db import Base

tokens.generate_keys()

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hack4health_test"
)


async def ensure_database(url: str) -> None:
    url = make_url(url)
    admin = create_async_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        await admin.dispose()


@pytest.fixture
async def session():
    """A session on a freshly created schema. Skips when no Postgres is running."""
    try:
        await ensure_database(TEST_DATABASE_URL)
    except (OSError, DBAPIError) as e:
        pytest.skip(f"no Postgres at {TEST_DATABASE_URL} ({e})")

    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as s:
        yield s
    await engine.dispose()


@pytest.fixture(autouse=True)
def started_runs(monkeypatch):
    """Record agent runs instead of starting them, so no test reaches a model by accident."""
    started = []
    monkeypatch.setattr(runs, "start", lambda user_id, since: started.append((user_id, since)))
    return started
