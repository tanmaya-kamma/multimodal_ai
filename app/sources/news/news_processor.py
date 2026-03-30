"""
news_processor.py — Reads raw_news, extracts locations via keyword-based NER,
scores severity, assigns H3 cells, writes to processed_news.

Location: app/sources/news/news_processor.py

Processing pipeline:
  1. Read unprocessed articles from raw_news
  2. Extract location mentions (keyword matching to known Arlington locations)
  3. Classify event type (flooding, road_closure, etc.)
  4. Score severity (0.0 - 1.0)
  5. Score confidence (0.0 - 1.0)
  6. Assign H3 cell based on extracted location
  7. Write to processed_news

Usage (from project root):
    python app/sources/news/news_processor.py
"""

import sqlite3
import hashlib
import re
import h3
from pathlib import Path
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
H3_RESOLUTION = 8
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"

# Arlington center (default when no specific location found)
ARLINGTON_CENTER = {"lat": 38.8816, "lon": -77.0910}

# ──────────────────────────────────────────────
# Known Arlington locations for keyword-based NER
# Maps location name → (lat, lon)
# When an article mentions one of these, we know
# the approximate coordinates of the event.
# ──────────────────────────────────────────────
ARLINGTON_LOCATIONS = {
    # Neighborhoods / Areas
    "pentagon city":        (38.862, -77.059),
    "crystal city":         (38.856, -77.049),
    "rosslyn":              (38.897, -77.072),
    "ballston":             (38.882, -77.112),
    "clarendon":            (38.887, -77.094),
    "courthouse":           (38.890, -77.086),
    "shirlington":          (38.843, -77.074),
    "columbia pike":        (38.858, -77.085),
    "lee highway":          (38.904, -77.130),
    "falls church":         (38.882, -77.171),
    "cherrydale":           (38.893, -77.108),
    "lyon park":            (38.883, -77.091),
    "ashton heights":       (38.880, -77.100),
    "virginia square":      (38.883, -77.103),
    "bluemont":             (38.872, -77.120),
    "glencarlyn":           (38.857, -77.118),
    "nauck":                (38.849, -77.083),
    "penrose":              (38.850, -77.090),
    "aurora highlands":     (38.851, -77.063),
    "addison heights":      (38.862, -77.070),
    "alcova heights":       (38.855, -77.098),
    "arlington ridge":      (38.851, -77.060),
    "douglas park":         (38.847, -77.087),
    "fairlington":          (38.843, -77.058),
    "south arlington":      (38.845, -77.070),
    "north arlington":      (38.900, -77.110),
    "east falls church":    (38.886, -77.158),

    # Major roads
    "route 1":              (38.850, -77.051),
    "route 50":             (38.880, -77.095),
    "i-66":                 (38.885, -77.100),
    "i-395":                (38.850, -77.060),
    "wilson boulevard":     (38.887, -77.097),
    "washington boulevard": (38.872, -77.090),
    "glebe road":           (38.860, -77.080),
    "walter reed":          (38.855, -77.085),
    "george washington parkway": (38.880, -77.055),
    "arlington boulevard":  (38.870, -77.105),
    "jefferson davis highway": (38.850, -77.051),
    "army navy drive":      (38.858, -77.056),
    "four mile run":        (38.843, -77.074),
    "potomac river":        (38.880, -77.055),

    # Landmarks
    "pentagon":             (38.871, -77.056),
    "reagan airport":       (38.852, -77.040),
    "arlington cemetery":   (38.876, -77.069),
    "amazon hq2":           (38.901, -77.049),
}

# ──────────────────────────────────────────────
# Event type classification keywords
# Maps keywords → event_type
# ──────────────────────────────────────────────
EVENT_KEYWORDS = {
    "flooding": [
        "flood", "flooding", "flash flood", "floodwater",
        "submerged", "inundated", "water level", "overflowed",
    ],
    "road_closure": [
        "road closed", "road closure", "street closed",
        "lane closed", "lane closure", "blocked road",
        "impassable", "barricade",
    ],
    "severe_storm": [
        "tornado", "hurricane", "thunderstorm", "severe storm",
        "hail", "funnel cloud", "wind damage", "lightning",
    ],
    "winter_storm": [
        "snow", "ice", "blizzard", "freezing rain",
        "sleet", "black ice", "whiteout", "ice storm",
    ],
    "power_outage": [
        "power outage", "power failure", "blackout",
        "no power", "electricity", "downed power line",
        "dominion energy",
    ],
    "accident": [
        "accident", "crash", "collision", "pileup",
        "overturned", "jackknife", "vehicle fire",
    ],
    "infrastructure": [
        "water main break", "gas leak", "sinkhole",
        "bridge closed", "structural damage", "collapse",
    ],
    "supply_disruption": [
        "supply chain", "delivery delay", "shortage",
        "out of stock", "supply disruption", "distribution",
        "resupply", "fuel shortage", "grocery shortage",
    ],
    "emergency_alert": [
        "emergency alert", "evacuation", "shelter in place",
        "state of emergency", "emergency declaration",
        "emergency response", "rescue", "first responders",
    ],
}

