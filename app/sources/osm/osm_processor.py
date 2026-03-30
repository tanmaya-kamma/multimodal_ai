"""
osm_processor.py — Reads static OSM road and railway data,
assigns H3 cells to each segment, writes to processed tables.

Location: app/sources/osm/osm_processor.py

Usage (from project root):
    python app/sources/osm/osm_processor.py
"""

import json
import sqlite3
import h3
from pathlib import Path
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
H3_RESOLUTION = 8  # ~0.74 km² hexagons

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "static"
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def get_db():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run setup_db.py first: python app/db/setup_db.py")
        return None
    return sqlite3.connect(DB_PATH)


def h3_cells_for_polyline(coordinates: list) -> set:
    """
    Given a list of {"lat": ..., "lon": ...} points,
    return the set of H3 cells the polyline passes through.
    """
    cells = set()
    for point in coordinates:
        cell = h3.latlng_to_cell(point["lat"], point["lon"], H3_RESOLUTION)
        cells.add(cell)
    return cells


# ──────────────────────────────────────────────
# Process Roads
# ──────────────────────────────────────────────
def process_roads():
    print("\n  [ROADS] Processing road segments...")

    conn = get_db()
    if not conn:
        return

    # Clear existing processed roads
    conn.execute("DELETE FROM processed_roads")

    total_inserted = 0

    for filename in ["arlington_major_roads.json", "arlington_secondary_roads.json"]:
        filepath = STATIC_DIR / filename
        if not filepath.exists():
            print(f"    ⚠️  {filename} not found, skipping")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        roads = data.get("roads", [])
        print(f"    📄 {filename}: {len(roads)} roads")

        for road in roads:
            coords = road.get("coordinates", [])
            if not coords:
                continue

            cells = h3_cells_for_polyline(coords)

            for cell in cells:
                conn.execute(
                    """
                    INSERT INTO processed_roads (h3_cell, osm_id, road_name, highway_type, ref)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        cell,
                        road.get("osm_id"),
                        road.get("name"),
                        road.get("highway_type"),
                        road.get("ref"),
                    ),
                )
                total_inserted += 1

    conn.commit()
    conn.close()
    print(f"    ✅ Inserted {total_inserted} road-cell records into processed_roads")


# ──────────────────────────────────────────────
# Process Railways
# ──────────────────────────────────────────────
def process_railways():
    print("\n  [RAILWAYS] Processing railway segments...")

    conn = get_db()
    if not conn:
        return

    conn.execute("DELETE FROM processed_railways")

    filepath = STATIC_DIR / "arlington_railways.json"
    if not filepath.exists():
        print("    ⚠️  arlington_railways.json not found, skipping")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    railways = data.get("railways", [])
    print(f"    📄 {len(railways)} railway segments")

    total_inserted = 0
    for rw in railways:
        coords = rw.get("coordinates", [])
        if not coords:
            continue

        cells = h3_cells_for_polyline(coords)

        for cell in cells:
            conn.execute(
                """
                INSERT INTO processed_railways (h3_cell, osm_id, railway_name, usage, service, operator)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    cell,
                    rw.get("osm_id"),
                    rw.get("name"),
                    rw.get("usage"),
                    rw.get("service"),
                    rw.get("operator"),
                ),
            )
            total_inserted += 1

    conn.commit()
    conn.close()
    print(f"    ✅ Inserted {total_inserted} railway-cell records into processed_railways")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    print("\n🔧 Processing OSM data → H3 indexed records...\n")

    process_roads()
    process_railways()

    # Summary
    conn = get_db()
    if conn:
        road_count = conn.execute("SELECT COUNT(*) FROM processed_roads").fetchone()[0]
        rail_count = conn.execute("SELECT COUNT(*) FROM processed_railways").fetchone()[0]

        road_cells = conn.execute("SELECT COUNT(DISTINCT h3_cell) FROM processed_roads").fetchone()[0]
        rail_cells = conn.execute("SELECT COUNT(DISTINCT h3_cell) FROM processed_railways").fetchone()[0]

        conn.close()

        print("\n" + "=" * 50)
        print(f"  🛣️  processed_roads:    {road_count} records across {road_cells} H3 cells")
        print(f"  🚂 processed_railways: {rail_count} records across {rail_cells} H3 cells")
        print("=" * 50)

    print("\n✅ OSM processing complete.\n")


if __name__ == "__main__":
    main()