"""
weather_scheduler.py — Runs weather data fetching on a schedule.

Location: app/sources/weather/weather_scheduler.py

Fetches:
  - Active alerts every 2 minutes
  - Hourly forecast every 30 minutes

Usage (from project root):
    python app/sources/weather/weather_scheduler.py

Runs until you press Ctrl+C.
"""

import time
import threading
from datetime import datetime, timezone
from weather_source import fetch_active_alerts, fetch_hourly_forecast

# ──────────────────────────────────────────────
# Schedule intervals (in seconds)
# ──────────────────────────────────────────────
ALERT_INTERVAL = 2 * 60       # every 2 minutes
FORECAST_INTERVAL = 30 * 60   # every 30 minutes


def run_alerts_loop():
    """Fetch alerts on a loop."""
    while True:
        try:
            now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            print(f"\n⏰ [{now}] Running scheduled alert fetch...")
            fetch_active_alerts()
        except Exception as e:
            print(f"  ❌ Alert fetch error: {e}")

        time.sleep(ALERT_INTERVAL)


def run_forecast_loop():
    """Fetch hourly forecast on a loop."""
    while True:
        try:
            now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            print(f"\n⏰ [{now}] Running scheduled forecast fetch...")
            fetch_hourly_forecast()
        except Exception as e:
            print(f"  ❌ Forecast fetch error: {e}")

        time.sleep(FORECAST_INTERVAL)


def main():
    print("\n🌦️  Weather Scheduler — Arlington, VA")
    print(f"    Alerts:   every {ALERT_INTERVAL // 60} minutes")
    print(f"    Forecast: every {FORECAST_INTERVAL // 60} minutes")
    print("    Press Ctrl+C to stop\n")

    # Run initial fetch immediately
    print("=" * 50)
    print("  Running initial fetch...")
    print("=" * 50)
    fetch_active_alerts()
    fetch_hourly_forecast()

    # Start background threads for scheduled fetching
    alert_thread = threading.Thread(target=run_alerts_loop, daemon=True)
    forecast_thread = threading.Thread(target=run_forecast_loop, daemon=True)

    alert_thread.start()
    forecast_thread.start()

    print("\n" + "=" * 50)
    print("  ✅ Scheduler running. Ctrl+C to stop.")
    print("=" * 50)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped.\n")


if __name__ == "__main__":
    main()