"""Block 2: the same tools served over MCP, so any harness (Pi, Claude Code...) can call them.

    python -m oracle.mcp_server        # stdio transport
"""
from mcp.server.mcpserver import MCPServer

from oracle import tools

server = MCPServer("night-oracle")


@server.tool()
def predict_night(day: str, rain: bool = False, weather: str = "normal",
                  biryani_special: bool = False) -> dict:
    """Predict evening guests (YYYY-MM-DD or weekday name), a 90% range and the staff plan.
    weather: normal | cool_no_wind | very_cold."""
    return tools.predict_night(day, rain, weather, biryani_special)


@server.tool()
def stats(metric: str, year: int | None = None, month: int | None = None, day_name: str | None = None,
          rain: bool | None = None, biryani: bool | None = None, before_holiday: bool | None = None,
          start_of_month: bool | None = None, guests_above: int | None = None,
          guests_equal: int | None = None, by_day: bool = False) -> dict:
    """mean/sum/count/max/min of guests on past nights, after filters; by_day=True gives one value per weekday."""
    return tools.stats(metric, year, month, day_name, rain, biryani, before_holiday, start_of_month,
                       guests_above, guests_equal, by_day)


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
