"""Block 2: the same tools served over MCP, so any harness (Pi, Claude Code...) can call them.

    python -m oracle.mcp_server        # stdio transport
"""
from mcp.server.mcpserver import MCPServer

from oracle import tools

server = MCPServer("night-oracle")


@server.tool()
def predict_night(day: str, rain: bool = False, match: bool = False) -> dict:
    """Predict orders for one night (YYYY-MM-DD or weekday name), a 90% range and the staffing call."""
    return tools.predict_night(day, rain, match)


@server.tool()
def ask_data(code: str) -> dict:
    """Run safe pandas code on the clean sales table `df`; the code must set `result`."""
    return tools.ask_data(code)


@server.tool()
def save_rule(text: str) -> dict:
    """Save a house rule from the manager."""
    return tools.save_rule(text)


if __name__ == "__main__":
    server.run("stdio")
