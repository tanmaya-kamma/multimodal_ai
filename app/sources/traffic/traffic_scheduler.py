"""
traffic_scheduler.py — Fetches camera images on a schedule.

Location: app/sources/traffic/traffic_scheduler.py

Usage:
    cd app/sources/traffic
    python traffic_scheduler.py

Runs until you press Ctrl+C.
"""

import time
import threading
from datetime import datetime, timezone
from traffic_source import run

# ──────────────────────────────────────────────
# Schedule interval
# ──────────────────────────────────────────────
TRAFFIC_INTERVAL = 5 * 60  # every 5 minutes


def run_traffic_loop():
    while True:
        try:
            now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            print(f"\n⏰ [{now}] Running scheduled camera fetch...")
            run()
        except Exception as e:
            print(f"  ❌ Traffic fetch error: {e}")

        time.sleep(TRAFFIC_INTERVAL)


def main():
    print("\n📸 Traffic Camera Scheduler — Arlington, VA")
    print(f"    Fetch images: every {TRAFFIC_INTERVAL // 60} minutes")
    print("    Press Ctrl+C to stop\n")

    # Initial fetch
    print("=" * 50)
    print("  Running initial fetch...")
    print("=" * 50)
    run()

    # Background thread
    traffic_thread = threading.Thread(target=run_traffic_loop, daemon=True)
    traffic_thread.start()

    print("\n" + "=" * 50)
    print("  ✅ Scheduler running. Ctrl+C to stop.")
    print("=" * 50)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Traffic scheduler stopped.\n")


if __name__ == "__main__":
    main()