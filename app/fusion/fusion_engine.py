"""
fusion_engine.py — Attention-weighted multi-source signal fusion.

Location: app/fusion/fusion_engine.py

Architecture:
  1. Collect all recent signals grouped by H3 cell
  2. For each cell with 2+ sources, run attention-weighted fusion:
     - Source reliability weights (static)
     - Temporal decay (recent signals weighted higher)
     - Cross-source corroboration bonus (multiple sources → higher confidence)
     - Event-type attention (flood signal from weather + flood from camera → amplified)
  3. Cross-reference fused cells with POIs and roads
  4. Generate structured alerts with traceable source links

Usage (from project root):
    python app/fusion/fusion_engine.py
"""

import sqlite3
import json
import math
import h3
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "supply_chain.db"
H3_RESOLUTION = 8

# How far back to look for signals
TIME_WINDOW_HOURS = 3

# ──────────────────────────────────────────────
# Source Reliability Weights (static attention)
# These reflect how trustworthy each source is
# for supply chain disruption detection.
# ──────────────────────────────────────────────
SOURCE_WEIGHTS = {
    "weather":  0.90,  # NWS is authoritative
    "traffic":  0.85,  # Camera images are direct evidence
    "news":     0.70,  # News can be delayed or sensationalized
}

# ──────────────────────────────────────────────
# Event-type semantic similarity matrix
# Measures how much two event types from different
# sources corroborate each other.
# High value = strong corroboration signal.
# ──────────────────────────────────────────────
CORROBORATION_MATRIX = {
    # (weather_event, traffic_event) → corroboration score
    ("Flash Flood Warning", "flooding"):       0.95,
    ("Flash Flood Warning", "blocked"):        0.85,
    ("Flood Warning", "flooding"):             0.90,
    ("Flood Warning", "blocked"):              0.80,
    ("Severe Thunderstorm Warning", "debris"):  0.75,
    ("Severe Thunderstorm Warning", "accident"): 0.60,
    ("Winter Storm Warning", "blocked"):        0.85,
    ("Ice Storm Warning", "blocked"):           0.90,
    ("Tornado Warning", "blocked"):             0.95,
    ("Tornado Warning", "debris"):              0.90,
    # (weather_event, news_event) → corroboration score
    ("Flash Flood Warning", "flooding"):        0.95,
    ("Flash Flood Warning", "road_closure"):    0.85,
    ("Flood Warning", "flooding"):              0.90,
    ("Severe Thunderstorm Warning", "severe_storm"): 0.80,
    ("Severe Thunderstorm Warning", "road_closure"): 0.70,
    ("Winter Storm Warning", "winter_storm"):    0.85,
    # (traffic_event, news_event) → corroboration score
    ("flooding", "flooding"):                    0.90,
    ("flooding", "road_closure"):                0.80,
    ("blocked", "road_closure"):                 0.85,
    ("blocked", "emergency_alert"):              0.80,
    ("accident", "accident"):                    0.90,
    ("debris", "severe_storm"):                  0.70,
}

# ──────────────────────────────────────────────
# Alert tier thresholds
# ──────────────────────────────────────────────
TIER_THRESHOLDS = {
    "CRITICAL": {"min_severity": 0.70, "min_sources": 2},
    "WARNING":  {"min_severity": 0.45, "min_sources": 2},
    "WATCH":    {"min_severity": 0.25, "min_sources": 1},
}

