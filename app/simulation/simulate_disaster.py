"""
simulate_disaster.py — Injects a realistic flash flood scenario
into the database for hackathon demo.

Location: app/simulation/simulate_disaster.py

Scenario: Severe thunderstorm + flash flooding hits east Arlington.
Affected area: a compact Pentagon City -> Crystal City -> Route 1
corridor pocket (3 adjacent H3 cells). Kept intentionally small so the
rest of the road network (Columbia Pike, Glebe Rd, Arlington Blvd,
Washington Blvd, Shirlington) stays clear and the route analyzer can
always offer a viable alternate.

Usage:
    python app/simulation/simulate_disaster.py              # inject
    python app/simulation/simulate_disaster.py --cleanup    # remove

After injecting, run the fusion engine:
    python app/fusion/fusion_engine.py
"""


import sqlite3
import json
import h3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

H3_RESOLUTION = 8
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "supply_chain.db"
NOW = datetime.now(timezone.utc)


def get_db():
    if not DB_PATH.exists():
        print(f"[ERROR] Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


def ts(minutes_offset=0):
    return (NOW + timedelta(minutes=minutes_offset)).isoformat()


def cell(lat, lon):
    return h3.latlng_to_cell(lat, lon, H3_RESOLUTION)


# ──────────────────────────────────────────────
# Affected locations — a tight 3-cell pocket in east Arlington.
# These three coordinates resolve to three mutually-adjacent H3
# res-8 cells (Pentagon City, Crystal City, Route 1 corridor).
# Every severity-bearing signal below snaps onto one of these three
# anchors, so the disruption never spreads beyond 3 cells and the
# surrounding network always offers an alternate route.
# ──────────────────────────────────────────────
FLOOD_ZONE = [
    {"name": "Shirlington",      "lat": 38.843, "lon": -77.086},  # Cell A - I-395 near Shirlington
    {"name": "Pentagon City",    "lat": 38.861, "lon": -77.063},  # Cell B - I-395 near Pentagon City
]


def inject_weather(conn):
    print("\n  [WEATHER] Injecting weather alerts + forecast...")

    # Raw weather: the full NWS alert response
    alert_response = {
        "data_type": "alerts",
        "point_name": "Arlington Zone VAZ054",
        "response": {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {
                        "id": "NWS-FLOOD-001",
                        "event": "Flash Flood Warning",
                        "severity": "Severe",
                        "certainty": "Observed",
                        "urgency": "Immediate",
                        "headline": "Flash Flood Warning issued for Arlington County until 6 PM EDT",
                        "description": (
                            f"Heavy rainfall has caused flash flooding in the {FLOOD_ZONE[0]['name']} "
                            f"and {FLOOD_ZONE[1]['name']} area. Several roads along the highway "
                            "are impassable. Water levels are rising rapidly. Low-lying areas "
                            f"around {FLOOD_ZONE[0]['name']} and {FLOOD_ZONE[1]['name']} are experiencing significant "
                            "flooding."
                        ),
                        "instruction": "Turn around, don't drown. Avoid flood-prone areas.",
                        "onset": ts(-10),
                        "expires": ts(180),
                        "senderName": "NWS Baltimore MD/Washington DC",
                        "areaDesc": "Arlington County, VA",
                        "affectedZones": ["VAZ054"],
                    }
                },
                {
                    "properties": {
                        "id": "NWS-STORM-001",
                        "event": "Severe Thunderstorm Warning",
                        "severity": "Severe",
                        "certainty": "Observed",
                        "urgency": "Immediate",
                        "headline": "Severe Thunderstorm Warning for Arlington County",
                        "description": (
                            f"A severe thunderstorm producing heavy rain and damaging winds "
                            f"up to 60 mph is moving through east Arlington over the {FLOOD_ZONE[0]['name']} "
                            f"and {FLOOD_ZONE[1]['name']}. Rainfall rates exceeding 2 inches "
                            "per hour."
                        ),
                        "instruction": "Move to an interior room on the lowest floor.",
                        "onset": ts(-60),
                        "expires": ts(120),
                        "senderName": "NWS Baltimore MD/Washington DC",
                        "areaDesc": "Arlington County, VA",
                        "affectedZones": ["VAZ054"],
                    }
                },
            ],
        },
    }

    conn.execute(
        "INSERT INTO raw_weather (lat, lon, response_json, fetched_at) VALUES (?, ?, ?, ?)",
        (FLOOD_ZONE[0]["lat"], FLOOD_ZONE[0]["lon"], json.dumps(alert_response), ts(0)),
    )

    # Processed weather: alerts at each of the 3 pocket cells
    # (lat/lon, severity, confidence chosen so Pentagon City + Crystal
    #  City read CRITICAL once traffic/news corroborate, Route 1 WARNING)
    alerts = [
        ("Flash Flood Warning",         FLOOD_ZONE[0]["lat"], FLOOD_ZONE[0]["lon"], 0.95, 1.0,  ts(-10)),
        ("Flash Flood Warning",         FLOOD_ZONE[1]["lat"], FLOOD_ZONE[1]["lon"], 0.95, 1.0,  ts(-10)),
        ("Severe Thunderstorm Warning", FLOOD_ZONE[0]["lat"], FLOOD_ZONE[0]["lon"], 0.80, 1.0,  ts(-60)),
    ]

    for alert_type, lat, lon, severity, confidence, timestamp in alerts:
        conn.execute(
            """INSERT INTO processed_weather 
            (h3_cell, timestamp_utc, alert_type, severity, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (cell(lat, lon), timestamp, alert_type, severity, confidence, ts(0)),
        )

    # Processed weather: severe forecast at all 3 pocket points
    for point in FLOOD_ZONE:
        for offset in [-60, -30, 0, 30, 60]:
            conn.execute(
                """INSERT INTO processed_weather 
                (h3_cell, timestamp_utc, alert_type, temperature, wind_speed, 
                 precipitation_mm, severity, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cell(point["lat"], point["lon"]), ts(offset),
                 "forecast_heavy_rain_and_flooding", 58, 45, 95, 0.75, 0.7, ts(0)),
            )

    count = len(alerts) + len(FLOOD_ZONE) * 5
    print(f"    DONE: {count} weather records")


