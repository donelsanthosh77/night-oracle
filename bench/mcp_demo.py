"""Block 2 evidence: start the MCP server, list its tools, make one real call, save the trace.

    python -m bench.mcp_demo
"""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from oracle import config


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "oracle.mcp_server"],
                                   cwd=str(config.ROOT))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [t.name for t in listed.tools]
            args = {"day": "Friday", "match": True}
            res = await session.call_tool("predict_night", args)
            text = res.content[0].text
            trace = {"tools_listed": names, "call": {"tool": "predict_night", "args": args},
                     "result": json.loads(text)}
    print(json.dumps(trace, indent=2))
    config.TRACES.mkdir(exist_ok=True)
    (config.TRACES / "mcp_call.json").write_text(json.dumps(trace, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