# Event type → recommended actions mapping
ACTION_MAP = {
    "flooding": [
        "Reroute delivery trucks away from flooded road segments",
        "Alert gas stations and grocery stores in affected area of potential supply delays",
        "Coordinate with emergency services for road clearance timeline",
        "Identify alternate supply routes that bypass the flooded zone",
    ],
    "road_closure": [
        "Identify alternate routes for freight and delivery vehicles",
        "Notify affected POIs of expected delivery delays",
        "Monitor traffic cameras for reopening indicators",
        "Coordinate with VDOT for estimated road reopening time",
    ],
    "severe_storm": [
        "Pre-position emergency supplies at unaffected distribution points",
        "Alert all POIs in storm path to secure inventory and prepare for power outages",
        "Suspend non-essential deliveries until storm passes",
        "Monitor weather updates for storm trajectory changes",
    ],
    "winter_storm": [
        "Pre-treat priority supply routes with salt/brine if possible",
        "Switch to chains-equipped or all-weather delivery vehicles",
        "Stockpile essential supplies at POIs ahead of storm arrival",
        "Coordinate with VDOT for plowing priority on freight corridors",
    ],
    "accident": [
        "Reroute delivery vehicles around accident scene",
        "Monitor traffic cameras for scene clearance",
        "Assess if hazardous materials are involved (fuel tanker, etc.)",
        "Estimate clearance time and adjust delivery schedules",
    ],
    "power_outage": [
        "Alert gas stations — fuel pumps require electricity",
        "Alert grocery stores — refrigeration at risk",
        "Identify POIs with backup generators",
        "Coordinate with Dominion Energy for restoration timeline",
    ],
    "supply_disruption": [
        "Identify which specific supplies are affected (fuel, food, medicine)",
        "Activate alternate supplier or distribution center",
        "Prioritize resupply to critical POIs (hospitals, shelters)",
        "Communicate estimated restoration timeline to affected POIs",
    ],
    "emergency_alert": [
        "Follow all directives from Arlington County Emergency Management",
        "Suspend all non-essential supply chain operations in affected area",
        "Redirect resources to support emergency shelters",
        "Coordinate with first responders for supply needs",
    ],
    "general": [
        "Continue monitoring all data sources for escalation",
        "Verify the disruption through additional sources",
        "Prepare contingency routes in case of escalation",
    ],
}


