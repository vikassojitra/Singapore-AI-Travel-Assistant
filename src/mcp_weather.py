import logging
import sys
from pathlib import Path
import httpx
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402,F401

log = logging.getLogger("travel.mcp.weather")
mcp = FastMCP("weather")

CONDITIONS = {
    0: "clear", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "drizzle", 53: "drizzle", 55: "drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 80: "showers",
    81: "showers", 82: "heavy showers", 95: "thunderstorm",
    96: "thunderstorm", 99: "thunderstorm"
}


def fetch(city: str, **params) -> tuple[str, dict]:
    """Look up the city's coordinates, then fetch weather data for them."""
    log.info("Open-Meteo request: city=%s %s", city, params)
    places = httpx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=15
    ).json().get("results")
    if not places:
        raise ValueError(f"unknown city '{city}'")
    p = places[0]
    response = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        timeout=15,
        params={
            "latitude": p["latitude"],
            "longitude": p["longitude"],
            "timezone": "auto",
            **params
        }
    )
    return f"{p['name']}, {p.get('country', '')}", response.raise_for_status().json()


@mcp.tool()
def get_current_weather(city: str = "Singapore") -> str:
    """Current weather for a city."""
    try:
        place, data = fetch(city, current_weather=True)
        w = data["current_weather"]
        return f"{place} now: {CONDITIONS.get(w['weathercode'], 'unknown')}, {w['temperature']}°C, wind {w['windspeed']} km/h"
    except Exception as e:
        log.warning("get_current_weather failed: %s", e)
        return f"ERROR: weather unavailable ({e}). Do not guess the weather."


@mcp.tool()
def get_forecast(city: str = "Singapore", days: int = 3) -> str:
    """Daily forecast for 1-7 days: conditions, temperature range and chance of rain."""
    try:
        place, data = fetch(
            city,
            forecast_days=max(1, min(days, 7)),
            daily="weathercode,temperature_2m_min,temperature_2m_max,precipitation_probability_max"
        )
        d = data["daily"]
        rows = zip(
            d["time"],
            d["weathercode"],
            d["temperature_2m_min"],
            d["temperature_2m_max"],
            d["precipitation_probability_max"]
        )
        return f"Forecast for {place}:\n" + "\n".join(
            f"- {day}: {CONDITIONS.get(code, 'unknown')}, {low}-{high}°C, rain chance {rain}%"
            for day, code, low, high, rain in rows
        )
    except Exception as e:
        log.warning("get_forecast failed: %s", e)
        return f"ERROR: forecast unavailable ({e}). Do not guess the forecast."


if __name__ == "__main__":
    mcp.run()