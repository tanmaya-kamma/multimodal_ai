"""
news_source.py — Fetches news articles relevant to Arlington, VA
from multiple RSS feeds. Deduplicates using SHA256 hashing.

Location: app/sources/news/news_source.py

Sources:
  1. ARLnow — Arlington's main local news
  2. Google News RSS — disaster keyword search for Arlington VA
  3. WTOP — DC area breaking news

Usage (from project root):
    python app/sources/news/news_source.py
"""

import httpx
import sqlite3
import hashlib
import json
import time
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("❌ feedparser not installed. Run: pip install feedparser")
    exit(1)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "supply_chain.db"

# Only ingest articles from the last N days
MAX_AGE_DAYS = 7

# Disaster-relevant keywords to filter articles
DISASTER_KEYWORDS = [
    "flood", "flooding", "flash flood",
    "storm", "thunderstorm", "tornado", "hurricane",
    "snow", "ice", "blizzard", "freezing",
    "road closure", "road closed", "road blocked",
    "accident", "crash", "collision",
    "power outage", "power failure", "blackout",
    "fire", "wildfire",
    "emergency", "evacuation", "shelter",
    "water main", "gas leak",
    "debris", "fallen tree", "downed",
    "disruption", "delay", "closure",
    "supply", "shortage", "delivery",
    "rescue", "damage", "destroyed",
    "warning", "advisory", "watch",
]

# RSS Feed sources
RSS_FEEDS = [
    {
        "name": "ARLnow",
        "url": "https://www.arlnow.com/feed/",
        "description": "Arlington VA local news",
    },
    {
        "name": "Google News",
        "url": (
            "https://news.google.com/rss/search?"
            "q=Arlington+Virginia+"
            "emergency+OR+flooding+OR+storm+OR+accident+OR+road+closure+OR+power+outage"
            "&hl=en-US&gl=US&ceid=US:en"
        ),
        "description": "Google News search for Arlington VA disaster-related articles",
    },
    {
        "name": "WTOP Arlington",
        "url": "https://wtop.com/local/virginia/arlington/feed/",
        "description": "WTOP DC area news - Arlington section",
    },
]


# ──────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────
def get_db():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run setup_db.py first: python app/db/setup_db.py")
        return None
    return sqlite3.connect(DB_PATH)


def generate_article_hash(title: str, source: str) -> str:
    """Generate SHA256 hash of title + source for deduplication."""
    raw = f"{title.strip().lower()}|{source.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def article_exists(conn, article_hash: str) -> bool:
    """Check if an article with this hash already exists in raw_news."""
    result = conn.execute(
        "SELECT COUNT(*) FROM raw_news WHERE article_id = ?",
        (article_hash,),
    ).fetchone()
    return result[0] > 0


def is_disaster_relevant(title: str, content: str = "") -> bool:
    """Check if article is related to disasters/disruptions."""
    text = f"{title} {content}".lower()
    return any(keyword in text for keyword in DISASTER_KEYWORDS)


def is_too_old(published_str: str) -> bool:
    """Check if article is older than MAX_AGE_DAYS."""
    try:
        # Try parsing ISO format
        dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
        return dt < cutoff
    except (ValueError, TypeError, AttributeError):
        # If we can't parse the date, accept the article
        return False


def clean_html(text: str | None) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    text = str(text)
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def parse_published_date(entry) -> str:
    """Extract and normalize published date to ISO 8601 UTC."""
    # feedparser parses dates into a time struct
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        try:
            dt = datetime(*published[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except (ValueError, TypeError):
            pass

    # Fallback: try the raw string
    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        return raw

    # Last resort: current time
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────
# Fetch from a single RSS feed
# ──────────────────────────────────────────────
def fetch_feed(feed_config: dict) -> list:
    """Fetch and parse a single RSS feed. Returns list of articles."""
    name = feed_config["name"]
    url = feed_config["url"]

    print(f"\n    📡 Fetching {name}...")
    print(f"       URL: {url[:80]}...")

    try:
        # Use httpx to fetch (some feeds block default feedparser user agent)
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers={
                "User-Agent": "SupplyChainDisruptionApp/1.0"
            })
            resp.raise_for_status()
            raw_feed = resp.text
    except Exception as e:
        print(f"    ❌ Failed to fetch {name}: {e}")
        return []

    # Parse the RSS feed
    feed = feedparser.parse(raw_feed)
    entries = feed.get("entries") or []
    print(f"       Found {len(entries)} total entries")

    articles = []
    for entry in entries:
        title = clean_html(str(entry.get("title", "")))

        # Extract content from whichever field is available
        raw_content = entry.get("summary", "") or entry.get("description", "")
        if not raw_content:
            content_list = entry.get("content", [])
            if content_list and len(content_list) > 0:
                raw_content = content_list[0].get("value", "")
        content = clean_html(str(raw_content))
        url = entry.get("link", "")
        author = entry.get("author", "")
        published = parse_published_date(entry)

        if not title:
            continue

        articles.append({
            "source_name": name,
            "title": title,
            "content": content,
            "url": url,
            "author": author,
            "published_at": published,
        })

    return articles


# ──────────────────────────────────────────────
# Main ingestion
# ──────────────────────────────────────────────
def fetch_all_news(filter_relevant: bool = True):
    """
    Fetch news from all RSS feeds, filter for disaster relevance,
    deduplicate, and store in raw_news.

    Args:
        filter_relevant: If True, only store disaster-relevant articles.
                         Set False to store everything (useful for testing).
    """
    print("\n📰 Fetching news for Arlington, VA...")
    print(f"📁 Database: {DB_PATH}")
    print(f"🔍 Filtering for disaster relevance: {filter_relevant}\n")

    conn = get_db()
    if not conn:
        return

    total_fetched = 0
    total_relevant = 0
    total_new = 0
    total_duplicate = 0
    total_too_old = 0

    for feed_config in RSS_FEEDS:
        articles = fetch_feed(feed_config)
        total_fetched += len(articles)

        for article in articles:
            # Skip old articles
            if is_too_old(article["published_at"]):
                total_too_old += 1
                continue

            # Filter for disaster relevance
            if filter_relevant:
                if not is_disaster_relevant(article["title"], article["content"]):
                    continue
            total_relevant += 1

            # Dedup check with SHA256
            article_hash = generate_article_hash(article["title"], article["source_name"])

            if article_exists(conn, article_hash):
                total_duplicate += 1
                continue

            # Insert into raw_news
            conn.execute(
                """
                INSERT INTO raw_news 
                (source_name, article_id, author, title, content, url, published_at, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article["source_name"],
                    article_hash,
                    article["author"],
                    article["title"],
                    article["content"],
                    article["url"],
                    article["published_at"],
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            total_new += 1

            print(f"    ✅ NEW: [{article['source_name']}] {article['title'][:70]}...")

        # Small delay between feeds
        time.sleep(1)

    conn.commit()
    conn.close()

    print("\n" + "=" * 50)
    print(f"  📰 Total articles fetched:   {total_fetched}")
    print(f"  ⏭️  Too old (>{MAX_AGE_DAYS} days):      {total_too_old}")
    print(f"  🔍 Disaster-relevant:        {total_relevant}")
    print(f"  ✅ New articles stored:       {total_new}")
    print(f"  ⏭️  Duplicates skipped:       {total_duplicate}")
    print("=" * 50)
    print("\n✅ News ingestion complete.\n")


if __name__ == "__main__":
    fetch_all_news(filter_relevant=True)