# ──────────────────────────────────────────────
# Severity keywords with scores
# ──────────────────────────────────────────────
SEVERITY_KEYWORDS = {
    # Extreme (0.85 - 1.0)
    "tornado": 0.95, "hurricane": 0.95,
    "flash flood": 0.90, "evacuation": 0.90,
    "state of emergency": 0.95, "emergency declaration": 0.90,
    "water rescue": 0.90, "life threatening": 0.95,
    "catastrophic": 0.95, "destroyed": 0.90,

    # Severe (0.65 - 0.85)
    "flooding": 0.80, "flood": 0.75,
    "submerged": 0.80, "impassable": 0.75,
    "stranded": 0.75, "road closed": 0.70,
    "severe storm": 0.75, "power outage": 0.70,
    "multiple injuries": 0.80, "collapse": 0.85,

    # Moderate (0.40 - 0.65)
    "road closure": 0.55, "accident": 0.50,
    "crash": 0.50, "heavy rain": 0.45,
    "thunderstorm": 0.50, "lane closure": 0.45,
    "downed tree": 0.45, "debris": 0.45,
    "delay": 0.40, "disruption": 0.50,

    # Minor (0.20 - 0.40)
    "advisory": 0.30, "watch": 0.25,
    "warning": 0.35, "minor flooding": 0.35,
    "ponding": 0.25, "wind": 0.25,
    "rain": 0.20, "fog": 0.20,
}

# Source reliability scores
SOURCE_CONFIDENCE = {
    "ARLnow": 0.85,        # Local, reliable, specific to Arlington
    "WTOP Arlington": 0.80, # Regional, reliable
    "Google News": 0.70,    # Aggregator, may include less reliable sources
}


# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────
def get_db():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


# ──────────────────────────────────────────────
# NLP Functions
# ──────────────────────────────────────────────
def extract_location(title: str, content: str) -> tuple:
    """
    Extract the most specific location mentioned in the article.
    Returns (location_name, lat, lon) or defaults to Arlington center.
    """
    text = f"{title} {content}".lower()

    # Check from most specific to least specific
    # Sort locations by name length (longer = more specific) to match first
    sorted_locations = sorted(ARLINGTON_LOCATIONS.items(), key=lambda x: len(x[0]), reverse=True)

    for location_name, (lat, lon) in sorted_locations:
        if location_name in text:
            return location_name.title(), lat, lon

    # Check for generic "arlington" mention
    if "arlington" in text:
        return "Arlington (general)", ARLINGTON_CENTER["lat"], ARLINGTON_CENTER["lon"]

    # No location found
    return None, ARLINGTON_CENTER["lat"], ARLINGTON_CENTER["lon"]


def classify_event_type(title: str, content: str) -> str:
    """Classify the article into an event type based on keywords."""
    text = f"{title} {content}".lower()

    # Count keyword matches per event type
    scores = {}
    for event_type, keywords in EVENT_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[event_type] = count

    if not scores:
        return "general"

    # Return the event type with most keyword matches
    return max(scores, key=lambda x: scores[x])


def calculate_severity(title: str, content: str) -> float:
    """
    Calculate a disruption severity score (0.0-1.0) based on
    keyword analysis of the article text.
    """
    text = f"{title} {content}".lower()

    # Find all matching severity keywords and take the highest
    matched_scores = []
    for keyword, score in SEVERITY_KEYWORDS.items():
        if keyword in text:
            matched_scores.append(score)

    if not matched_scores:
        return 0.2  # baseline for any disaster-relevant article

    # Use the top 3 scores with diminishing weight
    matched_scores.sort(reverse=True)
    if len(matched_scores) == 1:
        severity = matched_scores[0]
    elif len(matched_scores) == 2:
        severity = matched_scores[0] * 0.7 + matched_scores[1] * 0.3
    else:
        severity = matched_scores[0] * 0.6 + matched_scores[1] * 0.25 + matched_scores[2] * 0.15

    return min(severity, 1.0)


def calculate_confidence(source_name: str, location_found: bool, event_type: str) -> float:
    """
    Calculate confidence score based on source reliability,
    whether a specific location was extracted, and event specificity.
    """
    # Base confidence from source
    base = SOURCE_CONFIDENCE.get(source_name, 0.5)

    # Bonus for specific location mention
    if location_found:
        base += 0.1

    # Slight penalty for vague event types
    if event_type == "general":
        base -= 0.15

    return max(0.1, min(base, 1.0))


def calculate_sentiment(title: str, content: str) -> float:
    """
    Simple sentiment scoring (-1.0 to 1.0).
    Disaster articles are generally negative.
    """
    text = f"{title} {content}".lower()

    negative_words = [
        "damage", "destroyed", "killed", "injured", "death",
        "devastation", "crisis", "danger", "threat", "severe",
        "worst", "catastrophic", "critical", "trapped", "stranded",
        "closed", "blocked", "flooded", "failed", "collapsed",
    ]

    # Positive/recovery words
    positive_words = [
        "restored", "recovered", "reopened", "cleared",
        "repaired", "improved", "subsided", "safe",
        "helped", "rescued", "volunteers",
    ]

    neg_count = sum(1 for w in negative_words if w in text)
    pos_count = sum(1 for w in positive_words if w in text)

    if neg_count + pos_count == 0:
        return -0.3  # default slightly negative for disaster articles

    sentiment = (pos_count - neg_count) / (pos_count + neg_count)
    return max(-1.0, min(sentiment, 1.0))


