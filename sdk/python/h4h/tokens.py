"""Token rules shared by the core (which signs tokens) and modules (which verify them)."""

import enum

import jwt

ISSUER = "h4h-core"
ALGORITHM = "EdDSA"
CORE_AUDIENCE = "core"

# Key in an MCP request's `_meta` that carries the user token. Set by the core, never by the model.
USER_TOKEN_META_KEY = "h4h/user_token"


class TokenType(enum.StrEnum):
    SESSION = "session"  # admin -> core (admin panel login)
    MODULE = "module"  # module -> core (module API)
    USER = "user"  # core -> module MCP server, in _meta
    ADMIN = "admin"  # admin panel -> module UI -> module backend
    CLIENT = "client"  # chat client -> core (agent API)
    REPLY = "reply"  # core -> chat client, with each reply to send


def verify(token: str, key, *, audience: str, typ: TokenType) -> dict:
    """Check signature, issuer, audience and expiry; return the claims. Raises jwt.PyJWTError."""
    claims = jwt.decode(
        token,
        key,
        algorithms=[ALGORITHM],
        audience=audience,
        issuer=ISSUER,
        options={"require": ["iss", "aud", "sub"]},
    )
    if claims.get("typ") != typ:
        raise jwt.InvalidTokenError(f"expected a {typ} token")
    return claims
