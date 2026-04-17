"""
Supply Chain Disruption Management — Base Layer API
Serves Arlington, VA OSM data from local JSON files.
Location: app/api/main.py

Usage (from project root):
    python app/api/main.py
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import json
import h3
from pathlib import Path
import sys

# Add project root to path so we can import fusion
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "fusion"))

# ──────────────────────────────────────────────
# App Setup
# ──────────────────────────────────────────────
app = FastAPI(
    title="Supply Chain Disruption API",
    description="Base layer API for Arlington, VA supply chain situational awareness",
    version="0.1.0",
)
# Define absolute static file directory
API_DIR = Path(__file__).resolve().parent
STATIC_PATH = API_DIR / "static"
STATIC_PATH.mkdir(parents=True, exist_ok=True)

# Ensure the simulation subfolder exists
SIMULATION_DIR = STATIC_PATH / "simulation"
SIMULATION_DIR.mkdir(parents=True, exist_ok=True)

print(f"VLM Image Vault active at: {SIMULATION_DIR}")

# Mount the static folder using the absolute path
app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.map_viewer import viewer_router
app.include_router(viewer_router)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
DATA_STATIC_DIR = Path(__file__).resolve().parent.parent / "data" / "static"

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
    filepath = DATA_STATIC_DIR / filename
    if not filepath.exists():
        print(f"    {filepath} not found — run fetch_osm_data.py first")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    size_kb = filepath.stat().st_size / 1024
    print(f"   Loaded {filename} ({size_kb:.1f} KB)")
    return data


@app.on_event("startup")
async def load_cached_data():
    print("\n   Loading Arlington, VA OSM data from local files...\n")

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

    print(f"\n   Loaded {len(_cache)}/{TOTAL_LAYERS} layers: {list(_cache.keys())}")

    if len(_cache) < TOTAL_LAYERS:
        print("   Some layers missing. Run: python app/sources/osm/fetch_osm_data.py")

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


# ──────────────────────────────────────────────
# Fusion & Alert Endpoints
# ──────────────────────────────────────────────

@app.post("/arlington/fusion/run")
async def run_fusion_endpoint():
    """
    Trigger the fusion engine. Clears old alerts,
    analyzes all current data, generates fresh alerts.
    Call this before reading /alerts/active.
    """
    from fusion_engine import run_fusion
    alerts = run_fusion()
    return {
        "status": "success",
        "alerts_generated": len(alerts),
    }


@app.get("/arlington/alerts/active")
async def get_active_alerts():
    """
    Returns all active alerts. Each alert has:
      1. location — where the issue is
      2. explanation — what's happening and why
      3. source_links — clickable links to each data source
      4. severity — 0.0 to 1.0
      5. confidence — 0.0 to 1.0
      6. recommended_actions — steps to take
    """
    from fusion_engine import run_fusion
    raw_alerts = run_fusion()

    alerts = []
    for a in raw_alerts:
        alerts.append({
            "h3_cell": a["h3_cell"],
            "location": a["location"],
            "explanation": a["explanation"],
            "source_links": a["source_links"],
            "severity": a["severity"],
            "confidence": a["confidence"],
            "recommended_actions": a["recommended_actions"],
            "alert_tier": a["alert_tier"],
            "affected_pois": a["affected_pois"],
            "affected_roads": a["affected_roads"],
            "timestamp": a["timestamp"],
            "corroboration_factor": a.get("corroboration_factor", 1.0),
            "source_count": a.get("source_count", 0),
            "signal_count": a.get("signal_count", 0),
            "primary_event": a.get("primary_event", ""),
            "all_events": a.get("all_events", []),
        })

    return {"total_alerts": len(alerts), "alerts": alerts}


@app.get("/arlington/heatmap")
async def get_heatmap():
    """
    Returns deduplicated H3 cells with severity scores
    and hexagon boundary coordinates for map overlay.
    """
    import sqlite3
    db_path = DATA_STATIC_DIR.parent / "supply_chain.db"
    conn = sqlite3.connect(db_path)

    # Get highest severity per cell (deduplicated)
    rows = conn.execute("""
        SELECT h3_cell, alert_tier, MAX(combined_severity) as severity, MAX(source_count) as sources
        FROM alerts
        GROUP BY h3_cell
        ORDER BY severity DESC
    """).fetchall()
    conn.close()

    cells = []
    for h3_cell, tier, severity, sources in rows:
        boundary = h3.cell_to_boundary(h3_cell)
        cells.append({
            "h3_cell": h3_cell,
            "tier": tier,
            "severity": severity,
            "combined_severity": severity,
            "boundary": [{"lat": lat, "lon": lon} for lat, lon in boundary],
        })

    return {"total_cells": len(cells), "cells": cells}


# ──────────────────────────────────────────────
# Route Analysis Endpoint
# ──────────────────────────────────────────────

class Location(BaseModel):
    name: str  # address, place name, or POI name like "Pentagon City" or "1234 Columbia Pike"

class RouteAnalysisRequest(BaseModel):
    source: Location
    destinations: list[Location]


async def geocode_location(name: str) -> dict | None:
    """
    Convert a place name or address to lat/lon using Nominatim.
    Biased toward Arlington, VA for better local results.
    """
    import httpx

    # Append Arlington VA if not already specific
    query = name.strip()
    if "arlington" not in query.lower() and "virginia" not in query.lower() and "va" not in query.lower():
        query = f"{query}, Arlington, VA"

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "viewbox": "-77.172,38.934,-77.032,38.827",  # Arlington bbox
        "bounded": 1,
    }
    headers = {"User-Agent": "SupplyChainDisruptionApp/1.0"}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            results = resp.json()

            if results:
                return {
                    "name": name,
                    "lat": float(results[0]["lat"]),
                    "lon": float(results[0]["lon"]),
                    "resolved_address": results[0].get("display_name", ""),
                }

            # Retry without Arlington bbox restriction
            params.pop("bounded")
            params.pop("viewbox")
            resp = await client.get(url, params=params, headers=headers)
            results = resp.json()
            if results:
                return {
                    "name": name,
                    "lat": float(results[0]["lat"]),
                    "lon": float(results[0]["lon"]),
                    "resolved_address": results[0].get("display_name", ""),
                }

        except Exception as e:
            print(f"   Geocoding failed for '{name}': {e}")

    return None


@app.post("/arlington/routes/analyze")
async def analyze_supply_routes(request: RouteAnalysisRequest):
    """
    Analyze supply delivery routes for disruptions.

    User provides place names or addresses — no lat/lon needed.

    Request body:
    {
        "source": { "name": "Ballston" },
        "destinations": [
            { "name": "Shell on Columbia Pike" },
            { "name": "Harris Teeter Pentagon City" },
            { "name": "1550 Crystal Drive" }
        ]
    }
    """
    from route_analysis import analyze_routes

    # Geocode source
    source_geo = await geocode_location(request.source.name)
    if not source_geo:
        raise HTTPException(
            status_code=400,
            detail=f"Could not find location: '{request.source.name}'. Try a more specific address."
        )

    # Geocode each destination
    destinations_geo = []
    failed = []
    for dest in request.destinations:
        geo = await geocode_location(dest.name)
        if geo:
            destinations_geo.append(geo)
        else:
            failed.append(dest.name)

    if not destinations_geo:
        raise HTTPException(
            status_code=400,
            detail=f"Could not find any destinations. Failed: {', '.join(failed)}"
        )

    # Run route analysis
    result = analyze_routes(
        source=source_geo,
        destinations=destinations_geo,
    )

    # Add geocoding failures to response
    if failed:
        result["geocoding_failures"] = failed

    return result


@app.get("/arlington/alerts/cell/{h3_cell}")
async def get_cell_detail(h3_cell: str):
    """
    Drill-down: returns everything known about a specific H3 cell.
    All raw signals, POIs at risk, roads affected.
    """
    import sqlite3
    db_path = DATA_STATIC_DIR.parent / "supply_chain.db"
    conn = sqlite3.connect(db_path)

    weather = [
        {"alert_type": r[0], "severity": r[1], "confidence": r[2], "timestamp": r[3]}
        for r in conn.execute(
            "SELECT alert_type, severity, confidence, timestamp_utc FROM processed_weather WHERE h3_cell = ?",
            (h3_cell,)
        ).fetchall()
    ]

    traffic = []
    for r in conn.execute(
        "SELECT camera_id, congestion_level, anomaly_type, image_path, severity, timestamp_utc FROM processed_traffic WHERE h3_cell = ?",
        (h3_cell,)
    ).fetchall():
        # Check if physical asset exists in SIMULATION_DIR
        has_visual = False
        if r[3]:
             img_filename = Path(r[3]).name
             has_visual = (SIMULATION_DIR / img_filename).exists()
             
        traffic.append({
            "camera_id": r[0],
            "congestion": r[1],
            "anomaly": r[2],
            "image": r[3],
            "has_visual_evidence": has_visual,
            "severity": r[4],
            "timestamp": r[5]
        })

    news = [
        {"source": r[0], "title": r[1], "location": r[2], "event_type": r[3], "severity": r[4], "timestamp": r[5]}
        for r in conn.execute(
            "SELECT source_name, title, extracted_location, event_type, severity, timestamp_utc FROM processed_news WHERE h3_cell = ?",
            (h3_cell,)
        ).fetchall()
    ]

    pois = [
        {"type": r[0], "name": r[1], "address": r[2], "lat": r[3], "lon": r[4]}
        for r in conn.execute(
            "SELECT poi_type, name, address, lat, lon FROM processed_pois WHERE h3_cell = ?",
            (h3_cell,)
        ).fetchall()
    ]

    roads = [
        {"name": r[0], "type": r[1], "ref": r[2]}
        for r in conn.execute(
            "SELECT DISTINCT road_name, highway_type, ref FROM processed_roads WHERE h3_cell = ?",
            (h3_cell,)
        ).fetchall()
        if r[0] != "Unnamed"
    ]

    conn.close()

    return {
        "h3_cell": h3_cell,
        "signals": {
            "weather": weather,
            "traffic": traffic,
            "news": news,
        },
        "at_risk": {
            "pois": pois,
            "roads": roads,
        },
    }


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
# Simulation Trigger Endpoint
# ──────────────────────────────────────────────

class SimulationTriggerRequest(BaseModel):
    scenario: str = "flash_flood"
    epicenter: Optional[dict] = None
    intensity: Optional[float] = 0.85

@app.post("/arlington/simulation/trigger")
async def trigger_simulation(request: SimulationTriggerRequest):
    """
    Inject simulation data, then run fusion to generate alerts.
    Currently only supports the flash_flood scenario.
    """
    import sys
    from pathlib import Path
    app_dir = Path(__file__).resolve().parent.parent
    if str(app_dir / "simulation") not in sys.path:
        sys.path.insert(0, str(app_dir / "simulation"))
    
    try:
        from simulate_disaster import inject_weather, inject_traffic, inject_news, cleanup, get_db
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Simulation scripts missing: {e}")

    try:
        from fusion_engine import run_fusion
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Fusion engine missing: {e}")

    from datetime import datetime, timezone

    # 1. Clean previous simulation data
    cleanup()

    # 2. Inject fresh scenario
    if request.scenario == "flash_flood":
        conn = get_db()
        if not conn:
            raise HTTPException(status_code=500, detail="Database not available")

        inject_weather(conn)
        inject_traffic(conn)
        inject_news(conn)
        conn.commit()
        conn.close()
    else:
        raise HTTPException(status_code=400, detail=f"Scenario '{request.scenario}' not implemented yet.")

    # 3. Chain fusion
    alerts = run_fusion()
    affected_cells = list(set(a["h3_cell"] for a in alerts))

    return {
        "status": "success",
        "scenario": request.scenario,
        "records_injected": len(alerts) * 3,  # approximate
        "alerts_generated": len(alerts),
        "affected_cells": affected_cells,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)