def calculate_urgency(event_type: str, severity: float) -> float:
    """Calculate urgency (0.0-1.0) based on event type and severity."""
    urgency_base = {
        "flooding": 0.85,
        "severe_storm": 0.80,
        "road_closure": 0.60,
        "power_outage": 0.55,
        "accident": 0.50,
        "winter_storm": 0.70,
        "infrastructure": 0.65,
        "supply_disruption": 0.75,
        "emergency_alert": 0.90,
        "general": 0.30,
    }

    base = urgency_base.get(event_type, 0.3)
    # Weight with severity
    return min((base * 0.6 + severity * 0.4), 1.0)


# ──────────────────────────────────────────────
# Main processor
# ──────────────────────────────────────────────
def process_news():
    """Read raw_news, process each article, write to processed_news."""
    print("\n🔧 Processing news articles...\n")

    conn = get_db()
    if not conn:
        return

    # Get all raw articles that haven't been processed yet
    # (check by article_id not existing in processed_news)
    raw_articles = conn.execute("""
        SELECT rn.id, rn.source_name, rn.article_id, rn.title, rn.content, 
               rn.url, rn.published_at
        FROM raw_news rn
        LEFT JOIN processed_news pn ON rn.article_id = pn.title
        WHERE pn.id IS NULL
    """).fetchall()

    # Fallback: just get all raw articles if the join is tricky
    if not raw_articles:
        raw_articles = conn.execute("""
            SELECT id, source_name, article_id, title, content, url, published_at
            FROM raw_news
        """).fetchall()

    print(f"  📄 Found {len(raw_articles)} articles to process\n")

    # Clear existing processed news to avoid duplicates on re-run
    conn.execute("DELETE FROM processed_news")

    processed_count = 0

    for row in raw_articles:
        raw_id, source_name, article_id, title, content, url, published_at = row

        if not title:
            continue

        content = content or ""

        # 1. Extract location
        location_name, lat, lon = extract_location(title, content)
        location_found = location_name is not None and "general" not in (location_name or "").lower()

        # 2. Classify event type
        event_type = classify_event_type(title, content)

        # 3. Calculate scores
        severity = calculate_severity(title, content)
        confidence = calculate_confidence(source_name, location_found, event_type)
        sentiment = calculate_sentiment(title, content)
        urgency = calculate_urgency(event_type, severity)

        # 4. Assign H3 cell
        h3_cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)

        # 5. Determine timestamp (use article published time)
        timestamp_utc = published_at or datetime.now(timezone.utc).isoformat()

        # 6. Write to processed_news
        conn.execute(
            """
            INSERT INTO processed_news 
            (h3_cell, timestamp_utc, source_name, title, extracted_location,
             event_type, sentiment, urgency, severity, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                h3_cell,
                timestamp_utc,
                source_name,
                title,
                location_name or "Arlington (unspecified)",
                event_type,
                round(sentiment, 3),
                round(urgency, 3),
                round(severity, 3),
                round(confidence, 3),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        processed_count += 1

        # Print summary
        sev_icon = "🔴" if severity >= 0.7 else "🟠" if severity >= 0.4 else "🟡"
        loc_str = f" @ {location_name}" if location_name else ""
        print(
            f"  {sev_icon} [{event_type:18s}] sev={severity:.2f} conf={confidence:.2f}"
            f"{loc_str}"
        )
        print(f"     {title[:75]}...")

    conn.commit()
    conn.close()

    print(f"\n  ✅ Processed {processed_count} articles into processed_news")

    # Print summary stats
    conn = get_db()
    if conn:
        total = conn.execute("SELECT COUNT(*) FROM processed_news").fetchone()[0]
        cells = conn.execute("SELECT COUNT(DISTINCT h3_cell) FROM processed_news").fetchone()[0]
        avg_sev = conn.execute("SELECT AVG(severity) FROM processed_news").fetchone()[0] or 0

        # Event type breakdown
        types = conn.execute(
            "SELECT event_type, COUNT(*) FROM processed_news GROUP BY event_type ORDER BY COUNT(*) DESC"
        ).fetchall()

        conn.close()

        print("\n" + "=" * 50)
        print(f"  📰 Total processed articles: {total}")
        print(f"  📍 Unique H3 cells: {cells}")
        print(f"  📊 Average severity: {avg_sev:.3f}")
        if types:
            print(f"  📋 Event types:")
            for event_type, count in types:
                print(f"     {event_type}: {count}")
        print("=" * 50)

    print("\n✅ News processing complete.\n")


if __name__ == "__main__":
    process_news()