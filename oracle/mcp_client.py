"""A small MCP client: lets OUR harness call the tools through the MCP server (instead of directly).

Each call starts the server (stdio), calls one tool and stops it: simple and easy to explain,
a bit slower (~1-2 s per call).
"""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from oracle import config

PARAMS = StdioServerParameters(command=sys.executable, args=["-m", "oracle.mcp_server"],
                               cwd=str(config.ROOT))


async def _session(fn):
    async with stdio_client(PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await fn(session)


def list_schemas() -> list[dict]:
    """Ask the MCP server which tools it has, in the format the model understands."""
    async def go(s):
        listed = await s.list_tools()
        return [{"type": "function", "function": {
            "name": t.name, "description": t.description or "", "parameters": t.input_schema}}
            for t in listed.tools]
    return asyncio.run(_session(go))


def call(name: str, args: dict) -> dict:
    """Call one tool on the MCP server and return its JSON result."""
    async def go(s):
        res = await s.call_tool(name, args)
        text = res.content[0].text if res.content else "{}"
        if getattr(res, "isError", False) or getattr(res, "is_error", False):
            return {"error": text}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"result": text}
    return asyncio.run(_session(go))
