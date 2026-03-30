"""
weather_source.py — Fetches live weather data for Arlington, VA
from the National Weather Service API (api.weather.gov).

Location: app/sources/weather/weather_source.py

Two data types fetched:
  1. Active weather alerts — zone-wide (covers all of Arlington)
  2. Hourly forecast — at 6 grid points spread across the county

Both are stored in raw_weather table in the SQLite database.

Usage:
    python app/sources/weather/weather_source.py
"""

import httpx
import sqlite3
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
NWS_BASE = "https://api.weather.gov"
NWS_HEADERS = {
    "User-Agent": "(SupplyChainDisruptionApp, contact@example.com)",
    "Accept": "application/geo+json",
}

ARLINGTON_ZONE = "VAZ054"

# 6 grid points spread across Arlington County
# Covers north, south, east, west, center, and Pentagon area
ARLINGTON_GRID_POINTS = [
    {"name": "North Arlington (Ballston)",     "lat": 38.882, "lon": -77.112},
    {"name": "South Arlington (Pentagon City)", "lat": 38.862, "lon": -77.059},
    {"name": "West Arlington (Falls Church)",   "lat": 38.875, "lon": -77.150},
    {"name": "East Arlington (Crystal City)",   "lat": 38.856, "lon": -77.049},
    {"name": "Central Arlington (Clarendon)",   "lat": 38.887, "lon": -77.094},
    {"name": "Northwest Arlington (Lee Hwy)",   "lat": 38.904, "lon": -77.130},
]

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"

# Grid info cache (avoids repeat /points lookups)
_grid_cache = {}


# ──────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────
def get_db():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run setup_db.py first: python app/db/setup_db.py")
        return None
    return sqlite3.connect(DB_PATH)


