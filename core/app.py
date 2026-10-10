from fastapi import FastAPI

from core import admin_api, module_api, tokens

app = FastAPI(title="hack4health core")
app.include_router(admin_api.router)
app.include_router(module_api.router)


@app.get("/.well-known/jwks.json", tags=["tokens"])
def jwks() -> dict:
    """Public key modules use to verify user and admin tokens."""
    return tokens.jwks()
