"""FastAPI dependencies: database session, logged-in admin, calling module."""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from h4h.tokens import TokenType
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Session
from core.models import Admin
from core.registry import ModuleConfig, load_modules
from core.tokens import verify_core_token

bearer = HTTPBearer()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with Session() as session:
        yield session


DB = Annotated[AsyncSession, Depends(get_session)]
Credentials = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]


def _claims(credentials: HTTPAuthorizationCredentials, typ: TokenType) -> dict:
    try:
        return verify_core_token(credentials.credentials, typ)
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"invalid token: {e}") from e


async def current_admin(credentials: Credentials, session: DB) -> Admin:
    claims = _claims(credentials, TokenType.SESSION)
    admin = await session.get(Admin, uuid.UUID(claims["sub"]))
    if admin is None:
        raise HTTPException(401, "admin no longer exists")
    return admin


async def current_module(credentials: Credentials) -> ModuleConfig:
    claims = _claims(credentials, TokenType.MODULE)
    module = load_modules().get(claims["sub"])
    if module is None:
        raise HTTPException(401, f"module {claims['sub']!r} is not in the registry")
    return module


CurrentAdmin = Annotated[Admin, Depends(current_admin)]
CurrentModule = Annotated[ModuleConfig, Depends(current_module)]
