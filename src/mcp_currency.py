import logging
import sys
from pathlib import Path
import httpx
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402,F401

log = logging.getLogger("travel.mcp.currency")
mcp = FastMCP("currency")


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between 3-letter currency codes, e.g. 60000, "INR", "SGD"."""
    frm, to = from_currency.strip().upper(), to_currency.strip().upper()
    log.info("Frankfurter request: %s %s -> %s", amount, frm, to)
    try:
        response = httpx.get(
            "https://api.frankfurter.dev/v1/latest",
            timeout=15,
            params={"amount": amount, "base": frm, "symbols": to}
        )
        if response.status_code in (404, 422):
            log.warning("Unsupported currency code: %s or %s", frm, to)
            return f"ERROR: unsupported currency code '{frm}' or '{to}'. Do not guess a rate."
        data = response.raise_for_status().json()
        return f"{amount:,.2f} {frm} = {data['rates'][to]:,.2f} {to} (ECB rate of {data['date']})"
    except Exception as e:
        log.warning("convert_currency failed: %s", e)
        return f"ERROR: currency service unavailable ({e}). Do not guess a rate."


if __name__ == "__main__":
    mcp.run()