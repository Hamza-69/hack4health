import base64
import hashlib
import hmac
import os

# scrypt parameters; stored with each hash so they can change later.
N, R, P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=N, r=R, p=P)
    return f"scrypt${N}${R}${P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    _, n, r, p, salt, digest = stored.split("$")
    actual = hashlib.scrypt(
        password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p)
    )
    return hmac.compare_digest(actual, base64.b64decode(digest))


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()
