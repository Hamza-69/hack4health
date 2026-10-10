import asyncio
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from h4h.core_client import CoreClient, CoreError
from h4h.tokens import USER_TOKEN_META_KEY, TokenType, verify

DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/hack4health"

_bearer = HTTPBearer()


@dataclass(frozen=True)
class User:
    """The chat user a tool call is for. Comes from the core-signed token in `_meta`."""

    id: uuid.UUID


@dataclass(frozen=True)
class Admin:
    """The admin panel user calling this module's API. Comes from the admin token."""

    id: uuid.UUID
    email: str
    role: str  # operator | supplier


class Module:
    """Everything a module needs. Create one per module, register tools and routes, call app().

    - `mcp`: the MCP server; tools call `await module.user(ctx)` to get the user.
    - `api`: router mounted at /api for the module's admin UI; every route requires an admin token.
    - `Base`: declarative base whose tables live in this module's own Postgres schema.
    - `db`: session factory; `session` is the same as a FastAPI dependency.
    - `core`: client for the core's module API (tickets, notify).
    """

    def __init__(self, name: str, *, title: str | None = None, instructions: str | None = None):
        load_dotenv(".env")  # the module's own folder; MODULE_TOKEN lives there
        self.name = name
        self.core_url = os.environ.get("CORE_URL", "http://localhost:8000")

        self.mcp = MCPServer(name, title=title, instructions=instructions)
        self.api = APIRouter(prefix="/api", dependencies=[Depends(self.admin)])

        class Base(DeclarativeBase):
            metadata = MetaData(schema=name)

        self.Base = Base
        self.engine = create_async_engine(os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
        self.db = async_sessionmaker(self.engine, expire_on_commit=False)

        self.core = CoreClient(self.core_url, os.environ.get("MODULE_TOKEN"))
        self._jwks = jwt.PyJWKClient(f"{self.core_url}/.well-known/jwks.json")

    async def user(self, ctx: Context) -> User:
        """The user this tool call is for. Raises if the call carries no valid user token."""
        token = (ctx.request_context.meta or {}).get(USER_TOKEN_META_KEY)
        if not token:
            raise ToolError("no user token in _meta; call tools through the core")
        try:
            claims = await self._verify(token, TokenType.USER)
        except jwt.PyJWTError as e:
            raise ToolError(f"invalid user token: {e}") from e
        return User(id=uuid.UUID(claims["sub"]))

    async def admin(
        self, credentials: HTTPAuthorizationCredentials = Depends(_bearer)
    ) -> Admin:
        """FastAPI dependency: the admin calling this module's API."""
        try:
            claims = await self._verify(credentials.credentials, TokenType.ADMIN)
        except jwt.PyJWTError as e:
            raise HTTPException(401, f"invalid admin token: {e}") from e
        return Admin(id=uuid.UUID(claims["sub"]), email=claims["email"], role=claims["role"])

    async def session(self) -> AsyncIterator[AsyncSession]:
        """FastAPI dependency: a database session on this module's schema."""
        async with self.db() as session:
            yield session

    def app(self) -> FastAPI:
        """Build the module's server: MCP at /mcp, admin API at /api, built UI at /ui.

        Call it after the modules that register tools and routes are imported.
        """
        # Without MCP_HOST, only localhost Host headers are accepted (DNS rebinding protection).
        mcp_app = self.mcp.streamable_http_app(
            stateless_http=True, json_response=True, host=os.environ.get("MCP_HOST", "127.0.0.1")
        )

        @asynccontextmanager
        async def lifespan(_: FastAPI):
            async with self.engine.begin() as conn:
                await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.name}"'))
                await conn.run_sync(self.Base.metadata.create_all)
            async with self.mcp.session_manager.run():
                yield
            await self.core.aclose()
            await self.engine.dispose()

        app = FastAPI(title=self.name, lifespan=lifespan)
        app.include_router(self.api)

        @app.exception_handler(CoreError)
        async def core_error(_: Request, e: CoreError) -> JSONResponse:
            return JSONResponse({"detail": e.detail}, status_code=e.status_code)

        if Path("ui/dist").is_dir():
            app.mount("/ui", StaticFiles(directory="ui/dist", html=True), name="ui")
        app.mount("/", mcp_app)
        return app

    async def _verify(self, token: str, typ: TokenType) -> dict:
        key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, token)
        return verify(token, key.key, audience=self.name, typ=typ)
