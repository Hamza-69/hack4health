"""The agent's view of module tools: every registered module's MCP tools under one namespace.

Tool names are `<module>__<tool>`. Calls carry a fresh user token in `_meta`, so the model
never sees or chooses the user id.
"""

import logging
import uuid

from h4h.tokens import USER_TOKEN_META_KEY
from mcp import Client
from mcp_types import CallToolResult, Tool

from core import tokens
from core.registry import load_modules

SEPARATOR = "__"

log = logging.getLogger(__name__)


async def list_tools() -> list[Tool]:
    """All tools of all registered modules. A module that is down is skipped, not fatal."""
    found = []
    for module in load_modules().values():
        try:
            async with Client(module.mcp_url) as client:
                result = await client.list_tools()
        except Exception as e:
            log.warning("module %s unreachable at %s: %s", module.name, module.mcp_url, e)
            continue
        found += [
            tool.model_copy(update={"name": f"{module.name}{SEPARATOR}{tool.name}"})
            for tool in result.tools
        ]
    return found


async def call_tool(user_id: uuid.UUID, name: str, arguments: dict | None = None) -> CallToolResult:
    module_name, _, tool = name.partition(SEPARATOR)
    module = load_modules().get(module_name)
    if module is None or not tool:
        raise ValueError(f"unknown tool {name!r}; expected <module>{SEPARATOR}<tool>")
    meta = {USER_TOKEN_META_KEY: tokens.user_token(user_id, module.name)}
    async with Client(module.mcp_url) as client:
        return await client.call_tool(tool, arguments or {}, meta=meta)
