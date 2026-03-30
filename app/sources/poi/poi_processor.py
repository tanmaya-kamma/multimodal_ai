"""
poi_processor.py — Reads static POI data (gas stations, grocery stores),
assigns H3 cells, writes to processed_pois table.

Location: app/sources/poi/poi_processor.py

Usage (from project root):
    python app/sources/poi/poi_processor.py
"""

import json
import sqlite3
import h3
from pathlib import Path

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
H3_RESOLUTION = 8

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "static"
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"


def get_db():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run setup_db.py first: python app/db/setup_db.py")
        return None
    return sqlite3.connect(DB_PATH)


# ──────────────────────────────────────────────
# Process Gas Stations
# ──────────────────────────────────────────────
def process_gas_stations():
    print("\n  [GAS STATIONS] Processing...")

    filepath = STATIC_DIR / "arlington_gas_stations.json"
    if not filepath.exists():
        print("    ⚠️  arlington_gas_stations.json not found")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    stations = data.get("stations", [])
    print(f"    📄 {len(stations)} gas stations")

    conn = get_db()
    if not conn:
        return

    # Clear existing gas station POIs
    conn.execute("DELETE FROM processed_pois WHERE poi_type = 'gas_station'")

    inserted = 0
    for s in stations:
        lat = s.get("lat")
        lon = s.get("lon")
        if not lat or not lon:
            continue

        cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

        conn.execute(
            """
            INSERT INTO processed_pois (h3_cell, poi_type, name, address, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                cell,
                "gas_station",
                s.get("name"),
                s.get("address"),
                lat,
                lon,
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"    ✅ Inserted {inserted} gas stations into processed_pois")


# ──────────────────────────────────────────────
# Process Grocery Stores
# ──────────────────────────────────────────────
def process_grocery_stores():
    print("\n  [GROCERY STORES] Processing...")

    filepath = STATIC_DIR / "arlington_grocery_stores.json"
    if not filepath.exists():
        print("    ⚠️  arlington_grocery_stores.json not found")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    stores = data.get("stores", [])
    print(f"    📄 {len(stores)} grocery stores")

    conn = get_db()
    if not conn:
        return

    # Clear existing grocery POIs
    conn.execute("DELETE FROM processed_pois WHERE poi_type IN ('grocery_store', 'supermarket', 'convenience', 'greengrocer')")

    inserted = 0
    for s in stores:
        lat = s.get("lat")
        lon = s.get("lon")
        if not lat or not lon:
            continue

        cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

        # Use shop_type as the poi_type for more detail
        poi_type = s.get("shop_type", "grocery_store")

        conn.execute(
            """
            INSERT INTO processed_pois (h3_cell, poi_type, name, address, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                cell,
                poi_type,
                s.get("name"),
                s.get("address"),
                lat,
                lon,
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"    ✅ Inserted {inserted} grocery stores into processed_pois")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    print("\n🔧 Processing POI data → H3 indexed records...\n")

    process_gas_stations()
    process_grocery_stores()

    # Summary
    conn = get_db()
    if conn:
        gas = conn.execute("SELECT COUNT(*) FROM processed_pois WHERE poi_type = 'gas_station'").fetchone()[0]
        grocery = conn.execute("SELECT COUNT(*) FROM processed_pois WHERE poi_type != 'gas_station'").fetchone()[0]
        total_cells = conn.execute("SELECT COUNT(DISTINCT h3_cell) FROM processed_pois").fetchone()[0]

        conn.close()

        print("\n" + "=" * 50)
        print(f"  ⛽ Gas stations:   {gas}")
        print(f"  🛒 Grocery stores: {grocery}")
        print(f"  📍 Unique H3 cells: {total_cells}")
        print("=" * 50)

    print("\n✅ POI processing complete.\n")


if __name__ == "__main__":
    main()