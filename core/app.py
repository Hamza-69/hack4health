import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core import admin_api, agent_api, module_api, runs, tokens


@asynccontextmanager
async def lifespan(_: FastAPI):
    sweeper = asyncio.create_task(runs.sweep_forever())
    yield
    sweeper.cancel()
    await runs.stop_all()


app = FastAPI(title="hack4health core", lifespan=lifespan)
app.include_router(admin_api.router)
app.include_router(module_api.router)
app.include_router(agent_api.router)


@app.get("/.well-known/jwks.json", tags=["tokens"])
def jwks() -> dict:
    """Public key modules use to verify user and admin tokens."""
    return tokens.jwks()
