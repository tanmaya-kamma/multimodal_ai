"""
route_analysis.py — Analyzes supply delivery routes for disruptions.

Location: app/fusion/route_analysis.py

Given a source and destinations, finds the driving route using OSRM,
checks which H3 cells the route passes through, and flags any
segments that overlap with active disruption alerts.

Uses OSRM (Open Source Routing Machine) — free, no API key.
"""

import httpx
import sqlite3
import h3
import math
from pathlib import Path
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
H3_RESOLUTION = 8
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "supply_chain.db"

OSRM_BASE = "https://router.project-osrm.org"

# Keep roughly 1 point per this many meters
SIMPLIFY_DISTANCE_M = 100


def get_db():
    if not DB_PATH.exists():
        return None
    return sqlite3.connect(DB_PATH)


def haversine_m(lat1, lon1, lat2, lon2):
    """Distance in meters between two lat/lon points."""
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def simplify_coords(coordinates: list, min_distance_m: int = SIMPLIFY_DISTANCE_M) -> list:
    """
    Reduce coordinate density by keeping only points that are
    at least min_distance_m apart. Always keeps first and last point.
    """
    if len(coordinates) <= 2:
        return coordinates

    simplified = [coordinates[0]]

    for point in coordinates[1:-1]:
        last = simplified[-1]
        dist = haversine_m(last["lat"], last["lon"], point["lat"], point["lon"])
        if dist >= min_distance_m:
            simplified.append(point)

    simplified.append(coordinates[-1])
    return simplified


# ──────────────────────────────────────────────
# Step 1: Get driving route from OSRM
# ──────────────────────────────────────────────
def get_route(source: dict, destination: dict) -> dict | None:
    """
    Get driving route between two points using OSRM.
    Returns route geometry as list of coordinates + metadata.
    """
    # OSRM expects lon,lat (not lat,lon)
    coords = f"{source['lon']},{source['lat']};{destination['lon']},{destination['lat']}"
    url = f"{OSRM_BASE}/route/v1/driving/{coords}"

    params = {
        "overview": "full",          # full route geometry
        "geometries": "geojson",     # return as GeoJSON
        "steps": "true",             # include turn-by-turn steps
        "annotations": "true",       # include speed/distance per segment
    }

    with httpx.Client(timeout=30) as client:
        try:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != "Ok" or not data.get("routes"):
                return None

            route = data["routes"][0]
            geometry = route["geometry"]["coordinates"]  # [[lon, lat], ...]
            
            # Convert to our format
            coordinates = [{"lat": c[1], "lon": c[0]} for c in geometry]

            # Extract step-by-step directions
            steps = []
            for leg in route.get("legs", []):
                for step in leg.get("steps", []):
                    steps.append({
                        "instruction": step.get("maneuver", {}).get("type", ""),
                        "road_name": step.get("name", ""),
                        "distance_m": step.get("distance", 0),
                        "duration_s": step.get("duration", 0),
                    })

            return {
                "coordinates": simplify_coords(coordinates),
                "full_coordinates": coordinates,  # keep full for H3 indexing
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_min": round(route["duration"] / 60, 1),
                "steps": steps,
            }

        except Exception as e:
            print(f"  ❌ OSRM routing error: {e}")
            return None


# ──────────────────────────────────────────────
# Step 2: Assign H3 cells to route segments
# ──────────────────────────────────────────────
def h3_index_route(coordinates: list) -> list:
    """
    Walk along the route coordinates and assign H3 cells.
    Returns list of segments, each with start/end coords and H3 cell.
    """
    segments = []
    
    for i in range(len(coordinates) - 1):
        start = coordinates[i]
        end = coordinates[i + 1]
        
        # Use midpoint for H3 assignment
        mid_lat = (start["lat"] + end["lat"]) / 2
        mid_lon = (start["lon"] + end["lon"]) / 2
        cell = h3.latlng_to_cell(mid_lat, mid_lon, H3_RESOLUTION)

        segments.append({
            "start": start,
            "end": end,
            "h3_cell": cell,
        })

    return segments


# ──────────────────────────────────────────────
# Step 3: Check which cells have active alerts
# ──────────────────────────────────────────────
def get_disrupted_cells(conn) -> dict:
    """
    Get all H3 cells with active alerts above minimum severity.
    Only real disruptions mark routes as compromised.
    """
    rows = conn.execute("""
        SELECT h3_cell, alert_tier, MAX(combined_severity) as severity, description
        FROM alerts
        WHERE combined_severity >= 0.3
        GROUP BY h3_cell
    """).fetchall()

    return {
        row[0]: {
            "tier": row[1],
            "severity": row[2],
            "description": row[3],
        }
        for row in rows
    }


