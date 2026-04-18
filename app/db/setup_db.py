"""
setup_db.py — Creates all SQLite tables for the supply chain project.
Run this ONCE before starting the server or any data fetchers.

Location: app/db/setup_db.py
Creates:  app/data/supply_chain.db

Usage (from project root):
    python app/db/setup_db.py
"""

import sqlite3
import os
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "supply_chain.db"


def create_tables():
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n[DB] Setting up database at: {DB_PATH}\n")

    # ──────────────────────────────────────────
    # RAW TABLES
    # ──────────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_weather (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        lat             REAL NOT NULL,
        lon             REAL NOT NULL,
        response_json   TEXT NOT NULL,
        fetched_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: raw_weather")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_traffic (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id       TEXT NOT NULL,
        image_path      TEXT,
        raw_response    TEXT,
        lat             REAL NOT NULL,
        lon             REAL NOT NULL,
        fetched_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: raw_traffic")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_news (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name     TEXT NOT NULL,
        article_id      TEXT,
        author          TEXT,
        title           TEXT NOT NULL,
        content         TEXT,
        url             TEXT,
        published_at    TEXT,
        fetched_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: raw_news")

    # ──────────────────────────────────────────
    # PROCESSED TABLES
    # ──────────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_weather (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        h3_cell         TEXT NOT NULL,
        timestamp_utc   TEXT NOT NULL,
        alert_type      TEXT,
        temperature     REAL,
        wind_speed      REAL,
        precipitation_mm REAL,
        severity        REAL NOT NULL,
        confidence      REAL NOT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: processed_weather")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_traffic (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        h3_cell         TEXT NOT NULL,
        timestamp_utc   TEXT NOT NULL,
        camera_id       TEXT NOT NULL,
        congestion_level TEXT,
        anomaly_type    TEXT,
        image_path      TEXT,
        severity        REAL NOT NULL,
        confidence      REAL NOT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: processed_traffic")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_news (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        h3_cell             TEXT NOT NULL,
        timestamp_utc       TEXT NOT NULL,
        source_name         TEXT NOT NULL,
        title               TEXT,
        extracted_location  TEXT,
        event_type          TEXT,
        sentiment           REAL,
        urgency             REAL,
        severity            REAL NOT NULL,
        confidence          REAL NOT NULL,
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: processed_news")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_pois (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        h3_cell         TEXT NOT NULL,
        poi_type        TEXT NOT NULL,
        name            TEXT,
        address         TEXT,
        lat             REAL NOT NULL,
        lon             REAL NOT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: processed_pois")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_roads (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        h3_cell         TEXT NOT NULL,
        osm_id          INTEGER,
        road_name       TEXT,
        highway_type    TEXT,
        ref             TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: processed_roads")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_railways (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        h3_cell         TEXT NOT NULL,
        osm_id          INTEGER,
        railway_name    TEXT,
        usage           TEXT,
        service         TEXT,
        operator        TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: processed_railways")

    # ──────────────────────────────────────────
    # FUSION OUTPUT
    # ──────────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        h3_cell         TEXT NOT NULL,
        timestamp_utc   TEXT NOT NULL,
        alert_tier      TEXT NOT NULL,
        combined_severity REAL NOT NULL,
        source_count    INTEGER NOT NULL,
        sources         TEXT,
        affected_pois   TEXT,
        affected_roads  TEXT,
        description     TEXT,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("  DONE: alerts")

    # ──────────────────────────────────────────
    # INDEXES
    # ──────────────────────────────────────────

    indexes = [
        ("idx_weather_h3_time", "processed_weather", "h3_cell, timestamp_utc"),
        ("idx_traffic_h3_time", "processed_traffic", "h3_cell, timestamp_utc"),
        ("idx_news_h3_time", "processed_news", "h3_cell, timestamp_utc"),
        ("idx_pois_h3", "processed_pois", "h3_cell"),
        ("idx_roads_h3", "processed_roads", "h3_cell"),
        ("idx_railways_h3", "processed_railways", "h3_cell"),
        ("idx_alerts_h3_time", "alerts", "h3_cell, timestamp_utc"),
        ("idx_raw_weather_time", "raw_weather", "fetched_at"),
    ]

    print("\n  Creating indexes...")
    for idx_name, table, columns in indexes:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns});")
        print(f"  DONE: {idx_name}")

    conn.commit()
    conn.close()

    print(f"\n[DONE] Database ready at: {DB_PATH}")
    print(f"   File size: {DB_PATH.stat().st_size / 1024:.1f} KB\n")


if __name__ == "__main__":
    create_tables()