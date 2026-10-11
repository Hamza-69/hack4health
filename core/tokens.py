"""Minting tokens. Only the core holds the private key; everyone verifies with the public key."""

import base64
import hashlib
import os
import time
import uuid
from functools import cache
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from h4h.tokens import ALGORITHM, CORE_AUDIENCE, ISSUER, TokenType, verify

USER_TOKEN_TTL = 5 * 60
ADMIN_TOKEN_TTL = 15 * 60
SESSION_TOKEN_TTL = 12 * 60 * 60
REPLY_TOKEN_TTL = 5 * 60


def keys_dir() -> Path:
    return Path(os.environ.get("KEYS_DIR", "keys"))


def generate_keys() -> bool:
    """Create the signing key pair unless it exists. Returns True if new keys were written."""
    path = keys_dir() / "private.pem"
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    pem = Ed25519PrivateKey.generate().private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    path.write_bytes(pem)
    path.chmod(0o600)
    return True


@cache
def _private_key() -> Ed25519PrivateKey:
    path = keys_dir() / "private.pem"
    if not path.exists():
        raise RuntimeError(f"no signing key at {path}; run `uv run h4h init`")
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def _public_key() -> Ed25519PublicKey:
    return _private_key().public_key()


def _key_id() -> str:
    raw = _public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()[:16]


def jwks() -> dict:
    """The public key as a JWK set, served at /.well-known/jwks.json for modules."""
    raw = _public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    x = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    return {"keys": [{"kty": "OKP", "crv": "Ed25519", "x": x, "kid": _key_id(), "alg": ALGORITHM, "use": "sig"}]}


def mint(typ: TokenType, subject: str, audience: str, ttl: int | None, **claims) -> str:
    now = int(time.time())
    payload = {"iss": ISSUER, "aud": audience, "sub": subject, "typ": typ, "iat": now, **claims}
    if ttl is not None:
        payload["exp"] = now + ttl
    return jwt.encode(payload, _private_key(), algorithm=ALGORITHM, headers={"kid": _key_id()})


def user_token(user_id: uuid.UUID, module: str) -> str:
    return mint(TokenType.USER, str(user_id), module, USER_TOKEN_TTL)


def admin_token(admin_id: uuid.UUID, email: str, role: str, module: str) -> str:
    return mint(TokenType.ADMIN, str(admin_id), module, ADMIN_TOKEN_TTL, email=email, role=role)


def session_token(admin_id: uuid.UUID) -> str:
    return mint(TokenType.SESSION, str(admin_id), CORE_AUDIENCE, SESSION_TOKEN_TTL)


def module_token(module: str) -> str:
    """Long-lived. Revoke a module by removing it from modules.toml."""
    return mint(TokenType.MODULE, module, CORE_AUDIENCE, None)


def client_token(app: str) -> str:
    """Long-lived. Revoke a client by removing it from clients.toml."""
    return mint(TokenType.CLIENT, app, CORE_AUDIENCE, None)


def reply_token(app: str) -> str:
    """Sent with each reply so the client can check it comes from the core."""
    return mint(TokenType.REPLY, app, f"client:{app}", REPLY_TOKEN_TTL)


def verify_user_token(token: str, module: str) -> uuid.UUID:
    """A user token the core minted for `module`, handed back by that module as proof."""
    return uuid.UUID(verify(token, _public_key(), audience=module, typ=TokenType.USER)["sub"])


def verify_core_token(token: str, typ: TokenType) -> dict:
    """Verify a token addressed to the core (session, module or client token)."""
    return verify(token, _public_key(), audience=CORE_AUDIENCE, typ=typ)