def store_raw_weather(data_type: str, lat: float, lon: float, response_json: dict, point_name: str =""):
    conn = get_db()
    if not conn:
        return

    conn.execute(
        """
        INSERT INTO raw_weather (lat, lon, response_json, fetched_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            lat,
            lon,
            json.dumps({
                "data_type": data_type,
                "point_name": point_name,
                "response": response_json,
            }),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# NWS API helpers
# ──────────────────────────────────────────────
def nws_get(url: str, timeout: int = 30) -> dict | None:
    with httpx.Client(timeout=timeout, headers=NWS_HEADERS) as client:
        try:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            print(f"    ❌ NWS API error ({e.response.status_code}): {e.response.text[:200]}")
            return None
        except httpx.TimeoutException:
            print("    ❌ NWS API timed out")
            return None
        except Exception as e:
            print(f"    ❌ NWS API error: {e}")
            return None


def resolve_grid(lat: float, lon: float) -> dict | None:
    cache_key = f"{lat},{lon}"
    if cache_key in _grid_cache:
        return _grid_cache[cache_key]

    data = nws_get(f"{NWS_BASE}/points/{lat},{lon}")
    if not data:
        return None

    props = data.get("properties", {})
    grid_info = {
        "wfo": props.get("gridId"),
        "grid_x": props.get("gridX"),
        "grid_y": props.get("gridY"),
        "forecast_hourly_url": props.get("forecastHourly"),
    }

    _grid_cache[cache_key] = grid_info
    return grid_info


# ──────────────────────────────────────────────
# Fetchers
# ──────────────────────────────────────────────
def fetch_active_alerts() -> dict | None:
    """
    Fetch active weather alerts for all of Arlington.
    One call covers the entire zone — no need for multiple points.
    """
    print("\n  [ALERTS] Fetching active weather alerts for Arlington...")
    url = f"{NWS_BASE}/alerts/active/zone/{ARLINGTON_ZONE}"
    data = nws_get(url)

    if data is None:
        return None

    features = data.get("features", [])
    print(f"    ✅ Found {len(features)} active alert(s)")

    alerts = []
    for feature in features:
        props = feature.get("properties", {})
        alert = {
            "id": props.get("id"),
            "event": props.get("event"),
            "severity": props.get("severity"),
            "certainty": props.get("certainty"),
            "urgency": props.get("urgency"),
            "headline": props.get("headline"),
            "description": props.get("description"),
            "instruction": props.get("instruction"),
            "onset": props.get("onset"),
            "expires": props.get("expires"),
            "sender_name": props.get("senderName"),
            "affected_zones": props.get("affectedZones", []),
            "area_desc": props.get("areaDesc"),
        }
        alerts.append(alert)

        if alert["event"]:
            icon = {"Minor": "🟡", "Moderate": "🟠", "Severe": "🔴", "Extreme": "🔴"}.get(alert["severity"], "⚪")
            print(f"    {icon} {alert['event']} — {alert['severity']}")

    # Store once for the whole zone
    store_raw_weather(
        data_type="alerts",
        lat=38.8816,
        lon=-77.0910,
        response_json=data,
        point_name="Arlington Zone VAZ054",
    )

    return {"alert_count": len(alerts), "alerts": alerts}


def fetch_hourly_forecast_for_point(point: dict) -> dict | None:
    """Fetch hourly forecast for a single grid point."""
    name = point["name"]
    lat = point["lat"]
    lon = point["lon"]

    # Resolve grid coordinates
    grid = resolve_grid(lat, lon)
    if not grid:
        print(f"    ❌ {name}: Could not resolve grid")
        return None

    url = grid["forecast_hourly_url"]
    data = nws_get(url)

    if data is None:
        print(f"    ❌ {name}: Forecast fetch failed")
        return None

    periods = data.get("properties", {}).get("periods", [])

    # Parse first 24 hours
    hourly = []
    for period in periods[:24]:
        hourly.append({
            "start_time": period.get("startTime"),
            "end_time": period.get("endTime"),
            "temperature": period.get("temperature"),
            "temperature_unit": period.get("temperatureUnit"),
            "wind_speed": period.get("windSpeed"),
            "wind_direction": period.get("windDirection"),
            "precipitation_probability": period.get("probabilityOfPrecipitation", {}).get("value"),
            "humidity": period.get("relativeHumidity", {}).get("value"),
            "short_forecast": period.get("shortForecast"),
            "is_daytime": period.get("isDaytime"),
        })

    # Store raw response
    store_raw_weather(
        data_type="hourly_forecast",
        lat=lat,
        lon=lon,
        response_json=data,
        point_name=name,
    )

    # Quick summary
    if hourly:
        h = hourly[0]
        precip = h["precipitation_probability"] or 0
        print(f"    ✅ {name}: {h['temperature']}°{h['temperature_unit']} | Precip: {precip}% | {h['short_forecast']}")

    return {
        "point_name": name,
        "lat": lat,
        "lon": lon,
        "grid": grid,
        "next_24h": hourly,
    }


def fetch_hourly_forecast() -> list:
    """
    Fetch hourly forecast at all grid points across Arlington.
    Each point is a separate NWS API call with a small delay
    between calls to be respectful to the API.
    """
    print(f"\n  [FORECAST] Fetching hourly forecast at {len(ARLINGTON_GRID_POINTS)} points...")

    # Resolve all grid coordinates first
    print("    📡 Resolving grid coordinates...")
    for point in ARLINGTON_GRID_POINTS:
        grid = resolve_grid(point["lat"], point["lon"])
        if grid:
            print(f"      {point['name']}: {grid['wfo']}/{grid['grid_x']},{grid['grid_y']}")
        time.sleep(0.5)

    print("\n    📡 Fetching forecasts...")
    results = []
    for point in ARLINGTON_GRID_POINTS:
        result = fetch_hourly_forecast_for_point(point)
        if result:
            results.append(result)
        time.sleep(0.5)  # small delay between calls

    print(f"\n    ✅ Fetched forecast for {len(results)}/{len(ARLINGTON_GRID_POINTS)} points")
    return results


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def fetch_all():
    print("\n🌦️  Fetching weather data for Arlington, VA...")
    print(f"📁 Database: {DB_PATH}")
    print(f"📍 Grid points: {len(ARLINGTON_GRID_POINTS)}\n")

    alerts = fetch_active_alerts()
    forecasts = fetch_hourly_forecast()

    print("\n" + "=" * 50)
    if alerts:
        print(f"  🚨 Active alerts: {alerts['alert_count']}")
    print(f"  🌡️  Forecast points fetched: {len(forecasts)}")
    print("=" * 50)
    print("\n✅ Weather data fetched and stored in raw_weather table.\n")

    return {"alerts": alerts, "forecasts": forecasts}


if __name__ == "__main__":
    fetch_all()