"""
traffic_source.py — Fetches traffic camera images for Arlington, VA
from VDOT snapshot cameras. Stores in raw_traffic with coordinates.

Location: app/sources/traffic/traffic_source.py

Usage (from project root):
    python app/sources/traffic/traffic_source.py
"""

import requests
import sqlite3
from pathlib import Path
from datetime import datetime, UTC

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "supply_chain.db"
IMAGE_DIR = BASE_DIR / "data" / "camera_images"

# Subdirectories for clean organization
LATEST_DIR = IMAGE_DIR / "latest"
PREVIOUS_DIR = IMAGE_DIR / "previous"
BASELINE_DAY_DIR = IMAGE_DIR / "baseline_day"
BASELINE_NIGHT_DIR = IMAGE_DIR / "baseline_night"

LATEST_DIR.mkdir(parents=True, exist_ok=True)
PREVIOUS_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_DAY_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_NIGHT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# VDOT Cameras with verified Arlington coordinates
# Coordinates sourced from known intersection locations
# To add more: visit 511virginia.org, click a camera,
# right-click image → copy URL, add here with location name
# ──────────────────────────────────────────────
CAMERAS = [
    # I-66 corridor (east-west through north Arlington)
    {"id": "arl_i66_1",     "lat": 38.8850, "lon": -77.0960, "location": "I-66 at Fairfax Dr",          "url": "https://snapshot.vdotcameras.com/b263fugn6jp26q7m4jr3wnuse4x3z45e.png"},
    {"id": "arl_i66_2",     "lat": 38.8849, "lon": -77.1131, "location": "I-66 at Glebe Rd",            "url": "https://snapshot.vdotcameras.com/44ywflb282uusgbdtfcmf54gx5f5f8fh.png"},
    {"id": "arl_i66_3",     "lat": 38.8835, "lon": -77.1230, "location": "I-66 at Washington Blvd",     "url": "https://snapshot.vdotcameras.com/38iggm3xn7t5tr9grypj6mmtuxjp165p.png"},

    # Fairfax Dr / Rt 50 corridor
    {"id": "arl_fairfax_1", "lat": 38.8823, "lon": -77.1117, "location": "Fairfax Dr at Ballston",      "url": "https://snapshot.vdotcameras.com/FairfaxVideo0730.png"},
    {"id": "arl_fairfax_2", "lat": 38.8833, "lon": -77.1035, "location": "Fairfax Dr at Virginia Sq",   "url": "https://snapshot.vdotcameras.com/FairfaxVideo0720.png"},
    {"id": "arl_fairfax_3", "lat": 38.8765, "lon": -77.1064, "location": "Rt 50 at Arlington Blvd",     "url": "https://snapshot.vdotcameras.com/FairfaxVideo0250.png"},
    {"id": "arl_fairfax_4", "lat": 38.8822, "lon": -77.0852, "location": "Rt 50 at Courthouse",         "url": "https://snapshot.vdotcameras.com/FairfaxVideo0320.png"},

    # Central Arlington arterials
    {"id": "arl_cam_1",     "lat": 38.8872, "lon": -77.0946, "location": "Clarendon Blvd",              "url": "https://snapshot.vdotcameras.com/f7vw5o9t5u6py1y47331trvnivtgn4gd.png"},
    {"id": "arl_cam_2",     "lat": 38.8780, "lon": -77.0880, "location": "Washington Blvd at Kirkwood",  "url": "https://snapshot.vdotcameras.com/2umf2vg4agfmbgwwxyumoknf46ypx2pt.png"},
    {"id": "arl_cam_3",     "lat": 38.8765, "lon": -77.1064, "location": "Arlington Blvd at Glebe",     "url": "https://snapshot.vdotcameras.com/za5npm668ttapl89jptwxvsczkozi4u2.png"},
    {"id": "arl_cam_4",     "lat": 38.8567, "lon": -77.0857, "location": "Columbia Pike",               "url": "https://snapshot.vdotcameras.com/FairfaxCCTV0265.png"},

    # Major intersections
    {"id": "arl_cctv_1",    "lat": 38.8569, "lon": -77.0792, "location": "Glebe Rd at Columbia Pike",   "url": "https://snapshot.vdotcameras.com/FairfaxPCCTV07.png"},
    {"id": "arl_cctv_2",    "lat": 38.8570, "lon": -77.0626, "location": "S Glebe Rd at Army Navy Dr",  "url": "https://snapshot.vdotcameras.com/FairfaxCCTV245.png"},

    # Rosslyn
    {"id": "arl_misc_1",    "lat": 38.8968, "lon": -77.0725, "location": "Rosslyn",                     "url": "https://snapshot.vdotcameras.com/NO0152.png"},

    # Pentagon City / Crystal City / South Arlington
    {"id": "arl_misc_2",    "lat": 38.8620, "lon": -77.0590, "location": "Route 1 at Pentagon City",    "url": "https://snapshot.vdotcameras.com/594mpxfpegw24t2nwvp9b4x5hvu8g07m.png"},
    {"id": "arl_misc_3",    "lat": 38.8560, "lon": -77.0497, "location": "Crystal City Jeff Davis Hwy", "url": "https://snapshot.vdotcameras.com/u6p6nr6f96t226pl8v206f2bd33f9d5f.png"},
    {"id": "arl_misc_4",    "lat": 38.8430, "lon": -77.0740, "location": "Shirlington Four Mile Run",   "url": "https://snapshot.vdotcameras.com/48def6e2gkm562pnw6zrfh8k66tgjwgt.png"},
]


