import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from core import admin_api, agent_api, media, module_api, runs, tokens


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


@app.get("/media/{name}", include_in_schema=False)
def media_file(name: str) -> FileResponse:
    """A photo or PDF a user sent. The random name is the only key."""
    if (path := media.path(name)) is None:
        raise HTTPException(404, "no such file")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=86400", "X-Content-Type-Options": "nosniff"})
