"""
Supply Chain Disruption Management — Base Layer API
Serves Arlington, VA OSM data from local JSON files.
Location: app/api/main.py

Usage (from project root):
    python app/api/main.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path

# ──────────────────────────────────────────────
# App Setup
# ──────────────────────────────────────────────
app = FastAPI(
    title="Supply Chain Disruption API",
    description="Base layer API for Arlington, VA supply chain situational awareness",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from map_viewer import viewer_router
app.include_router(viewer_router)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
STATIC_DIR = Path(__file__).resolve().parent.parent / "data" / "static"

ARLINGTON_BBOX = {
    "south": 38.827,
    "west": -77.172,
    "north": 38.934,
    "east": -77.032,
}

ARLINGTON_CENTER = {"lat": 38.8816, "lon": -77.0910}

TOTAL_LAYERS = 6

# ──────────────────────────────────────────────
# Load data from local JSON files on startup
# ──────────────────────────────────────────────
_cache = {}


def load_json(filename: str) -> dict | None:
    filepath = STATIC_DIR / filename
    if not filepath.exists():
        print(f"  ⚠️  {filepath} not found — run fetch_osm_data.py first")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    size_kb = filepath.stat().st_size / 1024
    print(f"  ✅ Loaded {filename} ({size_kb:.1f} KB)")
    return data


@app.on_event("startup")
async def load_cached_data():
    print("\n🗺️  Loading Arlington, VA OSM data from local files...\n")

    files = {
        "boundary": "arlington_boundary.json",
        "major_roads": "arlington_major_roads.json",
        "secondary_roads": "arlington_secondary_roads.json",
        "railways": "arlington_railways.json",
        "gas_stations": "arlington_gas_stations.json",
        "grocery_stores": "arlington_grocery_stores.json",
    }

    for key, filename in files.items():
        data = load_json(filename)
        if data:
            _cache[key] = data

    print(f"\n🗺️  Loaded {len(_cache)}/{TOTAL_LAYERS} layers: {list(_cache.keys())}")

    if len(_cache) < TOTAL_LAYERS:
        print("⚠️  Some layers missing. Run: python app/sources/osm/fetch_osm_data.py")

    print()


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "Supply Chain Disruption API",
        "version": "0.1.0",
        "status": "running",
        "area": "Arlington, VA",
        "cached_layers": list(_cache.keys()),
        "total_expected": TOTAL_LAYERS,
    }


@app.get("/arlington/bbox")
async def get_bbox():
    return {"bbox": ARLINGTON_BBOX, "center": ARLINGTON_CENTER}


@app.get("/arlington/boundary")
async def get_boundary():
    if "boundary" not in _cache:
        raise HTTPException(status_code=503, detail="Boundary not loaded. Run fetch_osm_data.py first.")
    return _cache["boundary"]


@app.get("/arlington/roads/major")
async def get_major_roads():
    if "major_roads" not in _cache:
        raise HTTPException(status_code=503, detail="Major roads not loaded. Run fetch_osm_data.py first.")
    return _cache["major_roads"]


@app.get("/arlington/roads/secondary")
async def get_secondary_roads():
    if "secondary_roads" not in _cache:
        raise HTTPException(status_code=503, detail="Secondary roads not loaded. Run fetch_osm_data.py first.")
    return _cache["secondary_roads"]


@app.get("/arlington/railways")
async def get_railways():
    if "railways" not in _cache:
        raise HTTPException(status_code=503, detail="Railways not loaded. Run fetch_osm_data.py first.")
    return _cache["railways"]


@app.get("/arlington/pois/gas-stations")
async def get_gas_stations():
    if "gas_stations" not in _cache:
        raise HTTPException(status_code=503, detail="Gas stations not loaded. Run fetch_poi_data.py first.")
    return _cache["gas_stations"]


@app.get("/arlington/pois/grocery-stores")
async def get_grocery_stores():
    if "grocery_stores" not in _cache:
        raise HTTPException(status_code=503, detail="Grocery stores not loaded. Run fetch_poi_data.py first.")
    return _cache["grocery_stores"]


@app.get("/arlington/base-layer")
async def get_base_layer():
    return {
        "area": "Arlington, VA",
        "center": ARLINGTON_CENTER,
        "bbox": ARLINGTON_BBOX,
        "cached_layers": list(_cache.keys()),
        "layers": {
            "boundary": "/arlington/boundary",
            "major_roads": "/arlington/roads/major",
            "secondary_roads": "/arlington/roads/secondary",
            "railways": "/arlington/railways",
            "gas_stations": "/arlington/pois/gas-stations",
            "grocery_stores": "/arlington/pois/grocery-stores",
        },
    }


# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)