def inject_traffic(conn):
    print("\n  [TRAFFIC] Injecting traffic camera detections...")

    cameras = [
        {
            "id": "CAM-SHIR-001", "lat": FLOOD_ZONE[0]["lat"], "lon": FLOOD_ZONE[0]["lon"],
            "congestion": "blocked", "anomaly": "flooding", "severity": 0.95, "confidence": 0.92,
            "time": ts(10),
            "desc": f"Standing water ~18 inches deep near {FLOOD_ZONE[0]['name']}",
        },
        {
            "id": "CAM-PENT-002", "lat": FLOOD_ZONE[1]["lat"], "lon": FLOOD_ZONE[1]["lon"],
            "congestion": "blocked", "anomaly": "flooding", "severity": 0.90, "confidence": 0.90,
            "time": ts(25),
            "desc": f"Intersection submerged near {FLOOD_ZONE[1]['name']}",
        },
    ]

    for cam in cameras:
        conn.execute(
            """INSERT INTO raw_traffic 
            (camera_id, image_path, raw_response, lat, lon, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (cam["id"], f"simulation/{cam['id']}.jpg",
             json.dumps({"description": cam["desc"]}),
             cam["lat"], cam["lon"], cam["time"]),
        )

        conn.execute(
            """INSERT INTO processed_traffic 
            (h3_cell, timestamp_utc, camera_id, congestion_level, 
             anomaly_type, image_path, severity, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cell(cam["lat"], cam["lon"]), cam["time"], cam["id"],
             cam["congestion"], cam["anomaly"], f"simulation/{cam['id']}.jpg",
             cam["severity"], cam["confidence"], ts(0)),
        )

    print(f"    DONE: {len(cameras)} traffic camera records")


def inject_news(conn):
    print("\n  [NEWS] Injecting news articles...")

    articles = [
        {
            "source": "ARLnow",
            "title": f"Flash Flooding Closes Roads Around {FLOOD_ZONE[0]['name']}",
            "content": (
                f"Several roads around {FLOOD_ZONE[0]['name']} are impassable due to flash flooding. "
                "Multiple vehicles reported stranded."
            ),
            "url": "https://www.arlnow.com/2026/flash-flooding",
            "published": ts(20),
            "location": FLOOD_ZONE[0]["name"],
            "event_type": "flooding",
            "lat": FLOOD_ZONE[0]["lat"], "lon": FLOOD_ZONE[0]["lon"],
            "severity": 0.85, "confidence": 0.90,
        },
        {
            "source": "WJLA ABC7",
            "title": f"Emergency Alert: Avoid {FLOOD_ZONE[1]['name']} Roads",
            "content": (
                f"Emergency Management is urging residents to avoid roads "
                f"around {FLOOD_ZONE[1]['name']}. Severe flooding reported."
            ),
            "url": "https://wjla.com/news/local/2026/emergency-alert-flooding",
            "published": ts(60),
            "location": FLOOD_ZONE[1]["name"],
            "event_type": "emergency_alert",
            "lat": FLOOD_ZONE[1]["lat"], "lon": FLOOD_ZONE[1]["lon"],
            "severity": 0.92, "confidence": 0.95,
        },
    ]

    for i, a in enumerate(articles, start=1):
        conn.execute(
            """INSERT INTO raw_news 
            (source_name, article_id, title, content, url, published_at, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (a["source"], f"SIM-{a['source'].upper().replace(' ', '')}-{i:03d}",
             a["title"], a["content"], a["url"], a["published"], ts(0)),
        )

        conn.execute(
            """INSERT INTO processed_news 
            (h3_cell, timestamp_utc, source_name, title, extracted_location,
             event_type, sentiment, urgency, severity, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cell(a["lat"], a["lon"]), a["published"], a["source"], a["title"],
             a["location"], a["event_type"], -0.8, 0.9,
             a["severity"], a["confidence"], ts(0)),
        )

    print(f"    DONE: {len(articles)} news articles")