def get_db():
    if not DB_PATH.exists():
        print(f"   [ERROR] Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


# ──────────────────────────────────────────────
# Step 1: Collect signals per H3 cell
# ──────────────────────────────────────────────
def collect_signals(conn, time_window_hours: int = TIME_WINDOW_HOURS) -> dict:
    """
    Query all processed tables for recent signals.
    Returns dict: { h3_cell: { "weather": [...], "traffic": [...], "news": [...] } }
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).isoformat()

    cells = defaultdict(lambda: {"weather": [], "traffic": [], "news": []})

    # Weather signals
    rows = conn.execute("""
        SELECT h3_cell, timestamp_utc, alert_type, temperature, wind_speed,
               precipitation_mm, severity, confidence
        FROM processed_weather
        WHERE timestamp_utc > ? OR created_at > ?
    """, (cutoff, cutoff)).fetchall()

    for h3_cell, ts, alert_type, temp, wind, precip, severity, confidence in rows:
        cells[h3_cell]["weather"].append({
            "source": "weather",
            "timestamp": ts,
            "event_type": alert_type or "forecast",
            "severity": severity,
            "confidence": confidence,
            "details": {
                "alert_type": alert_type,
                "temperature": temp,
                "wind_speed": wind,
                "precipitation": precip,
            },
        })

    # Traffic signals
    rows = conn.execute("""
        SELECT h3_cell, timestamp_utc, camera_id, congestion_level,
               anomaly_type, image_path, severity, confidence
        FROM processed_traffic
        WHERE timestamp_utc > ? OR created_at > ?
    """, (cutoff, cutoff)).fetchall()

    for h3_cell, ts, cam_id, congestion, anomaly, img, severity, confidence in rows:
        cells[h3_cell]["traffic"].append({
            "source": "traffic",
            "timestamp": ts,
            "event_type": anomaly or congestion or "unknown",
            "severity": severity,
            "confidence": confidence,
            "details": {
                "camera_id": cam_id,
                "congestion_level": congestion,
                "anomaly_type": anomaly,
                "image_path": img,
            },
        })

    # News signals
    rows = conn.execute("""
        SELECT h3_cell, timestamp_utc, source_name, title, extracted_location,
               event_type, severity, confidence, urgency
        FROM processed_news
        WHERE timestamp_utc > ? OR created_at > ?
    """, (cutoff, cutoff)).fetchall()

    for h3_cell, ts, src, title, location, event_type, severity, confidence, urgency in rows:
        cells[h3_cell]["news"].append({
            "source": "news",
            "timestamp": ts,
            "event_type": event_type or "general",
            "severity": severity,
            "confidence": confidence,
            "details": {
                "source_name": src,
                "title": title,
                "extracted_location": location,
                "urgency": urgency,
            },
        })

    return dict(cells)


# ──────────────────────────────────────────────
# Step 2: Temporal decay function
# Recent signals matter more than older ones
# ──────────────────────────────────────────────
def temporal_weight(timestamp_str: str, half_life_minutes: int = 60) -> float:
    """
    Exponential decay weight based on signal age.
    Half-life of 60 minutes: signal at 60min old gets 0.5 weight.
    """
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        age_minutes = (datetime.now(timezone.utc) - ts).total_seconds() / 60
        if age_minutes < 0:
            age_minutes = 0
        decay = math.exp(-0.693 * age_minutes / half_life_minutes)
        return max(decay, 0.05)  # minimum 5% weight
    except (ValueError, TypeError):
        return 0.5  # default if timestamp is unparseable


# ──────────────────────────────────────────────
# Step 3: Cross-source corroboration score
# When multiple sources report similar events,
# confidence should increase non-linearly
# ──────────────────────────────────────────────
def compute_corroboration(signals: dict) -> float:
    """
    Compute how much different sources corroborate each other.
    Returns a bonus multiplier (1.0 = no corroboration, up to 1.5).
    """
    active_sources = {s for s, sigs in signals.items() if sigs}
    if len(active_sources) < 2:
        return 1.0

    # Collect all event types per source
    events_by_source = {}
    for source, sigs in signals.items():
        if sigs:
            events_by_source[source] = [s["event_type"] for s in sigs]

    # Check corroboration matrix for matching event pairs
    max_corroboration = 0.0
    sources = list(events_by_source.keys())

    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            for event_a in events_by_source[sources[i]]:
                for event_b in events_by_source[sources[j]]:
                    # Check both orderings in the matrix
                    score = CORROBORATION_MATRIX.get((event_a, event_b), 0)
                    if score == 0:
                        score = CORROBORATION_MATRIX.get((event_b, event_a), 0)
                    max_corroboration = max(max_corroboration, score)

    # More sources = higher bonus
    source_bonus = 1.0 + (len(active_sources) - 1) * 0.15
    corroboration_bonus = 1.0 + max_corroboration * 0.5

    return min(source_bonus * corroboration_bonus, 1.5)


# ──────────────────────────────────────────────
# Step 4: Attention-weighted severity fusion
# ──────────────────────────────────────────────
def fuse_cell_signals(signals: dict) -> dict | None:
    """
    Apply attention-weighted fusion to all signals in an H3 cell.
    
    Attention weights combine:
      - Source reliability (static)
      - Temporal freshness (decay)
      - Cross-source corroboration (dynamic)
    
    Returns fused assessment for the cell.
    """
    all_signals = []
    for source, sigs in signals.items():
        for sig in sigs:
            all_signals.append(sig)

    if not all_signals:
        return None

    # Compute attention weight for each signal
    weighted_signals = []
    for sig in all_signals:
        source_weight = SOURCE_WEIGHTS.get(sig["source"], 0.5)
        time_weight = temporal_weight(sig["timestamp"])
        signal_confidence = sig["confidence"]

        # Attention score = source_reliability × temporal_freshness × self_confidence
        attention = source_weight * time_weight * signal_confidence
        weighted_signals.append({
            **sig,
            "attention_weight": round(attention, 4),
        })

    # Corroboration bonus
    corroboration = compute_corroboration(signals)

    # Weighted severity: sum(severity × attention) / sum(attention)
    total_attention = sum(s["attention_weight"] for s in weighted_signals)
    if total_attention == 0:
        return None

    fused_severity = sum(
        s["severity"] * s["attention_weight"] for s in weighted_signals
    ) / total_attention

    # Apply corroboration bonus to severity
    fused_severity = min(fused_severity * corroboration, 1.0)

    # Fused confidence: weighted average boosted by corroboration
    fused_confidence = sum(
        s["confidence"] * s["attention_weight"] for s in weighted_signals
    ) / total_attention
    fused_confidence = min(fused_confidence * corroboration, 1.0)

    # Determine primary event type (highest attention signal)
    primary_signal = max(weighted_signals, key=lambda s: s["attention_weight"])
    primary_event = primary_signal["event_type"]

    # Collect all unique event types
    all_events = list(set(s["event_type"] for s in all_signals if s["event_type"]))

    # Active source count
    active_sources = list(set(s["source"] for s in all_signals))

    return {
        "fused_severity": round(fused_severity, 4),
        "fused_confidence": round(fused_confidence, 4),
        "corroboration_bonus": round(corroboration, 4),
        "primary_event_type": primary_event,
        "all_event_types": all_events,
        "active_sources": active_sources,
        "source_count": len(active_sources),
        "signal_count": len(all_signals),
        "weighted_signals": weighted_signals,
    }


# ──────────────────────────────────────────────
# Step 5: Enrich with POI and road context
# ──────────────────────────────────────────────
def enrich_with_context(conn, h3_cell: str) -> dict:
    """
    Find POIs and roads in the same H3 cell.
    These are the supply chain assets at risk.
    """
    # POIs in this cell
    pois = conn.execute("""
        SELECT poi_type, name, address, lat, lon
        FROM processed_pois WHERE h3_cell = ?
    """, (h3_cell,)).fetchall()

    affected_pois = [
        {"type": t, "name": n, "address": a, "lat": lat, "lon": lon}
        for t, n, a, lat, lon in pois
    ]

    # Roads in this cell
    roads = conn.execute("""
        SELECT DISTINCT road_name, highway_type, ref
        FROM processed_roads WHERE h3_cell = ?
    """, (h3_cell,)).fetchall()

    affected_roads = [
        {"name": n, "type": t, "ref": r}
        for n, t, r in roads
        if n != "Unnamed"
    ]

    # Railways in this cell
    railways = conn.execute("""
        SELECT DISTINCT railway_name, operator
        FROM processed_railways WHERE h3_cell = ?
    """, (h3_cell,)).fetchall()

    affected_railways = [
        {"name": n, "operator": o}
        for n, o in railways
        if n != "Unnamed"
    ]

    return {
        "affected_pois": affected_pois,
        "affected_roads": affected_roads,
        "affected_railways": affected_railways,
        "gas_stations": [p for p in affected_pois if p["type"] == "gas_station"],
        "grocery_stores": [p for p in affected_pois if p["type"] in ("supermarket", "convenience", "greengrocer")],
    }


# ──────────────────────────────────────────────
# Step 6: Generate location description
# ──────────────────────────────────────────────
def generate_location_text(context: dict, signals: dict) -> str:
    """Build a human-readable location string."""
    parts = []

    # Use road names if available
    for road in context["affected_roads"][:3]:
        name = road["ref"] or road["name"]
        if name and name not in parts:
            parts.append(name)

    # Use news location if available
    for sig in signals.get("news", []):
        loc = sig["details"].get("extracted_location")
        if loc and loc not in parts and "unspecified" not in loc.lower():
            parts.append(loc)

    # Use POI names for context
    for poi in context["affected_pois"][:2]:
        name = poi.get("name")
        if name and name not in parts and name != "Unnamed":
            parts.append(f"near {name}")

    if not parts:
        parts.append("Arlington, VA")

    return ", ".join(parts[:3]) + ", Arlington, VA"


# ──────────────────────────────────────────────
# Step 7: Generate explanation
# ──────────────────────────────────────────────
def generate_explanation(fusion_result: dict, context: dict) -> str:
    """Build a human-readable explanation of the disruption."""
    sources = fusion_result["active_sources"]
    severity = fusion_result["fused_severity"]
    events = fusion_result["all_event_types"]

    parts = []

    # Filter out meaningless event types
    meaningful_events = [
        e for e in events 
        if e and e not in ("none", "unknown", "clear", "forecast")
    ]

    # What's happening
    if meaningful_events:
        event_desc = ", ".join(
            e.replace("_", " ").replace("forecast ", "").title() 
            for e in meaningful_events[:3]
        )
        parts.append(f"Detected: {event_desc}.")
    
    # Source evidence
    source_details = []
    for sig in fusion_result["weighted_signals"]:
        if sig["severity"] < 0.1:
            continue  # skip non-events

        if sig["source"] == "weather":
            alert = sig["details"].get("alert_type", "")
            if alert and "forecast" not in alert:
                source_details.append(f"NWS has issued a {alert} for this area")
            elif alert:
                precip = sig["details"].get("precipitation", 0)
                wind = sig["details"].get("wind_speed", 0)
                if precip and precip > 50:
                    source_details.append(f"Forecast shows {precip}% precipitation probability")
                if wind and wind > 25:
                    source_details.append(f"Wind speeds forecasted at {wind} mph")

        elif sig["source"] == "traffic":
            cam = sig["details"].get("camera_id", "unknown")
            anomaly = sig["details"].get("anomaly_type", "")
            congestion = sig["details"].get("congestion_level", "")
            
            if anomaly and anomaly not in ("none", "unknown"):
                source_details.append(f"Traffic camera {cam} has detected {anomaly} on the road")
            elif congestion and congestion not in ("clear", "unknown"):
                source_details.append(f"Traffic camera {cam} shows {congestion} congestion")
            elif sig["severity"] > 0.2:
                source_details.append(f"Traffic camera {cam} shows abnormal road conditions")

        elif sig["source"] == "news":
            title = sig["details"].get("title", "")
            src = sig["details"].get("source_name", "")
            if title:
                source_details.append(f'{src} reports: "{title[:60]}"')

    if source_details:
        parts.append(" ".join(source_details[:3]) + ".")

    # Impact
    gas = len(context["gas_stations"])
    grocery = len(context["grocery_stores"])
    roads = len(context["affected_roads"])

    impacts = []
    if gas > 0:
        names = [s["name"] for s in context["gas_stations"][:2] if s["name"] != "Unnamed"]
        if names:
            impacts.append(f"{gas} gas station{'s' if gas > 1 else ''} ({', '.join(names)})")
        else:
            impacts.append(f"{gas} gas station{'s' if gas > 1 else ''}")
    if grocery > 0:
        names = [s["name"] for s in context["grocery_stores"][:2] if s["name"] != "Unnamed"]
        if names:
            impacts.append(f"{grocery} grocery store{'s' if grocery > 1 else ''} ({', '.join(names)})")
        else:
            impacts.append(f"{grocery} grocery store{'s' if grocery > 1 else ''}")
    if roads > 0:
        road_names = [r["ref"] or r["name"] for r in context["affected_roads"][:2] if r["name"] != "Unnamed"]
        if road_names:
            impacts.append(f"roads including {', '.join(road_names)}")

    if impacts:
        parts.append(f"Supply chain at risk: {', '.join(impacts)}.")

    # Corroboration note
    if fusion_result["corroboration_bonus"] > 1.1:
        source_names = fusion_result["active_sources"]
        parts.append(
            f"This assessment is corroborated by {len(source_names)} independent sources "
            f"({', '.join(source_names)})."
        )

    if not parts:
        parts.append("Abnormal conditions detected. Monitoring for further developments.")

    return " ".join(parts)


# ──────────────────────────────────────────────
# Step 8: Generate source links
# ──────────────────────────────────────────────
def generate_source_links(fusion_result: dict) -> list:
    """Extract traceable source links. Each link is just the actual
    reference to the original data — a URL or file path."""
    links = []
    seen = set()  # dedup

    for sig in fusion_result["weighted_signals"]:
        # Skip non-events
        if sig["severity"] < 0.1:
            continue

        if sig["source"] == "weather":
            alert_type = sig["details"].get("alert_type", "forecast")
            if "forecast" in str(alert_type).lower():
                continue  # skip plain forecasts, only show actual alerts
            link = {
                "source_name": "National Weather Service",
                "description": f"{alert_type} for Arlington County",
                "link": "https://api.weather.gov/alerts/active/zone/VAZ054",
            }

        elif sig["source"] == "traffic":
            cam_id = sig["details"].get("camera_id", "unknown")
            anomaly = sig["details"].get("anomaly_type", "none")
            congestion = sig["details"].get("congestion_level", "unknown")
            image_path = sig["details"].get("image_path", "")

            condition = anomaly if anomaly not in ("none", "unknown") else congestion
            if condition in ("clear", "unknown", "none"):
                condition = "abnormal conditions"

            link = {
                "source_name": f"VDOT Camera {cam_id}",
                "description": f"{condition} detected",
                "link": image_path,
            }

        elif sig["source"] == "news":
            title = sig["details"].get("title", "")
            src_name = sig["details"].get("source_name", "")

            link = {
                "source_name": src_name,
                "description": title[:80] if title else "News article",
                "link": sig["details"].get("url", ""),
            }

        else:
            continue

        # Dedup by link
        dedup_key = link.get("link", "") or link.get("description", "")
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        links.append(link)

    return links


# ──────────────────────────────────────────────
# Step 9: Determine alert tier
# ──────────────────────────────────────────────
def determine_alert_tier(severity: float, source_count: int) -> str:
    """Classify the fused alert into Watch/Warning/Critical."""
    if (severity >= TIER_THRESHOLDS["CRITICAL"]["min_severity"] and
            source_count >= TIER_THRESHOLDS["CRITICAL"]["min_sources"]):
        return "CRITICAL"
    elif (severity >= TIER_THRESHOLDS["WARNING"]["min_severity"] and
            source_count >= TIER_THRESHOLDS["WARNING"]["min_sources"]):
        return "WARNING"
    elif severity >= TIER_THRESHOLDS["WATCH"]["min_severity"]:
        return "WATCH"
    return "NONE"


# ──────────────────────────────────────────────
# Step 10: Get recommended actions
# ──────────────────────────────────────────────
def get_recommended_actions(primary_event: str, context: dict) -> list:
    """Get specific actions based on event type and affected assets."""
    # Normalize event type
    event_key = primary_event.lower().replace(" ", "_")

    # Map NWS alert types to our action categories
    event_mapping = {
        "flash_flood_warning": "flooding",
        "flood_warning": "flooding",
        "severe_thunderstorm_warning": "severe_storm",
        "tornado_warning": "severe_storm",
        "winter_storm_warning": "winter_storm",
        "ice_storm_warning": "winter_storm",
    }

    action_key = event_mapping.get(event_key, event_key)

    # Get base actions
    actions = ACTION_MAP.get(action_key, ACTION_MAP["general"]).copy()

    # Add POI-specific actions
    if context["gas_stations"]:
        names = [s["name"] for s in context["gas_stations"][:3]]
        actions.append(f"Priority: Monitor fuel availability at {', '.join(names)}")

    if context["grocery_stores"]:
        names = [s["name"] for s in context["grocery_stores"][:3]]
        actions.append(f"Priority: Monitor supply levels at {', '.join(names)}")

    return actions


# ──────────────────────────────────────────────
# Main: Run the full fusion pipeline
# ──────────────────────────────────────────────
def run_fusion() -> list:
    """Execute the full fusion pipeline. Returns list of alerts."""
    print("\n   Running Fusion Engine...\n")

    conn = get_db()
    if not conn:
        return []

    # Step 1: Collect all recent signals
    print("  [1/5] Collecting signals from all sources...")
    cell_signals = collect_signals(conn)
    total_cells = len(cell_signals)
    print(f"        Found signals in {total_cells} H3 cells")

    if total_cells == 0:
        print("\n     No recent signals found. Run data ingestion first.")
        conn.close()
        return []

    alerts = []

    # Step 2-9: Process each cell
    print("  [2/5] Fusing signals per cell...")
    for h3_cell, signals in cell_signals.items():
        # Count active sources
        active = sum(1 for s, sigs in signals.items() if sigs)
        total_sigs = sum(len(sigs) for sigs in signals.values())

        # Fuse signals
        fusion = fuse_cell_signals(signals)
        if not fusion:
            continue

        # Determine alert tier
        tier = determine_alert_tier(fusion["fused_severity"], fusion["source_count"])
        if tier == "NONE":
            continue

        # Enrich with POI/road context
        context = enrich_with_context(conn, h3_cell)

        # Generate outputs
        location_text = generate_location_text(context, signals)
        explanation = generate_explanation(fusion, context)
        source_links = generate_source_links(fusion)
        actions = get_recommended_actions(fusion["primary_event_type"], context)

        # Build alert object
        alert = {
            "h3_cell": h3_cell,
            "alert_tier": tier,
            "location": location_text,
            "explanation": explanation,
            "severity": fusion["fused_severity"],
            "confidence": fusion["fused_confidence"],
            "corroboration_factor": fusion["corroboration_bonus"],
            "source_count": fusion["source_count"],
            "signal_count": fusion["signal_count"],
            "primary_event": fusion["primary_event_type"],
            "all_events": fusion["all_event_types"],
            "source_links": source_links,
            "recommended_actions": actions,
            "affected_pois": context["affected_pois"],
            "affected_roads": context["affected_roads"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        alerts.append(alert)

        # Print
        log_icon = {"CRITICAL": "[C]", "WARNING": "[W]", "WATCH": "[*]"}.get(tier, "[ ]")
        print(f"    {log_icon} {tier:8s} | sev={fusion['fused_severity']:.2f} | "
              f"conf={fusion['fused_confidence']:.2f} | "
              f"sources={fusion['source_count']} | {location_text[:50]}")

    # Step 10: Sort by severity and store
    alerts.sort(key=lambda a: a["severity"], reverse=True)

    print(f"\n  [3/5] Storing {len(alerts)} alerts...")
    
    # Clear old alerts first — fusion always generates fresh
    conn.execute("DELETE FROM alerts")
    
    for alert in alerts:
        conn.execute(
            """
            INSERT INTO alerts 
            (h3_cell, timestamp_utc, alert_tier, combined_severity, 
             source_count, sources, affected_pois, affected_roads, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert["h3_cell"],
                alert["timestamp"],
                alert["alert_tier"],
                alert["severity"],
                alert["source_count"],
                json.dumps(alert["source_links"]),
                json.dumps(alert["affected_pois"]),
                json.dumps(alert["affected_roads"]),
                alert["explanation"],
                alert["timestamp"],
            ),
        )

    conn.commit()
    conn.close()

    # Print summary
    print(f"\n  [4/5] Summary:")
    tier_counts = defaultdict(int)
    for a in alerts:
        tier_counts[a["alert_tier"]] += 1

    print(f"\n{'=' * 60}")
    print(f"  [C] CRITICAL alerts: {tier_counts.get('CRITICAL', 0)}")
    print(f"  [W] WARNING alerts:  {tier_counts.get('WARNING', 0)}")
    print(f"  [*] WATCH alerts:    {tier_counts.get('WATCH', 0)}")
    print(f"      Total alerts:    {len(alerts)}")
    print(f"{'=' * 60}")

    # Print detailed alerts
    if alerts:
        print(f"\n  [5/5] Detailed Alerts:\n")
        for i, alert in enumerate(alerts, 1):
            icon = {"CRITICAL": "[C]", "WARNING": "[W]", "WATCH": "[*]"}.get(alert["alert_tier"], "[ ]")
            print(f"  {'-' * 56}")
            print(f"  {icon} Alert #{i}: {alert['alert_tier']}")
            print(f"  {'-' * 56}")
            print(f"      Location:    {alert['location']}")
            print(f"      Severity:    {alert['severity']:.2f}")
            print(f"      Confidence:  {alert['confidence']:.2f}")
            print(f"      Sources:     {alert['source_count']} ({', '.join(alert['all_events'][:3])})")
            print(f"      Explanation: {alert['explanation'][:120]}...")

            if alert["affected_pois"]:
                poi_summary = []
                gas = [p for p in alert["affected_pois"] if p["type"] == "gas_station"]
                grocery = [p for p in alert["affected_pois"] if p["type"] != "gas_station"]
                if gas:
                    poi_summary.append(f"{len(gas)} gas stations")
                if grocery:
                    poi_summary.append(f"{len(grocery)} grocery stores")
                print(f"      At risk:    {', '.join(poi_summary)}")

            print(f"\n      Recommended Actions:")
            for j, action in enumerate(alert["recommended_actions"][:4], 1):
                print(f"     {j}. {action}")

            print(f"\n      Source Evidence:")
            for link in alert["source_links"]:
                print(f"     • {link['source_name']}: {link['description']}")
                print(f"       -> {link['link']}")
            print()

    return alerts


if __name__ == "__main__":
    run_fusion()