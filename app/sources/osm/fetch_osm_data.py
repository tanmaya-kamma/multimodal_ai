"""
fetch_osm_data.py — Run this ONCE to download Arlington, VA OSM data
and save it as local JSON files.

Location: app/sources/osm/fetch_osm_data.py
Saves to: app/data/static/

Usage (from project root):
    python app/sources/osm/fetch_osm_data.py
"""

import httpx
import json
import time
import os
from pathlib import Path

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Save to app/data/static/ (two levels up from app/sources/osm/)
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "static"

# Arlington County, Virginia
ARLINGTON_RELATION_ID = 962190

ARLINGTON_BBOX = {
    "south": 38.827,
    "west": -77.172,
    "north": 38.934,
    "east": -77.032,
}

ARLINGTON_CENTER = {"lat": 38.8816, "lon": -77.0910}


# ──────────────────────────────────────────────
# Overpass query helper with retry
# ──────────────────────────────────────────────
def query_overpass(query: str, timeout: int = 180, retries: int = 3) -> dict:
    with httpx.Client(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                print(f"    📡 Sending query (attempt {attempt + 1}/{retries})...")
                resp = client.post(OVERPASS_URL, data={"data": query})

                if resp.status_code == 429:
                    wait = 20 * (attempt + 1)
                    print(f"    ⏳ Rate limited (429). Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                if resp.status_code == 504:
                    wait = 15 * (attempt + 1)
                    print(f"    ⏳ Gateway timeout (504). Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.TimeoutException:
                wait = 15 * (attempt + 1)
                print(f"    ⏳ Request timed out. Waiting {wait}s...")
                time.sleep(wait)
                continue

    raise Exception("Overpass API failed after all retries.")


# ──────────────────────────────────────────────
# Parsers
# ──────────────────────────────────────────────
def parse_roads(elements: list) -> tuple[list, dict]:
    roads = []
    type_counts = {}
    for el in elements:
        r = {
            "osm_id": el.get("id"),
            "name": el.get("tags", {}).get("name", "Unnamed"),
            "highway_type": el.get("tags", {}).get("highway"),
            "ref": el.get("tags", {}).get("ref"),
            "lanes": el.get("tags", {}).get("lanes"),
            "coordinates": [
                {"lat": p["lat"], "lon": p["lon"]}
                for p in el.get("geometry", [])
            ],
        }
        roads.append(r)
        t = r["highway_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    return roads, type_counts


def save_json(filename: str, data: dict):
    filepath = STATIC_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)
    size_kb = os.path.getsize(filepath) / 1024
    print(f"    💾 Saved {filename} ({size_kb:.1f} KB)")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    os.makedirs(STATIC_DIR, exist_ok=True)
    bb = ARLINGTON_BBOX

    print(f"\n🗺️  Fetching Arlington, VA OSM data...")
    print(f"📁 Saving to: {STATIC_DIR}\n")

    # ── 1. County Boundary ──
    print("[1/4] County boundary (relation {})...".format(ARLINGTON_RELATION_ID))
    try:
        query = f"""
        [out:json][timeout:120];
        relation({ARLINGTON_RELATION_ID});
        way(r:"outer");
        out geom;
        """
        data = query_overpass(query)
        elements = data.get("elements", [])

        outer_coords = []
        for el in elements:
            if el.get("type") == "way" and "geometry" in el:
                coords = [
                    {"lat": p["lat"], "lon": p["lon"]}
                    for p in el["geometry"]
                ]
                outer_coords.append(coords)

        save_json("arlington_boundary.json", {
            "type": "boundary",
            "name": "Arlington County",
            "state": "Virginia",
            "osm_id": ARLINGTON_RELATION_ID,
            "center": ARLINGTON_CENTER,
            "bbox": ARLINGTON_BBOX,
            "outer_rings": outer_coords,
            "ring_count": len(outer_coords),
        })
        print(f"    ✅ Boundary: {len(outer_coords)} rings\n")
    except Exception as e:
        print(f"    ❌ Boundary failed: {e}\n")

    print("    ⏳ Waiting 10s before next query...")
    time.sleep(10)

    # ── 2. Major Roads (motorways, trunks — I-66, I-395, GW Parkway) ──
    print("[2/4] Major roads (motorways, trunks)...")
    try:
        query = f"""
        [out:json][timeout:120];
        (
          way["highway"="motorway"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["highway"="motorway_link"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["highway"="trunk"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["highway"="trunk_link"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
        );
        out geom;
        """
        data = query_overpass(query)
        roads, type_counts = parse_roads(data.get("elements", []))
        save_json("arlington_major_roads.json", {
            "total_roads": len(roads),
            "by_type": type_counts,
            "roads": roads,
        })
        print(f"    ✅ Major roads: {len(roads)} segments\n")
    except Exception as e:
        print(f"    ❌ Major roads failed: {e}\n")

    print("    ⏳ Waiting 10s before next query...")
    time.sleep(10)

    # ── 3. Primary / Secondary Roads (local arterials, delivery routes) ──
    print("[3/4] Primary/secondary roads...")
    try:
        query = f"""
        [out:json][timeout:120];
        (
          way["highway"="primary"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["highway"="secondary"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
        );
        out geom;
        """
        data = query_overpass(query)
        roads, type_counts = parse_roads(data.get("elements", []))
        save_json("arlington_secondary_roads.json", {
            "total_roads": len(roads),
            "by_type": type_counts,
            "roads": roads,
        })
        print(f"    ✅ Primary/Secondary: {len(roads)} segments\n")
    except Exception as e:
        print(f"    ❌ Primary/Secondary roads failed: {e}\n")

    print("    ⏳ Waiting 10s before next query...")
    time.sleep(10)

    # ── 4. Freight Railways ──
    print("[4/4] Freight railways...")
    try:
        query = f"""
        [out:json][timeout:120];
        (
          way["railway"="rail"]["usage"="main"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["railway"="rail"]["usage"="branch"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["railway"="rail"]["usage"="industrial"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["railway"="rail"]["service"="yard"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
          way["railway"="rail"]["service"="spur"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
        );
        out geom;
        """
        data = query_overpass(query)
        elements = data.get("elements", [])
        railways = []
        for el in elements:
            railways.append({
                "osm_id": el.get("id"),
                "name": el.get("tags", {}).get("name", "Unnamed"),
                "railway_type": el.get("tags", {}).get("railway"),
                "usage": el.get("tags", {}).get("usage"),
                "service": el.get("tags", {}).get("service"),
                "operator": el.get("tags", {}).get("operator"),
                "coordinates": [
                    {"lat": p["lat"], "lon": p["lon"]}
                    for p in el.get("geometry", [])
                ],
            })
        save_json("arlington_railways.json", {
            "total_railways": len(railways),
            "railways": railways,
        })
        print(f"    ✅ Freight railways: {len(railways)} lines\n")
    except Exception as e:
        print(f"    ❌ Freight railways failed: {e}\n")

    # ── Summary ──
    print("=" * 50)
    print("📁 Files in data/static/:")
    if STATIC_DIR.exists():
        for f in sorted(STATIC_DIR.iterdir()):
            if f.suffix == ".json":
                size_kb = f.stat().st_size / 1024
                print(f"    ✅ {f.name} ({size_kb:.1f} KB)")
    print("=" * 50)
    print("\n🎉 Done! Now start the server: python app/api/main.py\n")


if __name__ == "__main__":
    main()