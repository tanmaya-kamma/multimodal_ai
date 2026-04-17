"""
route_analysis.py - Analyzes supply delivery routes for disruptions.

Location: app/fusion/route_analysis.py

Given a source and destinations, finds the driving route using OSRM,
checks which H3 cells the route passes through, and flags any
segments that overlap with active disruption alerts.

Uses OSRM (Open Source Routing Machine) - free, no API key.
"""

import httpx
import sqlite3
import h3
import math
from pathlib import Path
from datetime import datetime, timezone

# ----------------------------------------------
# Constants
# ----------------------------------------------
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


# ----------------------------------------------
# Step 1: Get driving route from OSRM
# ----------------------------------------------
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
        "alternatives": "true"       # allow OSRM to find alternates if requested
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
            print(f"  - OSRM routing error: {e}")
            return None


# ----------------------------------------------
# Step 2: Assign H3 cells to route segments
# ----------------------------------------------
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


# ----------------------------------------------
# Step 3: Check which cells have active alerts
# ----------------------------------------------
def get_disrupted_cells(conn) -> dict:
    """
    Get all H3 cells with active alerts above minimum severity.
    Only real disruptions mark routes as compromised.
    """
    rows = conn.execute(\"\"\"
        SELECT h3_cell, alert_tier, MAX(combined_severity) as severity, description
        FROM alerts
        WHERE combined_severity >= 0.3
        GROUP BY h3_cell
    \"\"\").fetchall()

    return {
        row[0]: {
            "tier": row[1],
            "severity": row[2],
            "description": row[3],
        }
        for row in rows
    }


# ----------------------------------------------
# Step 4: Build Sequential Route Analysis
# ----------------------------------------------
def analyze_routes(source: dict, destinations: list) -> dict:
    """
    Analyze sequential supply route: Source -> Dest1 -> Dest2 -> ... -> DestN.
    Returns per-destination status flags (e.g., Clear, Compromised).
    """
    conn = get_db()
    if not conn:
        return {"error": "Database not found"}

    disrupted_cells = get_disrupted_cells(conn)
    conn.close()

    total_distance_km = 0
    total_duration_min = 0
    all_full_coords = []
    all_simplified_coords = []
    all_directions = []
    all_compromised_segments = []
    
    destination_results = []
    current_point = source
    
    for i, dest in enumerate(destinations):
        # Get segment route
        route = get_route(current_point, dest)
        
        if not route:
            destination_results.append({
                "destination": dest["name"],
                "status": "unreachable",
                "error": "Unreachable via road network"
            })
            # If a leg is unreachable, the chain breaks
            break
        
        # Analyze this segment's H3 footprint
        seg_all_segments = h3_index_route(route["full_coordinates"])
        seg_total_cells = len(set(s["h3_cell"] for s in seg_all_segments))
        seg_compromised_cells = 0
        seg_seen_cells = set()
        
        # Per-segment compromised segments for visual feedback
        seg_compromised_gl = []
        curr_comp = []
        
        for seg in seg_all_segments:
            cell = seg["h3_cell"]
            disruption = disrupted_cells.get(cell)
            
            if disruption:
                if cell not in seg_seen_cells:
                    seg_compromised_cells += 1
                    seg_seen_cells.add(cell)
                
                curr_comp.append(seg["start"])
                curr_comp.append(seg["end"])
            else:
                if curr_comp:
                    deduped = [curr_comp[0]]
                    for pt in curr_comp[1:]:
                        if pt != deduped[-1]: deduped.append(pt)
                    seg_compromised_gl.append({
                        "coordinates": simplify_coords(deduped),
                        "severity": 0.8
                    })
                    curr_comp = []
        
        if curr_comp:
            deduped = [curr_comp[0]]
            for pt in curr_comp[1:]:
                if pt != deduped[-1]: deduped.append(pt)
            seg_compromised_gl.append({"coordinates": simplify_coords(deduped), "severity": 0.8})

        # Calculate leg status
        leg_ratio = seg_compromised_cells / max(1, seg_total_cells)
        if seg_compromised_cells == 0:
            leg_status = "Clear"
        elif leg_ratio > 0.4:
            leg_status = "Severely Compromised"
        else:
            leg_status = "Partially Compromised"

        # Accumulate metrics
        total_distance_km += route["distance_km"]
        total_duration_min += route["duration_min"]
        
        # Store destination result
        destination_results.append({
            "destination": dest["name"],
            "status": leg_status,
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "compromised_cells": seg_compromised_cells,
            "total_cells": seg_total_cells,
            "risk_score": round(leg_ratio, 2)
        })

        # Extend global lists
        all_directions.extend([
            s for s in route["steps"]
            if s["road_name"] and s["instruction"] not in ("arrive",)
        ])
        
        if all_full_coords:
            all_full_coords.extend(route["full_coordinates"][1:])
            all_simplified_coords.extend(route["coordinates"][1:])
        else:
            all_full_coords.extend(route["full_coordinates"])
            all_simplified_coords.extend(route["coordinates"])
        
        all_compromised_segments.extend(seg_compromised_gl)
        
        # Prepare next leg
        current_point = dest

    # Determine overall status
    statuses = [r["status"] for r in destination_results]
    if "unreachable" in statuses:
        overall_status = "unreachable"
    elif "Severely Compromised" in statuses:
        overall_status = "severely_compromised"
    elif "Partially Compromised" in statuses:
        overall_status = "partially_compromised"
    else:
        overall_status = "clear"

    return {
        "source": source,
        "total_destinations": len(destinations),
        "status": overall_status,
        "destination_results": destination_results, # Per-destination status flags
        "metrics": {
            "total_distance_km": round(total_distance_km, 2),
            "total_duration_min": round(total_duration_min, 1),
        },
        "route_coordinates": all_simplified_coords,
        "compromised_segments": all_compromised_segments,
        "directions": all_directions,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