# ──────────────────────────────────────────────
# Step 4: Build route segments with status
# ──────────────────────────────────────────────
def analyze_single_route(source: dict, destination: dict, disrupted_cells: dict) -> dict | None:
    """Analyze one source→destination route."""
    
    # Get driving route
    route = get_route(source, destination)
    if not route:
        return {
            "source": source,
            "destination": destination,
            "status": "route_not_found",
            "error": "Could not find a driving route between these points",
        }

    # H3 index the route (use full detail for accuracy)
    segments = h3_index_route(route["full_coordinates"])

    # Check each segment against disrupted cells
    route_cells = []
    seen_cells = set()
    compromised_count = 0

    for seg in segments:
        cell = seg["h3_cell"]
        
        if cell in seen_cells:
            continue
        seen_cells.add(cell)

        disruption = disrupted_cells.get(cell)
        
        if disruption:
            compromised_count += 1
            route_cells.append({
                "h3_cell": cell,
                "status": "compromised",
                "alert_tier": disruption["tier"],
                "severity": disruption["severity"],
                "description": disruption["description"],
            })
        else:
            route_cells.append({
                "h3_cell": cell,
                "status": "clear",
            })

    # Build compromised segments (consecutive coordinates in bad cells)
    compromised_segments = []
    current_segment = []
    
    for seg in segments:
        disruption = disrupted_cells.get(seg["h3_cell"])
        if disruption:
            current_segment.append(seg["start"])
            current_segment.append(seg["end"])
        else:
            if current_segment:
                # Deduplicate consecutive points
                deduped = [current_segment[0]]
                for pt in current_segment[1:]:
                    if pt != deduped[-1]:
                        deduped.append(pt)
                compromised_segments.append({
                    "coordinates": simplify_coords(deduped),
                    "severity": max(
                        disrupted_cells.get(
                            h3.latlng_to_cell(pt["lat"], pt["lon"], H3_RESOLUTION), {}
                        ).get("severity", 0)
                        for pt in deduped
                    ),
                })
                current_segment = []

    # Don't forget the last segment
    if current_segment:
        deduped = [current_segment[0]]
        for pt in current_segment[1:]:
            if pt != deduped[-1]:
                deduped.append(pt)
        compromised_segments.append({
            "coordinates": simplify_coords(deduped),
            "severity": max(
                disrupted_cells.get(
                    h3.latlng_to_cell(pt["lat"], pt["lon"], H3_RESOLUTION), {}
                ).get("severity", 0)
                for pt in deduped
            ),
        })

    # Simplify compromised segment coordinates
    for seg in compromised_segments:
        seg["coordinates"] = simplify_coords(seg["coordinates"])

    total_cells = len(seen_cells)
    
    # Overall route status
    if compromised_count == 0:
        overall_status = "clear"
    elif compromised_count / total_cells > 0.5:
        overall_status = "severely_compromised"
    elif compromised_count > 0:
        overall_status = "partially_compromised"
    else:
        overall_status = "clear"

    # Clean up steps — remove empty road names
    clean_steps = [
        s for s in route["steps"]
        if s["road_name"] and s["instruction"] not in ("arrive",)
    ]

    return {
        "source": source,
        "destination": destination,
        "status": overall_status,
        "distance_km": route["distance_km"],
        "duration_min": route["duration_min"],
        "total_cells": total_cells,
        "compromised_cells": compromised_count,
        "route_coordinates": route["coordinates"],  # already simplified
        "compromised_segments": compromised_segments,
        "directions": clean_steps,
    }


# ──────────────────────────────────────────────
# Main: Analyze all routes from source to destinations
# ──────────────────────────────────────────────
def analyze_routes(source: dict, destinations: list) -> dict:
    """
    Analyze supply routes from one source to multiple destinations.
    
    Args:
        source: {"name": "...", "lat": ..., "lon": ...}
        destinations: [{"name": "...", "lat": ..., "lon": ...}, ...]
    
    Returns complete route analysis with compromised segments.
    """
    conn = get_db()
    if not conn:
        return {"error": "Database not found"}

    # Get all disrupted cells
    disrupted_cells = get_disrupted_cells(conn)
    conn.close()

    routes = []
    total_compromised = 0

    for dest in destinations:
        result = analyze_single_route(source, dest, disrupted_cells)
        if result:
            routes.append(result)
            if result.get("primary_route", {}).get("compromised_cells", 0) > 0:
                total_compromised += 1

    return {
        "source": source,
        "total_destinations": len(destinations),
        "total_routes": len(routes),
        "compromised_routes": total_compromised,
        "disrupted_cells_on_map": len(disrupted_cells),
        "routes": routes,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }