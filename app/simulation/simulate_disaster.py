"""
simulate_disaster.py — Injects a realistic flash flood scenario
into the database for hackathon demo.

Location: app/simulation/simulate_disaster.py

Scenario: Severe thunderstorm + flash flooding hits south Arlington.
Affected area: Pentagon City → Crystal City → Shirlington corridor.

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
# Affected locations in south Arlington
# ──────────────────────────────────────────────
FLOOD_ZONE = [
    {"name": "Pentagon City",     "lat": 38.862, "lon": -77.059},
    {"name": "Crystal City",      "lat": 38.856, "lon": -77.049},
    {"name": "Route 1 corridor",  "lat": 38.850, "lon": -77.051},
    {"name": "Columbia Pike",     "lat": 38.858, "lon": -77.085},
    {"name": "Shirlington",       "lat": 38.843, "lon": -77.074},
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
                            "Heavy rainfall has caused flash flooding in the Route 1 corridor "
                            "and Pentagon City area. Several roads are impassable. Water levels "
                            "are rising rapidly in Four Mile Run. Low-lying areas near Crystal City "
                            "and Shirlington are experiencing significant flooding."
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
                            "A severe thunderstorm producing heavy rain and damaging winds "
                            "up to 60 mph is moving through south Arlington. Rainfall rates "
                            "exceeding 2 inches per hour."
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
        (38.862, -77.059, json.dumps(alert_response), ts(0)),
    )

    # Processed weather: alerts at each flood zone point
    alerts = [
        ("Flash Flood Warning",        38.862, -77.059, 0.95, 1.0,  ts(-10)),
        ("Flash Flood Warning",        38.856, -77.049, 0.95, 1.0,  ts(-10)),
        ("Flash Flood Warning",        38.850, -77.051, 0.90, 0.9,  ts(-10)),
        ("Severe Thunderstorm Warning", 38.858, -77.085, 0.80, 1.0,  ts(-60)),
        ("Flash Flood Warning",        38.843, -77.074, 0.85, 0.9,  ts(-5)),
    ]

    for alert_type, lat, lon, severity, confidence, timestamp in alerts:
        conn.execute(
            """INSERT INTO processed_weather 
            (h3_cell, timestamp_utc, alert_type, severity, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (cell(lat, lon), timestamp, alert_type, severity, confidence, ts(0)),
        )

    # Processed weather: severe forecast at all points
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
            "id": "CAM-RT1-001", "lat": 38.850, "lon": -77.051,
            "congestion": "blocked", "anomaly": "flooding", "severity": 0.95, "confidence": 0.92,
            "time": ts(10),
            "desc": "Standing water ~18 inches deep on Route 1 near Pentagon City",
        },
        {
            "id": "CAM-CPIKE-002", "lat": 38.858, "lon": -77.085,
            "congestion": "blocked", "anomaly": "flooding", "severity": 0.85, "confidence": 0.88,
            "time": ts(15),
            "desc": "Columbia Pike at Walter Reed - road flooded, vehicles stranded",
        },
        {
            "id": "CAM-395-003", "lat": 38.848, "lon": -77.055,
            "congestion": "slow", "anomaly": "debris", "severity": 0.70, "confidence": 0.85,
            "time": ts(20),
            "desc": "I-395 southbound near Shirlington - debris on road, 1 lane blocked",
        },
        {
            "id": "CAM-SHRL-004", "lat": 38.843, "lon": -77.074,
            "congestion": "blocked", "anomaly": "flooding", "severity": 0.90, "confidence": 0.90,
            "time": ts(25),
            "desc": "Shirlington Road at Four Mile Run - completely submerged",
        },
        {
            "id": "CAM-CC-005", "lat": 38.856, "lon": -77.049,
            "congestion": "slow", "anomaly": "flooding", "severity": 0.75, "confidence": 0.80,
            "time": ts(30),
            "desc": "Crystal Drive - water rising on road surface",
        },
        {
            "id": "CAM-23RD-006", "lat": 38.860, "lon": -77.060,
            "congestion": "blocked", "anomaly": "flooding", "severity": 0.88, "confidence": 0.87,
            "time": ts(60),
            "desc": "23rd Street S near Pentagon City Mall - intersection flooded",
        },
        {
            "id": "CAM-GLEBE-007", "lat": 38.855, "lon": -77.080,
            "congestion": "slow", "anomaly": "accident", "severity": 0.65, "confidence": 0.90,
            "time": ts(45),
            "desc": "Glebe Road at Columbia Pike - multi-vehicle accident in heavy rain",
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
            "title": "Flash Flooding Closes Multiple Roads in South Arlington",
            "content": (
                "Several roads in south Arlington are impassable due to flash flooding. "
                "Route 1 near Pentagon City and Columbia Pike at Walter Reed Drive are "
                "completely blocked. Multiple vehicles stranded near Shirlington."
            ),
            "url": "https://www.arlnow.com/2026/flash-flooding-south-arlington",
            "published": ts(20),
            "location": "Route 1, Pentagon City",
            "event_type": "flooding",
            "lat": 38.855, "lon": -77.059,
            "severity": 0.85, "confidence": 0.90,
        },
        {
            "source": "WTOP",
            "title": "I-395 Partially Closed Due to Debris and Flooding Near Shirlington",
            "content": (
                "Virginia State Police have closed one lane of I-395 southbound near "
                "Shirlington. Flooding on exit ramps. VDOT crews responding."
            ),
            "url": "https://wtop.com/virginia/2026/i395-flooding-arlington",
            "published": ts(30),
            "location": "I-395, Shirlington",
            "event_type": "road_closure",
            "lat": 38.848, "lon": -77.055,
            "severity": 0.75, "confidence": 0.85,
        },
        {
            "source": "Washington Post",
            "title": "Severe Storms Disrupt Supply Deliveries Across Northern Virginia",
            "content": (
                "Grocery delivery trucks and fuel tankers unable to reach several locations "
                "in south Arlington. Harris Teeter and Giant Food in Pentagon City report "
                "cancelled deliveries. Gas stations along Route 1 may face fuel shortages."
            ),
            "url": "https://www.washingtonpost.com/dc-md-va/2026/supply-chain-disruption-nova",
            "published": ts(90),
            "location": "Pentagon City, Crystal City",
            "event_type": "supply_disruption",
            "lat": 38.860, "lon": -77.055,
            "severity": 0.90, "confidence": 0.85,
        },
        {
            "source": "NBC Washington",
            "title": "Four Mile Run Overflows Banks, Flooding Shirlington Businesses",
            "content": (
                "Four Mile Run has overflowed near Shirlington, sending floodwaters into "
                "Shirlington Village shopping area. Multiple businesses affected. Arlington "
                "County has activated emergency response teams."
            ),
            "url": "https://www.nbcwashington.com/weather/2026/four-mile-run-flooding",
            "published": ts(45),
            "location": "Shirlington",
            "event_type": "flooding",
            "lat": 38.843, "lon": -77.074,
            "severity": 0.88, "confidence": 0.92,
        },
        {
            "source": "WJLA ABC7",
            "title": "Arlington County Issues Emergency Alert: Avoid South Arlington Roads",
            "content": (
                "Arlington County Emergency Management urging all residents to avoid roads "
                "in south Arlington. Pentagon City, Crystal City, and Route 1 corridor "
                "experiencing severe flooding. Emergency shelters opened at Wakefield High. "
                "At least 15 water rescues performed."
            ),
            "url": "https://wjla.com/news/local/2026/arlington-emergency-alert-flooding",
            "published": ts(60),
            "location": "South Arlington",
            "event_type": "emergency_alert",
            "lat": 38.855, "lon": -77.065,
            "severity": 0.92, "confidence": 0.95,
        },
    ]

    for a in articles:
        conn.execute(
            """INSERT INTO raw_news 
            (source_name, article_id, title, content, url, published_at, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (a["source"], f"SIM-{a['source'].upper().replace(' ', '')}-001",
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
    print("  SIMULATING: Flash Flood in South Arlington")
    print(f"{'=' * 60}")
    print(f"  Time:     {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Area:     Pentagon City -> Crystal City -> Shirlington")
    print(f"  Event:    Severe thunderstorm + flash flooding")
    print(f"{'=' * 60}")

    inject_weather(conn)
    inject_traffic(conn)
    inject_news(conn)

    conn.commit()

    print_summary(conn)
    conn.close()

    print("\n[READY] Simulation ready! Now run:")
    print("   python app/fusion/fusion_engine.py")
    print("\n   Then test routes through south Arlington:")
    print('   POST /arlington/routes/analyze')
    print('   { "source": {"name": "Ballston"},')
    print('     "destinations": [{"name": "Pentagon City"}, {"name": "Crystal City"}] }')
    print(f"\n   To remove: python app/simulation/simulate_disaster.py --cleanup\n")


if __name__ == "__main__":
    main()