def already_exists(cursor, camera_id):
    """Check if this camera was fetched in the last 1 minute (dedup)."""
    cursor.execute("""
        SELECT COUNT(*) FROM raw_traffic
        WHERE camera_id = ?
        AND datetime(substr(fetched_at, 1, 19)) >= datetime('now', '-1 minutes')
    """, (camera_id,))
    return cursor.fetchone()[0] > 0


def download_image(url, camera_id):
    """Download camera snapshot. Preserves previous frame for change detection."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        content_type = response.headers.get("Content-Type", "")

        if response.status_code == 200 and "image" in content_type:
            latest_path = LATEST_DIR / f"{camera_id}.jpg"
            previous_path = PREVIOUS_DIR / f"{camera_id}.jpg"

            # Rotate: current latest becomes previous
            if latest_path.exists():
                import shutil
                shutil.copy2(latest_path, previous_path)

            # Save new image as latest
            with open(latest_path, "wb") as f:
                f.write(response.content)

            return str(latest_path)

    except Exception as e:
        print(f"     ❌ Download error for {camera_id}: {e}")

    return None


def run():
    """Fetch all camera images and store in raw_traffic."""
    print("\n📸 Fetching camera images for Arlington, VA...")
    print(f"📁 Images: {IMAGE_DIR}")
    print(f"📁 Database: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0
    failed = 0

    for cam in CAMERAS:
        if already_exists(cursor, cam["id"]):
            skipped += 1
            continue

        image_path = download_image(cam["url"], cam["id"])

        if not image_path:
            failed += 1
            continue

        cursor.execute("""
            INSERT INTO raw_traffic (camera_id, image_path, lat, lon, fetched_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            cam["id"],
            image_path,
            cam["lat"],
            cam["lon"],
            datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ))
        inserted += 1
        print(f"  ✅ {cam['id']:20s} — {cam['location']}")

    conn.commit()
    conn.close()

    print(f"\n{'=' * 50}")
    print(f"  ✅ New images stored:    {inserted}")
    print(f"  ⏩ Duplicates skipped:   {skipped}")
    print(f"  ❌ Failed downloads:     {failed}")
    print(f"  📸 Total cameras:        {len(CAMERAS)}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    run()