"""
news_scheduler.py — Runs news ingestion + processing on a schedule.

Location: app/sources/news/news_scheduler.py

Fetches news every 15 minutes, processes immediately after.

Usage (from project root):
    cd app/sources/news
    python news_scheduler.py

Runs until you press Ctrl+C.
"""

import time
import threading
from datetime import datetime, timezone
from news_source import fetch_all_news
from news_processor import process_news

# ──────────────────────────────────────────────
# Schedule interval (in seconds)
# ──────────────────────────────────────────────
NEWS_INTERVAL = 15 * 60  # every 15 minutes


def run_news_loop():
    """Fetch and process news on a loop."""
    while True:
        try:
            now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            print(f"\n⏰ [{now}] Running scheduled news fetch + process...")

            # Step 1: Ingest new articles
            fetch_all_news(filter_relevant=True)

            # Step 2: Process them immediately
            process_news()

        except Exception as e:
            print(f"  ❌ News cycle error: {e}")

        time.sleep(NEWS_INTERVAL)


def main():
    print("\n📰 News Scheduler — Arlington, VA")
    print(f"    Fetch + process: every {NEWS_INTERVAL // 60} minutes")
    print("    Press Ctrl+C to stop\n")

    # Run initial fetch immediately
    print("=" * 50)
    print("  Running initial fetch + process...")
    print("=" * 50)
    fetch_all_news(filter_relevant=True)
    process_news()

    # Start background thread
    news_thread = threading.Thread(target=run_news_loop, daemon=True)
    news_thread.start()

    print("\n" + "=" * 50)
    print("  ✅ Scheduler running. Ctrl+C to stop.")
    print("=" * 50)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 News scheduler stopped.\n")


if __name__ == "__main__":
    main()