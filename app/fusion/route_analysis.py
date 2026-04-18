"""
route_analysis.py — Analyzes sequential supply delivery routes for disruptions.

Location: app/fusion/route_analysis.py

Route model: Source → Dest1 → Dest2 → ... → DestN (like a delivery truck)
For each compromised leg, suggests an alternate route that avoids disrupted zones.

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
SIMPLIFY_DISTANCE_M = 100


def get_db():
    if not DB_PATH.exists():
        return None
    return sqlite3.connect(DB_PATH)


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    a = min(1.0, max(0.0, a))  # Clamp to guard against float drift
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def simplify_coords(coordinates: list, min_distance_m: int = SIMPLIFY_DISTANCE_M) -> list:
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
# Step 1: Get ALL driving routes from OSRM
# Returns list of route options (primary + alternatives)
# ──────────────────────────────────────────────
def get_all_routes(source: dict, destination: dict, via: dict = None) -> list:
    """
    Get primary + alternative driving routes between two points.
    Returns list of routes sorted by duration (fastest first).
    """
    if via:
        coords = f"{source['lon']},{source['lat']};{via['lon']},{via['lat']};{destination['lon']},{destination['lat']}"
    else:
        coords = f"{source['lon']},{source['lat']};{destination['lon']},{destination['lat']}"
        
    url = f"{OSRM_BASE}/route/v1/driving/{coords}"

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "annotations": "true",
        "alternatives": "3",
    }

    with httpx.Client(timeout=30) as client:
        try:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != "Ok" or not data.get("routes"):
                return []

            routes = []
            for route in data["routes"]:
                geometry = route["geometry"]["coordinates"]
                coordinates = [{"lat": c[1], "lon": c[0]} for c in geometry]

                steps = []
                for leg in route.get("legs", []):
                    for step in leg.get("steps", []):
                        steps.append({
                            "instruction": step.get("maneuver", {}).get("type", ""),
                            "road_name": step.get("name", ""),
                            "distance_m": step.get("distance", 0),
                            "duration_s": step.get("duration", 0),
                        })

                routes.append({
                    "coordinates": simplify_coords(coordinates),
                    "full_coordinates": coordinates,
                    "distance_km": round(route["distance"] / 1000, 2),
                    "duration_min": round(route["duration"] / 60, 1),
                    "steps": steps,
                })

            return routes

        except Exception as e:
            print(f"  [ERROR] OSRM routing error: {e}")
            return []


# ──────────────────────────────────────────────
# Step 2: Assign H3 cells to route segments
# ──────────────────────────────────────────────
def h3_index_route(coordinates: list) -> list:
    segments = []
    for i in range(len(coordinates) - 1):
        start = coordinates[i]
        end = coordinates[i + 1]
        mid_lat = (start["lat"] + end["lat"]) / 2
        mid_lon = (start["lon"] + end["lon"]) / 2
        cell = h3.latlng_to_cell(mid_lat, mid_lon, H3_RESOLUTION)
        segments.append({"start": start, "end": end, "h3_cell": cell})
    return segments


# ──────────────────────────────────────────────
# Step 3: Check which cells have active alerts
# ──────────────────────────────────────────────
def get_disrupted_cells(conn) -> dict:
    rows = conn.execute("""
        SELECT h3_cell, alert_tier, MAX(combined_severity) as severity, description
        FROM alerts
        WHERE combined_severity >= 0.3
        GROUP BY h3_cell
    """).fetchall()

    return {
        row[0]: {"tier": row[1], "severity": row[2], "description": row[3]}
        for row in rows
    }


# ──────────────────────────────────────────────
# Step 4: Score a single route against disruptions
# ──────────────────────────────────────────────
def score_route(route: dict, disrupted_cells: dict) -> dict:
    """
    Analyze one route for disruption.
    Returns route data with compromised segments and stats.
    """
    segments = h3_index_route(route["full_coordinates"])
    
    seen_cells = set()
    compromised_count = 0
    total_severity = 0.0
    
    # Build compromised segments for visualization
    compromised_segments = []
    current_comp = []

    for seg in segments:
        cell = seg["h3_cell"]
        disruption = disrupted_cells.get(cell)

        if cell not in seen_cells:
            seen_cells.add(cell)
            if disruption:
                compromised_count += 1
                total_severity += disruption["severity"]

        if disruption:
            current_comp.append(seg["start"])
            current_comp.append(seg["end"])
        else:
            if current_comp:
                deduped = [current_comp[0]]
                for pt in current_comp[1:]:
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
                current_comp = []

    # Last segment
    if current_comp:
        deduped = [current_comp[0]]
        for pt in current_comp[1:]:
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

    total_cells = len(seen_cells)
    ratio = compromised_count / max(1, total_cells)

    if compromised_count == 0:
        status = "clear"
    elif ratio > 0.4:
        status = "severely_compromised"
    else:
        status = "partially_compromised"

    return {
        "status": status,
        "distance_km": route["distance_km"],
        "duration_min": route["duration_min"],
        "total_cells": total_cells,
        "compromised_cells": compromised_count,
        "total_severity": round(total_severity, 4),
        "route_coordinates": route["coordinates"],
        "compromised_segments": compromised_segments,
        "directions": [
            s for s in route["steps"]
            if s["road_name"] and s["instruction"] not in ("arrive",)
        ],
    }


# ──────────────────────────────────────────────
# Step 5: Find best alternate for a compromised leg
# ──────────────────────────────────────────────
def find_alternate(source: dict, destination: dict, disrupted_cells: dict) -> dict | None:
    """
    Get all OSRM route alternatives for a leg,
    score each one, and return the safest option
    that is better than the primary route.
    """
    all_routes = get_all_routes(source, destination)

    if len(all_routes) < 2:
        return None  # OSRM only found one route, no alternatives

    # Score each route
    scored = []
    for route in all_routes:
        result = score_route(route, disrupted_cells)
        scored.append(result)

    # Primary is the first one (fastest)
    primary = scored[0]

    # Find the safest among alternatives (index 1+)
    alternatives = scored[1:]
    if not alternatives:
        return None

    print(f"    [WARN] Primary compromised. Finding alternate...")
    safest = min(alternatives, key=lambda r: (r["compromised_cells"], r["total_severity"]))

    # Only recommend if it's actually better
    if safest["compromised_cells"] >= primary["compromised_cells"]:
        return None  # no improvement

    # Build reason text
    avoided = primary["compromised_cells"] - safest["compromised_cells"]
    extra_dist = safest["distance_km"] - primary["distance_km"]
    extra_time = safest["duration_min"] - primary["duration_min"]

    if safest["compromised_cells"] == 0:
        route_note = "Fully avoids all compromised zones."
    else:
        route_note = f"Reduces exposure from {primary['compromised_cells']} to {safest['compromised_cells']} compromised zone(s)."

    return {
        "status": safest["status"],
        "distance_km": safest["distance_km"],
        "duration_min": safest["duration_min"],
        "total_cells": safest["total_cells"],
        "compromised_cells": safest["compromised_cells"],
        "route_coordinates": safest["route_coordinates"],
        "compromised_segments": safest["compromised_segments"],
        "directions": safest["directions"],
        "reason": f"{route_note} Additional distance: {extra_dist:+.1f} km, additional time: {extra_time:+.1f} min.",
    }


# ──────────────────────────────────────────────
# Step 6: Main — Sequential route analysis
# Source → Dest1 → Dest2 → ... → DestN
# ──────────────────────────────────────────────
def analyze_routes(source: dict, destinations: list) -> dict:
    """
    Analyze sequential supply route with alternate recommendations
    for compromised legs.
    """
    conn = get_db()
    if not conn:
        return {"error": "Database not found"}

    disrupted_cells = get_disrupted_cells(conn)
    conn.close()

    total_distance_km = 0
    total_duration_min = 0
    analyzed_legs = []
    current_point = source
    total_compromised_legs = 0
    all_disrupted_on_route = set()

    for i, dest in enumerate(destinations):
        # Get all routes for this leg
        print(f"  [DEBUG] Analyzing leg {i+1}: {current_point.get('name', 'Start')} -> {dest.get('name', 'Dest')}")
        all_routes = get_all_routes(current_point, dest)

        if not all_routes:
            analyzed_legs.append({
                "source": current_point,
                "destination": dest,
                "primary_route": {
                    "status": "unreachable",
                    "error": "No driving route found",
                    "distance_km": 0,
                    "duration_min": 0,
                    "total_cells": 0,
                    "compromised_cells": 0,
                    "total_severity": 0,
                    "route_coordinates": [],
                    "compromised_segments": [],
                    "directions": [],
                },
                "alternate_route": None,
            })
            current_point = dest
            continue

        # Score the primary (fastest) route
        primary = score_route(all_routes[0], disrupted_cells)

        leg_result = {
            "source": current_point,
            "destination": dest,
            "primary_route": primary,
            "alternate_route": None,
        }

        # If primary is compromised, find a better alternative
        if primary["compromised_cells"] > 0:
            total_compromised_legs += 1

            # Track disrupted cells
            for seg in h3_index_route(all_routes[0]["full_coordinates"]):
                if seg["h3_cell"] in disrupted_cells:
                    all_disrupted_on_route.add(seg["h3_cell"])

            # Score all alternatives and find the safest
            if len(all_routes) > 1:
                alternatives = [score_route(r, disrupted_cells) for r in all_routes[1:]]
                safest = min(alternatives, key=lambda r: (r["compromised_cells"], r["total_severity"]))

                extra_dist = safest["distance_km"] - primary["distance_km"]
                extra_time = safest["duration_min"] - primary["duration_min"]

                if safest["compromised_cells"] < primary["compromised_cells"] or safest["total_severity"] < primary["total_severity"]:
                    print(f"    [FIX] Safest alternate found with severity {safest['total_severity']}")
                    
                    if safest["compromised_cells"] == 0:
                        route_note = "Fully avoids all compromised zones."
                    elif safest["compromised_cells"] < primary["compromised_cells"]:
                        route_note = (
                            f"Reduces exposure from {primary['compromised_cells']} "
                            f"to {safest['compromised_cells']} compromised zone(s)."
                        )
                    else:
                        route_note = (
                            f"Reduces total threat severity from {primary['total_severity']:.1f} "
                            f"to {safest['total_severity']:.1f}."
                        )
                else:
                    route_note = "Alternate route available, but has similar or higher threat exposure."

                leg_result["alternate_route"] = {
                    **safest,
                    "reason": (
                        f"{route_note} "
                        f"Additional distance: {extra_dist:+.1f} km, "
                        f"additional time: {extra_time:+.1f} min."
                    ),
                }
            else:
                print("    [DEMO] Simulating alternate route via intermediate geometric offset...")
                # OSRM didn't return alternatives natively. Force a detour that follows real roads.
                mid_idx = len(all_routes[0]["full_coordinates"]) // 2
                midway = all_routes[0]["full_coordinates"][mid_idx]
                
                # Shift ~1.5km East
                forced_via = {"lat": midway["lat"], "lon": midway["lon"] + 0.015}
                forced_routes = get_all_routes(current_point, dest, via=forced_via)
                
                # If shifting East fails (e.g. goes into the river without local roads), try West
                if not forced_routes:
                    forced_via = {"lat": midway["lat"], "lon": midway["lon"] - 0.015}
                    forced_routes = get_all_routes(current_point, dest, via=forced_via)
                
                if forced_routes:
                    forced_scored = score_route(forced_routes[0], disrupted_cells)
                    extra_dist = forced_scored["distance_km"] - primary["distance_km"]
                    extra_time = forced_scored["duration_min"] - primary["duration_min"]
                    
                    leg_result["alternate_route"] = {
                        **forced_scored,
                        "reason": (
                            f"Forced via-point alternative to avoid primary corridor. "
                            f"Additional distance: {extra_dist:+.1f} km, "
                            f"additional time: {extra_time:+.1f} min."
                        )
                    }
                else:
                    leg_result["alternate_note"] = "No alternative routes available (even via offset geometries)."
        total_distance_km += primary["distance_km"]
        total_duration_min += primary["duration_min"]
        analyzed_legs.append(leg_result)

        # Next leg starts from this destination
        current_point = dest

    # Overall status
    statuses = [leg["primary_route"]["status"] for leg in analyzed_legs]
    if "unreachable" in statuses:
        overall_status = "unreachable"
    elif "severely_compromised" in statuses:
        overall_status = "severely_compromised"
    elif "partially_compromised" in statuses:
        overall_status = "partially_compromised"
    else:
        overall_status = "clear"

    return {
        "source": source,
        "total_destinations": len(destinations),
        "total_legs": len(analyzed_legs),
        "compromised_legs": total_compromised_legs,
        "disrupted_cells_on_route": len(all_disrupted_on_route),
        "status": overall_status,
        "legs": analyzed_legs,
        "metrics": {
            "total_distance_km": round(total_distance_km, 2),
            "total_duration_min": round(total_duration_min, 1),
        },
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }