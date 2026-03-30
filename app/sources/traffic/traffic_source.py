import requests
import sqlite3
from pathlib import Path
from datetime import datetime, UTC

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "supply_chain.db"
IMAGE_DIR = BASE_DIR / "data" / "camera_images"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ✅ Stable image sources (always return images)
CAMERAS = [
    # --- ORIGINAL CAMERAS ---
    {"id": "arl_cam_1", "url": "https://snapshot.vdotcameras.com/f7vw5o9t5u6py1y47331trvnivtgn4gd.png"},
    {"id": "arl_cam_2", "url": "https://snapshot.vdotcameras.com/2umf2vg4agfmbgwwxyumoknf46ypx2pt.png"},
    {"id": "arl_cam_3", "url": "https://snapshot.vdotcameras.com/za5npm668ttapl89jptwxvsczkozi4u2.png"},
    {"id": "arl_cam_4", "url": "https://snapshot.vdotcameras.com/FairfaxCCTV0265.png"},

    # --- NEW CAMERAS (CLEANED + RENAMED) ---
    {"id": "arl_i66_1", "url": "https://snapshot.vdotcameras.com/b263fugn6jp26q7m4jr3wnuse4x3z45e.png"},
    {"id": "arl_i66_2", "url": "https://snapshot.vdotcameras.com/44ywflb282uusgbdtfcmf54gx5f5f8fh.png"},
    {"id": "arl_i66_3", "url": "https://snapshot.vdotcameras.com/38iggm3xn7t5tr9grypj6mmtuxjp165p.png"},

    {"id": "arl_fairfax_1", "url": "https://snapshot.vdotcameras.com/FairfaxVideo0730.png"},
    {"id": "arl_fairfax_2", "url": "https://snapshot.vdotcameras.com/FairfaxVideo0720.png"},
    {"id": "arl_fairfax_3", "url": "https://snapshot.vdotcameras.com/FairfaxVideo0250.png"},
    {"id": "arl_fairfax_4", "url": "https://snapshot.vdotcameras.com/FairfaxVideo0320.png"},

    {"id": "arl_cctv_1", "url": "https://snapshot.vdotcameras.com/FairfaxPCCTV07.png"},
    {"id": "arl_cctv_2", "url": "https://snapshot.vdotcameras.com/FairfaxCCTV245.png"},

    {"id": "arl_misc_1", "url": "https://snapshot.vdotcameras.com/NO0152.png"},
    {"id": "arl_misc_2", "url": "https://snapshot.vdotcameras.com/594mpxfpegw24t2nwvp9b4x5hvu8g07m.png"},
    {"id": "arl_misc_3", "url": "https://snapshot.vdotcameras.com/u6p6nr6f96t226pl8v206f2bd33f9d5f.png"},
    {"id": "arl_misc_4", "url": "https://snapshot.vdotcameras.com/48def6e2gkm562pnw6zrfh8k66tgjwgt.png"},
]


def already_exists(cursor, camera_id):
    cursor.execute("""
        SELECT COUNT(*) FROM raw_traffic
        WHERE camera_id = ?
        AND datetime(substr(fetched_at, 1, 19)) >= datetime('now', '-1 minutes')
    """, (camera_id,))
    
    return cursor.fetchone()[0] > 0

def download_image(url, camera_id):
    try:
        print(f"📥 Downloading from: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=10)

        print("Status:", response.status_code)

        content_type = response.headers.get("Content-Type", "")
        print("Content-Type:", content_type)

        if response.status_code == 200 and "image" in content_type:
            timestamp = int(datetime.now(UTC).timestamp())
            filename = f"{camera_id}_{timestamp}.jpg"
            file_path = IMAGE_DIR / filename

            with open(file_path, "wb") as f:
                f.write(response.content)

            print("✅ Saved:", file_path)
            return str(file_path)

        else:
            print("❌ Not a valid image response")

    except Exception as e:
        print("❌ Download error:", e)

    return None


def run():
    print("\n📸 Fetching camera images...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0

    for cam in CAMERAS:
        camera_id = cam["id"]

        # 🚫 Skip duplicates
        if already_exists(cursor, camera_id):
            print(f"⏩ Skipping {camera_id} (recently added)")
            continue

        image_path = download_image(cam["url"], camera_id)

        if not image_path:
            continue

        cursor.execute("""
        INSERT INTO raw_traffic (camera_id, image_path, fetched_at)
        VALUES (?, ?, ?)
        """, (
            cam["id"],
            image_path,
            datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        ))

        inserted += 1

    conn.commit()
    conn.close()

    print(f"\n✅ Stored {inserted} new images\n")


if __name__ == "__main__":
    run()