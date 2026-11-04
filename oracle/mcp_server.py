"""Block 2: the same tools served over MCP, so any harness (ours, Pi, Claude Code...) can call them.

    python -m oracle.mcp_server        # stdio transport
"""
from mcp.server.mcpserver import MCPServer

from oracle import tools

server = MCPServer("night-oracle")
DESC = {s["function"]["name"]: s["function"]["description"] for s in tools.SCHEMAS}


@server.tool(description=DESC["predict_night"])
def predict_night(day: str, rain: bool = False, weather: str = "normal",
                  biryani_special: bool = False) -> dict:
    return tools.call("predict_night", {"day": day, "rain": rain, "weather": weather,
                                        "biryani_special": biryani_special})


@server.tool(description=DESC["stats"])
def stats(metric: str, year: int | None = None, month: int | None = None, day_name: str | None = None,
          rain: bool | None = None, biryani: bool | None = None, before_holiday: bool | None = None,
          start_of_month: bool | None = None, guests_above: int | None = None,
          guests_equal: int | None = None, by_day: bool = False) -> dict:
    args = {k: v for k, v in locals().items() if v is not None}
    return tools.call("stats", args)


@server.tool(description=DESC["ask_data"])
def ask_data(code: str) -> dict:
    return tools.call("ask_data", {"code": code})


@server.tool(description=DESC["save_rule"])
def save_rule(text: str) -> dict:
    return tools.call("save_rule", {"text": text})


if __name__ == "__main__":
    server.run("stdio")