def print_summary(conn):
    print(f"\n{'=' * 60}")
    print("  DB SUMMARY AFTER SIMULATION")
    print(f"{'=' * 60}")

    for table in ["raw_weather", "raw_traffic", "raw_news",
                   "processed_weather", "processed_traffic", "processed_news"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:25s} {count:4d} records")

    # Show converging cells
    print(f"\n  CONVERGING CELLS WITH MULTIPLE SOURCES:")
    rows = conn.execute("""
        SELECT h3_cell, COUNT(DISTINCT source) as n, GROUP_CONCAT(DISTINCT source) as sources
        FROM (
            SELECT h3_cell, 'weather' as source FROM processed_weather WHERE severity > 0
            UNION ALL
            SELECT h3_cell, 'traffic' as source FROM processed_traffic WHERE severity > 0
            UNION ALL
            SELECT h3_cell, 'news' as source FROM processed_news WHERE severity > 0
        )
        GROUP BY h3_cell
        HAVING n >= 2
        ORDER BY n DESC
    """).fetchall()

    for h3_cell, count, sources in rows:
        poi_count = conn.execute(
            "SELECT COUNT(*) FROM processed_pois WHERE h3_cell = ?", (h3_cell,)
        ).fetchone()[0]
        road_count = conn.execute(
            "SELECT COUNT(DISTINCT road_name) FROM processed_roads WHERE h3_cell = ? AND road_name != 'Unnamed'",
            (h3_cell,)
        ).fetchone()[0]

        tier = "CRITICAL" if count >= 3 else "WARNING"
        extras = []
        if poi_count:
            extras.append(f"{poi_count} POIs")
        if road_count:
            extras.append(f"{road_count} roads")
        extra_str = f" | {', '.join(extras)}" if extras else ""

        print(f"    {tier} {h3_cell[:12]}... -> {count} sources ({sources}){extra_str}")

    print(f"{'=' * 60}")


def cleanup():
    print("\n[CLEANUP] Cleaning up simulation data...")
    conn = get_db()
    if not conn:
        return

    # Clear all processed live data (simulation + real)
    conn.execute("DELETE FROM processed_weather")
    conn.execute("DELETE FROM processed_traffic")
    conn.execute("DELETE FROM processed_news")
    conn.execute("DELETE FROM alerts")

    # Clear raw simulation data
    conn.execute("DELETE FROM raw_weather WHERE response_json LIKE '%NWS-FLOOD%'")
    conn.execute("DELETE FROM raw_weather WHERE response_json LIKE '%NWS-STORM%'")
    conn.execute("DELETE FROM raw_traffic WHERE camera_id LIKE 'CAM-%'")
    conn.execute("DELETE FROM raw_news WHERE article_id LIKE 'SIM-%'")

    conn.commit()
    conn.close()
    print("  DONE: Simulation data removed.\n")


def main():
    if "--cleanup" in sys.argv:
        cleanup()
        return

    conn = get_db()
    if not conn:
        return

    print(f"\n{'=' * 60}")
    print("  SIMULATING: Flash Flood in East Arlington")
    print(f"{'=' * 60}")
    print(f"  Time:     {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    area_str = " -> ".join([p["name"] for p in FLOOD_ZONE])
    print(f"  Area:     {area_str}")
    print(f"  Event:    Severe thunderstorm + flash flooding ({len(FLOOD_ZONE)}-cell pocket)")
    print(f"{'=' * 60}")

    inject_weather(conn)
    inject_traffic(conn)
    inject_news(conn)

    conn.commit()

    print_summary(conn)
    conn.close()

    print("\n[READY] Simulation ready! Now run:")
    print("   python app/fusion/fusion_engine.py")
    print("\n   Then test routes. A route that crosses the pocket should be")
    print("   flagged, with a clear alternate around it, e.g.:")
    print('   POST /arlington/routes/analyze')
    print('   { "source": {"name": "Rosslyn"},')
    print('     "destinations": [{"name": "Pentagon City"}, {"name": "Crystal City"}] }')
    print(f"\n   To remove: python app/simulation/simulate_disaster.py --cleanup\n")


if __name__ == "__main__":
    main()