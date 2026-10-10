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
