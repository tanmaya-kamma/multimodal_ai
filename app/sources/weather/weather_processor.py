"""
weather_processor.py — Reads raw_weather table, assigns H3 cells,
calculates severity scores, writes to processed_weather table.

Location: app/sources/weather/weather_processor.py

Usage (from project root):
    python app/sources/weather/weather_processor.py
"""

import json
import sqlite3
import h3
from pathlib import Path
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
H3_RESOLUTION = 8

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"

# NWS severity → numeric score
ALERT_SEVERITY_MAP = {
    "Extreme": 1.0,
    "Severe": 0.8,
    "Moderate": 0.5,
    "Minor": 0.3,
    "Unknown": 0.2,
}

# NWS certainty → confidence score
ALERT_CERTAINTY_MAP = {
    "Observed": 1.0,
    "Likely": 0.8,
    "Possible": 0.5,
    "Unlikely": 0.2,
    "Unknown": 0.3,
}

# Weather event types that impact supply chains
DISRUPTIVE_EVENTS = {
    "Tornado Warning": 1.0,
    "Flash Flood Warning": 0.95,
    "Flood Warning": 0.85,
    "Severe Thunderstorm Warning": 0.8,
    "Winter Storm Warning": 0.8,
    "Ice Storm Warning": 0.9,
    "Blizzard Warning": 0.85,
    "Hurricane Warning": 1.0,
    "Tropical Storm Warning": 0.8,
    "Flood Watch": 0.5,
    "Severe Thunderstorm Watch": 0.4,
    "Winter Storm Watch": 0.4,
    "Wind Advisory": 0.3,
    "Dense Fog Advisory": 0.3,
    "Heat Advisory": 0.2,
    "Freeze Warning": 0.3,
}


def get_db():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


# ──────────────────────────────────────────────
# Process Alerts
# ──────────────────────────────────────────────
def process_alerts():
    """
    Read raw weather alert responses, score severity,
    assign H3 cells, write to processed_weather.
    """
    print("\n  [ALERTS] Processing weather alerts...")

    conn = get_db()
    if not conn:
        return

    # Get unprocessed alert records
    rows = conn.execute(
        "SELECT id, lat, lon, response_json, fetched_at FROM raw_weather"
    ).fetchall()

    alert_count = 0

    for row_id, lat, lon, response_json_str, fetched_at in rows:
        data = json.loads(response_json_str)

        if data.get("data_type") != "alerts":
            continue

        response = data.get("response", {})
        features = response.get("features", [])

        for feature in features:
            props = feature.get("properties", {})
            event = props.get("event", "")
            nws_severity = props.get("severity", "Unknown")
            certainty = props.get("certainty", "Unknown")
            onset = props.get("onset", fetched_at)

            # Calculate severity: combine NWS severity + event type impact
            base_severity = ALERT_SEVERITY_MAP.get(nws_severity, 0.2)
            event_impact = DISRUPTIVE_EVENTS.get(event, 0.2)
            severity = max(base_severity, event_impact)

            confidence = ALERT_CERTAINTY_MAP.get(certainty, 0.3)

            # Assign H3 cell based on the center of Arlington
            # (alerts are zone-wide, so they apply to all grid points)
            h3_cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

            conn.execute(
                """
                INSERT INTO processed_weather 
                (h3_cell, timestamp_utc, alert_type, severity, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (h3_cell, onset, event, severity, confidence),
            )
            alert_count += 1

            icon = "🔴" if severity >= 0.7 else "🟠" if severity >= 0.4 else "🟡"
            print(f"    {icon} {event}: severity={severity:.2f}, confidence={confidence:.2f}")

    conn.commit()
    conn.close()

    if alert_count == 0:
        print("    ℹ️  No active alerts to process")
    else:
        print(f"    ✅ Processed {alert_count} alerts")


# ──────────────────────────────────────────────
# Process Hourly Forecasts
# ──────────────────────────────────────────────
def process_forecasts():
    """
    Read raw hourly forecast responses, extract conditions,
    calculate disruption severity per grid point, write to processed_weather.
    """
    print("\n  [FORECAST] Processing hourly forecasts...")

    conn = get_db()
    if not conn:
        return

    # Clear previous processed forecast entries
    conn.execute("DELETE FROM processed_weather WHERE alert_type LIKE 'forecast_%'")

    rows = conn.execute(
        "SELECT id, lat, lon, response_json, fetched_at FROM raw_weather"
    ).fetchall()

    forecast_count = 0

    for row_id, lat, lon, response_json_str, fetched_at in rows:
        data = json.loads(response_json_str)

        if data.get("data_type") != "hourly_forecast":
            continue

        point_name = data.get("point_name", "Unknown")
        response = data.get("response", {})
        periods = response.get("properties", {}).get("periods", [])

        # Process next 6 hours (most relevant for immediate disruptions)
        for period in periods[:6]:
            temp = period.get("temperature")
            temp_unit = period.get("temperatureUnit", "F")
            wind_str = period.get("windSpeed", "0 mph")
            precip_prob = period.get("probabilityOfPrecipitation", {}).get("value") or 0
            forecast = period.get("shortForecast", "")
            start_time = period.get("startTime", fetched_at)

            # Parse wind speed (comes as "10 mph" or "10 to 15 mph")
            try:
                wind_parts = wind_str.replace(" mph", "").split(" to ")
                wind_speed = float(wind_parts[-1])
            except (ValueError, IndexError):
                wind_speed = 0.0

            # Calculate disruption severity from conditions
            severity = calculate_forecast_severity(
                temp, temp_unit, wind_speed, precip_prob, forecast
            )

            # Only store if there's meaningful disruption potential
            if severity < 0.1:
                continue

            h3_cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

            conn.execute(
                """
                INSERT INTO processed_weather 
                (h3_cell, timestamp_utc, alert_type, temperature, wind_speed, 
                 precipitation_mm, severity, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    h3_cell,
                    start_time,
                    f"forecast_{forecast.lower().replace(' ', '_')}",
                    temp,
                    wind_speed,
                    precip_prob,  # storing precip probability, not mm
                    severity,
                    0.6,  # forecasts have moderate confidence
                ),
            )
            forecast_count += 1

    conn.commit()
    conn.close()
    print(f"    ✅ Processed {forecast_count} forecast periods with disruption potential")


