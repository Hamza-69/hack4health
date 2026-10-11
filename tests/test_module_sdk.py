import uuid

import jwt
import pytest
from h4h import Module
from h4h.tokens import USER_TOKEN_META_KEY
from mcp import Client

from core import tokens


class LocalKeys:
    """Stands in for the core's JWKS endpoint, so the module verifies without HTTP."""

    def get_signing_key_from_jwt(self, token):
        return jwt.PyJWK(tokens.jwks()["keys"][0])


@pytest.fixture
def module():
    module = Module("testmod")
    module._jwks = LocalKeys()

    @module.mcp.tool()
    async def careless() -> str:
        """A tool that forgets to call module.user(ctx)."""
        return "ran"

    return module


def meta(token: str) -> dict:
    return {USER_TOKEN_META_KEY: token}


async def test_tool_runs_with_a_valid_user_token(module):
    async with Client(module.mcp) as client:
        result = await client.call_tool("careless", {}, meta=meta(tokens.user_token(uuid.uuid4(), "testmod")))
    assert not result.is_error


@pytest.mark.parametrize(
    "call_meta",
    [None, meta("not-a-token"), meta(tokens.user_token(uuid.uuid4(), "othermod"))],
    ids=["no token", "garbage", "other module"],
)
async def test_tool_is_refused_without_a_valid_user_token(module, call_meta):
    async with Client(module.mcp) as client:
        result = await client.call_tool("careless", {}, meta=call_meta)
    assert result.is_error
    assert "ran" not in result.content[0].text


async def test_listing_tools_needs_no_token(module):
    async with Client(module.mcp) as client:
        assert [t.name for t in (await client.list_tools()).tools] == ["careless"]


def test_mask_personal_hides_names_numbers_and_emails_only():
    from h4h.privacy import mask_personal

    assert mask_personal("بيي اسمو علي حداد وبدو عملية فتق") == "بيي اسمو [name] وبدو عملية فتق"
    assert mask_personal("my name is Ali Haddad and I need IVIG") == "my name is [name] and I need IVIG"
    assert mask_personal("ismi Rami w baddi saydaliye") == "ismi [name] w baddi saydaliye"
    assert mask_personal("call +961 70 123 456 or 03/123456") == "call [number] or [number]"
    assert mask_personal("رقمي ٠٣١٢٣٤٥٦، ali@gmail.com") == "رقمي [number]، [email]"
    for kept in ("شو رقم 1214 و 1787", "Panadol 500mg price", "they asked 1,500,000 LBP", "Concor 5 vs Concor 10"):
        assert mask_personal(kept) == kept
