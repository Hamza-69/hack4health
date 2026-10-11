"""The agent's view of module tools: every registered module's MCP tools under one namespace.

Tool names are `<module>__<tool>`. Calls carry a fresh user token in `_meta`, so the model
never sees or chooses the user id.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass

from h4h.tokens import USER_TOKEN_META_KEY
from mcp import Client
from mcp_types import CallToolResult, Tool

from core import tokens
from core.registry import ModuleConfig, load_modules

SEPARATOR = "__"

log = logging.getLogger(__name__)


@dataclass
class ModuleTools:
    name: str
    instructions: str | None  # the module's MCP instructions: how the agent should use its tools
    tools: list[Tool]  # named <module>__<tool>


async def list_modules() -> list[ModuleTools]:
    """Every registered module that is up, with its tools. A module that is down is skipped, not fatal."""
    found = await asyncio.gather(*(_describe(m) for m in load_modules().values()))
    return [m for m in found if m is not None]


async def _describe(module: ModuleConfig) -> ModuleTools | None:
    try:
        async with Client(module.mcp_url) as client:
            result = await client.list_tools()
            instructions = client.instructions
    except Exception as e:
        log.warning("module %s unreachable at %s: %s", module.name, module.mcp_url, e)
        return None
    tools = [
        tool.model_copy(update={"name": f"{module.name}{SEPARATOR}{tool.name}"})
        for tool in result.tools
    ]
    return ModuleTools(module.name, instructions, tools)


async def list_tools() -> list[Tool]:
    """All tools of all registered modules."""
    return [tool for module in await list_modules() for tool in module.tools]


async def call_tool(user_id: uuid.UUID, name: str, arguments: dict | None = None) -> CallToolResult:
    module_name, _, tool = name.partition(SEPARATOR)
    module = load_modules().get(module_name)
    if module is None or not tool:
        raise ValueError(f"unknown tool {name!r}; expected <module>{SEPARATOR}<tool>")
    meta = {USER_TOKEN_META_KEY: tokens.user_token(user_id, module.name)}
    async with Client(module.mcp_url) as client:
        return await client.call_tool(tool, arguments or {}, meta=meta)