def calculate_forecast_severity(temp, temp_unit, wind_speed, precip_prob, forecast_text):
    """
    Calculate a disruption severity score (0.0-1.0) from forecast conditions.
    Higher = more likely to disrupt supply chains.
    """
    severity = 0.0
    forecast_lower = forecast_text.lower()

    # Precipitation probability
    if precip_prob >= 80:
        severity += 0.3
    elif precip_prob >= 50:
        severity += 0.15
    elif precip_prob >= 30:
        severity += 0.05

    # Wind speed (mph)
    if wind_speed >= 50:
        severity += 0.4
    elif wind_speed >= 35:
        severity += 0.25
    elif wind_speed >= 25:
        severity += 0.1

    # Temperature extremes (Fahrenheit)
    if temp_unit == "F" and temp is not None:
        if temp <= 15:
            severity += 0.3  # dangerous cold, icy roads
        elif temp <= 32:
            severity += 0.15  # freezing, possible ice
        elif temp >= 105:
            severity += 0.2  # extreme heat

    # Forecast text keywords
    if any(w in forecast_lower for w in ["tornado", "hurricane"]):
        severity += 0.5
    elif any(w in forecast_lower for w in ["flood", "flooding"]):
        severity += 0.4
    elif any(w in forecast_lower for w in ["blizzard", "ice storm"]):
        severity += 0.35
    elif any(w in forecast_lower for w in ["thunderstorm", "severe"]):
        severity += 0.25
    elif any(w in forecast_lower for w in ["snow", "freezing rain", "sleet"]):
        severity += 0.2
    elif any(w in forecast_lower for w in ["rain", "showers"]):
        severity += 0.05
    elif any(w in forecast_lower for w in ["fog"]):
        severity += 0.1

    return min(severity, 1.0)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    print("\n🔧 Processing weather data → H3 indexed severity scores...\n")

    process_alerts()
    process_forecasts()

    # Summary
    conn = get_db()
    if conn:
        total = conn.execute("SELECT COUNT(*) FROM processed_weather").fetchone()[0]
        cells = conn.execute("SELECT COUNT(DISTINCT h3_cell) FROM processed_weather").fetchone()[0]
        avg_sev = conn.execute("SELECT AVG(severity) FROM processed_weather").fetchone()[0] or 0

        conn.close()

        print("\n" + "=" * 50)
        print(f"  🌦️  Total processed weather records: {total}")
        print(f"  📍 Unique H3 cells: {cells}")
        print(f"  📊 Average severity: {avg_sev:.3f}")
        print("=" * 50)

    print("\n✅ Weather processing complete.\n")


if __name__ == "__main__":
    main()