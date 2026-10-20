import asyncio
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# QWeather API only (English): GeoAPI city lookup, then current conditions and the
# daily forecast for the city's coordinates. Every QWeather account has its own
# API host (console → Settings); the key only works on that host.
GET_WEATHER_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Get the current weather and the forecast for the next days. "
            "The user's local weather is already in the context; call this for other cities, "
            "or when the context says local weather is unavailable. Never guess the weather."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name in English, e.g. Beijing or London. Omit if the user names no place.",
                },
            },
        },
    },
}

FORECAST_DAYS = 7
CACHE_SECONDS = 600


def _fmt(measure) -> str:
    """{"value": 7.37, "unit": "°C"} -> "7°C" """
    if not isinstance(measure, dict) or measure.get("value") is None:
        return "?"
    return f"{round(measure['value'])}{measure.get('unit', '')}"


def _pct(fraction) -> str:
    return f"{round(fraction * 100)}%" if isinstance(fraction, (int, float)) else "?"


class QWeatherError(RuntimeError):
    def __init__(self, status, detail):
        super().__init__(f"QWeather HTTP {status}")
        self.status, self.detail = status, detail


async def _get(client, api_host, api_key, path, **params):
    started = time.monotonic()
    response = await client.get(
        f"https://{api_host}{path}",
        params={"lang": "en", **params},
        headers={"X-QW-Api-Key": api_key},
    )
    logger.bind(tag=TAG).info(f"QWeather {path}: HTTP {response.status_code} in {time.monotonic() - started:.2f}s")
    if response.status_code != 200:
        detail = response.text[:200]
        logger.bind(tag=TAG).error(f"QWeather {path} failed: HTTP {response.status_code} {detail}")
        raise QWeatherError(response.status_code, detail)
    return response.json()


def _build_report(city, current, daily) -> str:
    tz = ZoneInfo(city.get("tz") or "UTC")
    place = ", ".join(p for p in (city.get("name"), city.get("adm1"), city.get("country")) if p)
    now = datetime.now(tz)
    lines = [f"Weather for {place} (local time {now:%a %b %d, %H:%M}).", ""]

    wind = current.get("wind", {})
    lines.append(
        "Now: {cond}, {temp} (feels like {feels}), humidity {hum}, wind {dir} {speed}, precipitation {rain}.".format(
            cond=current.get("condition", {}).get("text", "unknown"),
            temp=_fmt(current.get("temperature")),
            feels=_fmt(current.get("feelsLike")),
            hum=_pct(current.get("humidity")),
            dir=wind.get("direction", {}).get("compass", "").upper(),
            speed=_fmt(wind.get("speed")),
            rain=_fmt(current.get("precipitation", {}).get("amount")),
        )
    )

    lines += ["", "Forecast:"]
    for day in daily.get("days", []):
        # Days are bounded in UTC; label each with the city's local date
        start = datetime.fromisoformat(day["forecastStartTime"].replace("Z", "+00:00"))
        local_date = (start.astimezone(tz) + timedelta(hours=1)).date()
        if local_date < now.date():
            continue
        label = "Today" if local_date == now.date() else (
            "Tomorrow" if local_date == now.date() + timedelta(days=1) else f"{local_date:%a %b %d}"
        )
        daytime, night = day.get("daytime", {}), day.get("nighttime", {})
        rain = max(
            daytime.get("precipitation", {}).get("probability") or 0,
            night.get("precipitation", {}).get("probability") or 0,
        )
        lines.append(
            f"- {label}: {daytime.get('condition', {}).get('text', '?')} by day, "
            f"{night.get('condition', {}).get('text', '?')} at night, "
            f"{_fmt(day.get('temperatureMin'))} to {_fmt(day.get('temperatureMax'))}, "
            f"chance of rain {_pct(rain)}"
        )
    return "\n".join(lines)


class WeatherUnavailable(Exception):
    """The report can't be produced; the message is safe to show the LLM."""


async def fetch_weather_report(weather_config: dict, location: str) -> str:
    """English weather report for a city name or "lon,lat" coordinates (cached)."""
    from core.utils.cache.manager import cache_manager, CacheType

    api_host = weather_config.get("api_host", "")
    api_key = weather_config.get("api_key", "")
    if not api_host or not api_key:
        raise WeatherUnavailable("The weather service is not configured, so the weather can't be checked right now.")
    if not location:
        raise WeatherUnavailable("No city was given and the user's location is unknown; ask the user which city.")

    cache_key = f"qweather_v1_{location.lower()}"
    cached = cache_manager.get(CacheType.WEATHER, cache_key)
    if cached:
        return cached

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            try:
                geo = await _get(client, api_host, api_key, "/geo/v2/city/lookup", location=location, number=1)
            except QWeatherError as e:
                if "no-such-location" not in e.detail:
                    raise
                geo = {}
            cities = geo.get("location") or []
            if not cities:
                raise WeatherUnavailable(f"No city found for '{location}'. Ask the user to check the name.")
            city = cities[0]
            coords = f"{float(city['lat']):.2f}/{float(city['lon']):.2f}"
            current = await _get(client, api_host, api_key, f"/weather/v1/current/{coords}")
            daily = await _get(client, api_host, api_key, f"/weather/v1/daily/{coords}", days=FORECAST_DAYS)
    except WeatherUnavailable:
        raise
    except Exception as e:
        logger.bind(tag=TAG).error(f"Weather lookup failed for {location} after {time.monotonic() - started:.1f}s: {type(e).__name__} {e}")
        raise WeatherUnavailable("The weather service could not be reached; tell the user you can't check the weather right now.")

    report = _build_report(city, current, daily)
    logger.bind(tag=TAG).info(f"Weather for {city.get('name')} fetched in {time.monotonic() - started:.1f}s")
    cache_manager.set(CacheType.WEATHER, cache_key, report, ttl=CACHE_SECONDS)
    return report


@register_function("get_weather", GET_WEATHER_FUNCTION_DESC, ToolType.SYSTEM_CTL)
async def get_weather(conn: "ConnectionHandler", location: str = None, lang: str = None):
    # `lang` is accepted for older callers and ignored: reports are always English
    weather_config = conn.config.get("plugins", {}).get("get_weather", {})
    # No city named: the user's own location (resolved at connect), else the default city
    location = (
        (location or "").strip()
        or getattr(getattr(conn, "prompt_manager", None), "weather_location", None)
        or weather_config.get("default_location", "")
    )
    try:
        return ActionResponse(Action.REQLLM, await fetch_weather_report(weather_config, location), None)
    except WeatherUnavailable as e:
        return ActionResponse(Action.REQLLM, str(e), None)
