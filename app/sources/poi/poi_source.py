"""
fetch_poi_data.py — Fetches POI data for Arlington, VA and saves as static JSON.

Sources:
  - Gas stations: OpenStreetMap (Overpass API)
  - Grocery stores: OpenStreetMap (Overpass API)

Location: app/sources/poi/fetch_poi_data.py
Saves to: app/data/static/

Usage (from project root):
    python app/sources/poi/fetch_poi_data.py
"""

import httpx
import json
import time
import os
from pathlib import Path

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "static"

ARLINGTON_BBOX = {
    "south": 38.827,
    "west": -77.172,
    "north": 38.934,
    "east": -77.032,
}


# ──────────────────────────────────────────────
# Overpass helper
# ──────────────────────────────────────────────
def query_overpass(query: str, timeout: int = 180, retries: int = 3) -> dict:
    with httpx.Client(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                print(f"    📡 Sending Overpass query (attempt {attempt + 1}/{retries})...")
                resp = client.post(OVERPASS_URL, data={"data": query})

                if resp.status_code == 429:
                    wait = 20 * (attempt + 1)
                    print(f"    ⏳ Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                if resp.status_code == 504:
                    wait = 15 * (attempt + 1)
                    print(f"    ⏳ Timeout. Waiting {wait}s...")
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


def save_json(filename: str, data: dict):
    filepath = STATIC_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)
    size_kb = os.path.getsize(filepath) / 1024
    print(f"    💾 Saved {filename} ({size_kb:.1f} KB)")


# ──────────────────────────────────────────────
# 1. Gas Stations
# ──────────────────────────────────────────────
def fetch_gas_stations():
    print("\n[1/2] Gas stations (OpenStreetMap)...")
    bb = ARLINGTON_BBOX

    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="fuel"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
      way["amenity"="fuel"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
    );
    out center;
    """
    data = query_overpass(query)
    elements = data.get("elements", [])

    stations = []
    for el in elements:
        tags = el.get("tags", {})

        if el.get("type") == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        else:
            lat = el.get("center", {}).get("lat")
            lon = el.get("center", {}).get("lon")

        if not lat or not lon:
            continue

        station = {
            "osm_id": el.get("id"),
            "name": tags.get("name", "Unnamed Gas Station"),
            "brand": tags.get("brand"),
            "operator": tags.get("operator"),
            "address": ", ".join(filter(None, [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:city"),
                tags.get("addr:state"),
            ])),
            "fuel_types": {
                "diesel": tags.get("fuel:diesel") == "yes",
                "gasoline": tags.get("fuel:octane_87") == "yes" or tags.get("fuel:gasoline") == "yes",
            },
            "lat": lat,
            "lon": lon,
        }
        stations.append(station)

    save_json("arlington_gas_stations.json", {
        "poi_type": "gas_station",
        "total": len(stations),
        "stations": stations,
    })
    print(f"    ✅ Found {len(stations)} gas stations")
    return stations


# ──────────────────────────────────────────────
# 2. Grocery Stores
# ──────────────────────────────────────────────
def fetch_grocery_stores():
    print("\n[2/2] Grocery stores (OpenStreetMap)...")
    bb = ARLINGTON_BBOX

    query = f"""
    [out:json][timeout:60];
    (
      node["shop"="supermarket"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
      way["shop"="supermarket"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
      node["shop"="convenience"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
      way["shop"="convenience"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
      node["shop"="greengrocer"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
      way["shop"="greengrocer"]({bb['south']},{bb['west']},{bb['north']},{bb['east']});
    );
    out center;
    """
    data = query_overpass(query)
    elements = data.get("elements", [])

    stores = []
    for el in elements:
        tags = el.get("tags", {})

        if el.get("type") == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        else:
            lat = el.get("center", {}).get("lat")
            lon = el.get("center", {}).get("lon")

        if not lat or not lon:
            continue

        store = {
            "osm_id": el.get("id"),
            "name": tags.get("name", "Unnamed Store"),
            "shop_type": tags.get("shop"),
            "brand": tags.get("brand"),
            "operator": tags.get("operator"),
            "address": ", ".join(filter(None, [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:city"),
                tags.get("addr:state"),
            ])),
            "opening_hours": tags.get("opening_hours"),
            "lat": lat,
            "lon": lon,
        }
        stores.append(store)

    type_counts = {}
    for s in stores:
        t = s["shop_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    save_json("arlington_grocery_stores.json", {
        "poi_type": "grocery_store",
        "total": len(stores),
        "by_type": type_counts,
        "stores": stores,
    })
    print(f"    ✅ Found {len(stores)} grocery stores")
    for t, c in type_counts.items():
        print(f"       {t}: {c}")
    return stores


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    os.makedirs(STATIC_DIR, exist_ok=True)

    print(f"\n📍 Fetching POI data for Arlington, VA...")
    print(f"📁 Saving to: {STATIC_DIR}\n")

    fetch_gas_stations()
    print("\n    ⏳ Waiting 10s before next query...")
    time.sleep(10)
    fetch_grocery_stores()

    print("\n" + "=" * 50)
    print("📁 POI files in data/static/:")
    for f in sorted(STATIC_DIR.iterdir()):
        if "gas_station" in f.name or "grocery" in f.name:
            size_kb = f.stat().st_size / 1024
            print(f"    ✅ {f.name} ({size_kb:.1f} KB)")
    print("=" * 50)
    print("\n🎉 Done! POI data saved.\n")


if __name__ == "__main__":
    main()