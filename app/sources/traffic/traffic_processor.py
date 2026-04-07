"""
traffic_processor.py — Analyzes traffic camera images using two techniques:
  1. OpenCV change detection (fast, free — detects THAT something changed)
  2. Claude Vision API (intelligent — understands WHAT changed)

Location: app/sources/traffic/traffic_processor.py

Pipeline:
  1. Load latest + previous image for each camera
  2. OpenCV: compute change score between frames
  3. If change score > threshold → call Claude Vision for analysis
  4. Assign H3 cell + severity → write to processed_traffic

Usage (from project root):
    pip install opencv-python anthropic
    python app/sources/traffic/traffic_processor.py

Requires:
    ANTHROPIC_API_KEY environment variable (for Claude Vision)
"""

import sqlite3
import cv2
import numpy as np
import h3
import json
import base64
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import anthropic
except ImportError:
    print("❌ anthropic not installed. Run: pip install anthropic")
    exit(1)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
H3_RESOLUTION = 8
CHANGE_THRESHOLD = 0.35  # 0-1, above this triggers Claude Vision analysis

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "supply_chain.db"
IMAGE_DIR = BASE_DIR / "data" / "camera_images"

# Subdirectories
LATEST_DIR = IMAGE_DIR / "latest"
PREVIOUS_DIR = IMAGE_DIR / "previous"
BASELINE_DAY_DIR = IMAGE_DIR / "baseline_day"
BASELINE_NIGHT_DIR = IMAGE_DIR / "baseline_night"

# Daytime hours (6 AM to 8 PM local Arlington time = UTC-4 or UTC-5)
# Using UTC: roughly 10:00 - 00:00 UTC (covers both EST and EDT)
DAY_START_UTC = 10  # 6 AM EDT / 5 AM EST
DAY_END_UTC = 24    # 8 PM EDT / 7 PM EST (midnight UTC)

# Camera list (same as traffic_source.py — coordinates needed for H3)
CAMERAS = [
    {"id": "arl_i66_1",     "lat": 38.8850, "lon": -77.0960, "location": "I-66 at Fairfax Dr"},
    {"id": "arl_i66_2",     "lat": 38.8849, "lon": -77.1131, "location": "I-66 at Glebe Rd"},
    {"id": "arl_i66_3",     "lat": 38.8835, "lon": -77.1230, "location": "I-66 at Washington Blvd"},
    {"id": "arl_fairfax_1", "lat": 38.8823, "lon": -77.1117, "location": "Fairfax Dr at Ballston"},
    {"id": "arl_fairfax_2", "lat": 38.8833, "lon": -77.1035, "location": "Fairfax Dr at Virginia Sq"},
    {"id": "arl_fairfax_3", "lat": 38.8765, "lon": -77.1064, "location": "Rt 50 at Arlington Blvd"},
    {"id": "arl_fairfax_4", "lat": 38.8822, "lon": -77.0852, "location": "Rt 50 at Courthouse"},
    {"id": "arl_cam_1",     "lat": 38.8872, "lon": -77.0946, "location": "Clarendon Blvd"},
    {"id": "arl_cam_2",     "lat": 38.8780, "lon": -77.0880, "location": "Washington Blvd at Kirkwood"},
    {"id": "arl_cam_3",     "lat": 38.8765, "lon": -77.1064, "location": "Arlington Blvd at Glebe"},
    {"id": "arl_cam_4",     "lat": 38.8567, "lon": -77.0857, "location": "Columbia Pike"},
    {"id": "arl_cctv_1",    "lat": 38.8569, "lon": -77.0792, "location": "Glebe Rd at Columbia Pike"},
    {"id": "arl_cctv_2",    "lat": 38.8570, "lon": -77.0626, "location": "S Glebe Rd at Army Navy Dr"},
    {"id": "arl_misc_1",    "lat": 38.8968, "lon": -77.0725, "location": "Rosslyn"},
    {"id": "arl_misc_2",    "lat": 38.8620, "lon": -77.0590, "location": "Route 1 at Pentagon City"},
    {"id": "arl_misc_3",    "lat": 38.8560, "lon": -77.0497, "location": "Crystal City Jeff Davis Hwy"},
    {"id": "arl_misc_4",    "lat": 38.8430, "lon": -77.0740, "location": "Shirlington Four Mile Run"},
]


def get_db():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


def is_daytime() -> bool:
    """Check if it's currently daytime in Arlington (UTC-based)."""
    hour_utc = datetime.now(timezone.utc).hour
    return DAY_START_UTC <= hour_utc < DAY_END_UTC


def get_baseline_dir() -> Path:
    """Return the appropriate baseline directory for current time."""
    return BASELINE_DAY_DIR if is_daytime() else BASELINE_NIGHT_DIR


# ──────────────────────────────────────────────
# TECHNIQUE 1: OpenCV Change Detection
# ──────────────────────────────────────────────
def compute_change_score(latest_path: str, previous_path: str) -> tuple:
    """
    Compare two frames using structural similarity.
    Returns (change_score, diff_image).
    
    change_score: 0.0 = identical, 1.0 = completely different
    """
    # Load images in grayscale
    img_latest = cv2.imread(latest_path, cv2.IMREAD_GRAYSCALE)
    img_previous = cv2.imread(previous_path, cv2.IMREAD_GRAYSCALE)

    if img_latest is None or img_previous is None:
        return 0.0, None

    # Resize to same dimensions (cameras might crop slightly differently)
    h, w = 240, 320  # standardize to low res for speed
    img_latest = cv2.resize(img_latest, (w, h))
    img_previous = cv2.resize(img_previous, (w, h))

    # Apply Gaussian blur to reduce noise
    img_latest = cv2.GaussianBlur(img_latest, (5, 5), 0)
    img_previous = cv2.GaussianBlur(img_previous, (5, 5), 0)

    # Compute absolute difference
    diff = cv2.absdiff(img_latest, img_previous)

    # Threshold the difference to get significant changes
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # Change score = percentage of pixels that changed significantly
    change_score = np.sum(thresh > 0) / thresh.size

    return round(change_score, 4), diff


def compute_baseline_score(latest_path: str, camera_id: str) -> float:
    """
    Compare current frame against the correct baseline (day or night).
    Higher score = more different from normal conditions.
    """
    baseline_dir = get_baseline_dir()
    baseline_path = baseline_dir / f"{camera_id}.jpg"

    if not baseline_path.exists():
        return 0.0

    return compute_change_score(latest_path, str(baseline_path))[0]


# ──────────────────────────────────────────────
# TECHNIQUE 2: Claude Vision API Analysis
# ──────────────────────────────────────────────
def analyze_with_claude_vision(image_path: str, camera_location: str) -> Optional[dict[str, Any]]:
    """
    Send camera image to Claude Vision for intelligent analysis.
    Returns structured assessment of road conditions.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("    ⚠️  ANTHROPIC_API_KEY not set, using rule-based fallback")
        return None

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine media type
    media_type = "image/jpeg"
    if image_path.endswith(".png"):
        media_type = "image/png"

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"""Analyze this traffic camera image from {camera_location}, Arlington, VA.
You are assessing road conditions for supply chain disruption detection.

Respond ONLY with a JSON object, no other text:
{{
    "road_condition": "clear|wet|flooded|snow_covered|icy|debris",
    "congestion_level": "clear|light|moderate|heavy|blocked",
    "anomaly_detected": true/false,
    "anomaly_type": "none|flooding|accident|debris|stalled_vehicle|construction|poor_visibility",
    "visibility": "good|moderate|poor|very_poor",
    "truck_presence": "none|few|normal|many",
    "severity": 0.0 to 1.0 (supply chain disruption severity),
    "confidence": 0.0 to 1.0 (how confident you are in this assessment),
    "description": "One sentence describing what you see"
}}"""
                        },
                    ],
                }
            ],
        )

        # Parse response
        response_text = ""
        content_blocks = response.content if isinstance(response.content, list) else [response.content]
        for block in content_blocks:
            if isinstance(block, dict):
                response_text += block.get("text", "") or block.get("content", "")
            else:
                response_text += getattr(block, "text", None) or getattr(block, "content", None) or str(block)

        response_text = response_text.strip()
        # Clean markdown code fences if present
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        print(f"    ⚠️  Claude returned invalid JSON: {e}")
        return None
    except Exception as e:
        print(f"    ⚠️  Claude Vision error: {e}")
        return None


# ──────────────────────────────────────────────
# Fallback: rule-based severity from change score
# Used when Claude API is unavailable
# ──────────────────────────────────────────────
def rule_based_assessment(change_score: float, baseline_score: float) -> dict:
    """
    Generate a basic assessment from change detection scores alone.
    Without Claude Vision, we can only say "something changed" —
    we DON'T know what it is, so we set severity to 0 and
    anomaly to "none". Only Claude Vision can identify real issues.
    
    This prevents camera noise from generating false alerts.
    """
    combined = max(change_score, baseline_score)

    if combined >= 0.5:
        return {
            "road_condition": "unknown",
            "congestion_level": "unknown",
            "anomaly_detected": False,  # we don't KNOW it's an anomaly
            "anomaly_type": "none",
            "visibility": "unknown",
            "truck_presence": "unknown",
            "severity": 0.0,  # zero severity — only Claude Vision can assign real severity
            "confidence": 0.0,
            "description": f"Visual change detected (score: {combined:.2f}) — requires Vision AI analysis to classify",
        }
    else:
        return {
            "road_condition": "clear",
            "congestion_level": "clear",
            "anomaly_detected": False,
            "anomaly_type": "none",
            "visibility": "good",
            "truck_presence": "unknown",
            "severity": 0.0,
            "confidence": 0.5,
            "description": "Road appears normal",
        }


# ──────────────────────────────────────────────
# Main processor
# ──────────────────────────────────────────────
def process_traffic():
    print("\n🔧 Processing traffic camera images...\n")

    conn = get_db()
    if not conn:
        return

    # Clear previous processed records (we re-analyze each cycle)
    conn.execute("DELETE FROM processed_traffic WHERE camera_id NOT LIKE 'SIM%'")

    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if has_api_key:
        print("  🔑 Claude API key found — will use Vision analysis for anomalies")
    else:
        print("  ⚠️  No ANTHROPIC_API_KEY — using change detection only")
        print("     Set it with: set ANTHROPIC_API_KEY=your_key_here\n")

    processed = 0
    anomalies = 0
    api_calls = 0

    for cam in CAMERAS:
        camera_id = cam["id"]
        latest_path = LATEST_DIR / f"{camera_id}.jpg"
        previous_path = PREVIOUS_DIR / f"{camera_id}.jpg"

        if not latest_path.exists():
            continue

        # ── Step 1: OpenCV change detection ──
        change_score = 0.0
        if previous_path.exists():
            change_score, _ = compute_change_score(str(latest_path), str(previous_path))

        baseline_score = compute_baseline_score(str(latest_path), camera_id)

        effective_change = max(change_score, baseline_score)

        # ── Step 2: Decide whether to use Claude Vision ──
        assessment = None

        if effective_change >= CHANGE_THRESHOLD and has_api_key:
            # Significant change detected — use Claude Vision
            print(f"  🔍 {camera_id} — change={effective_change:.3f} → Sending to Claude Vision...")
            assessment = analyze_with_claude_vision(str(latest_path), cam["location"])
            api_calls += 1

            if assessment and assessment.get("anomaly_detected"):
                anomalies += 1
                icon = "🔴" if assessment["severity"] >= 0.7 else "🟠" if assessment["severity"] >= 0.4 else "🟡"
                print(f"    {icon} {assessment['description']}")
            elif assessment:
                print(f"    ✅ {assessment['description']}")

        if not assessment:
            # Either no significant change, no API key, or API failed
            assessment = rule_based_assessment(change_score, baseline_score)
            status = "normal" if effective_change < CHANGE_THRESHOLD else f"change={effective_change:.3f}"
            print(f"  📷 {camera_id:20s} — {status}")

        # ── Step 3: Store in processed_traffic ──
        h3_cell = h3.latlng_to_cell(cam["lat"], cam["lon"], H3_RESOLUTION)

        conn.execute(
            """
            INSERT INTO processed_traffic 
            (h3_cell, timestamp_utc, camera_id, congestion_level, 
             anomaly_type, image_path, severity, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                h3_cell,
                datetime.now(timezone.utc).isoformat(),
                camera_id,
                assessment.get("congestion_level", "unknown"),
                assessment.get("anomaly_type", "none"),
                str(latest_path),
                assessment.get("severity", 0.0),
                assessment.get("confidence", 0.5),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        processed += 1

    conn.commit()
    conn.close()

    # Summary
    print(f"\n{'=' * 55}")
    print(f"  📸 Cameras processed:     {processed}/{len(CAMERAS)}")
    print(f"  🔍 Claude Vision calls:   {api_calls}")
    print(f"  ⚠️  Anomalies detected:   {anomalies}")
    print(f"  📊 Change threshold:      {CHANGE_THRESHOLD}")
    print(f"{'=' * 55}")
    print("\n✅ Traffic processing complete.\n")


# ──────────────────────────────────────────────
# Utility: Capture baseline images
# Run this once on a clear day to set the reference
# ──────────────────────────────────────────────
def capture_baselines():
    """
    Copy current _latest images as baseline images.
    Automatically saves to day or night folder based on current time.
    
    Run this twice:
      - Once during a clear daytime   → saves to baseline_day/
      - Once during a clear nighttime → saves to baseline_night/
    """
    baseline_dir = get_baseline_dir()
    time_label = "DAYTIME" if is_daytime() else "NIGHTTIME"

    print(f"\n📸 Capturing {time_label} baseline images...")
    print(f"📁 Saving to: {baseline_dir}\n")

    count = 0
    for cam in CAMERAS:
        latest = LATEST_DIR / f"{cam['id']}.jpg"
        baseline = baseline_dir / f"{cam['id']}.jpg"

        if latest.exists():
            import shutil
            shutil.copy2(latest, baseline)
            print(f"  ✅ {cam['id']} → {time_label.lower()} baseline saved")
            count += 1
        else:
            print(f"  ⚠️  {cam['id']} — no latest image found")

    print(f"\n  Saved {count} {time_label.lower()} baselines.\n")


if __name__ == "__main__":
    import sys

    if "--baseline" in sys.argv:
        capture_baselines()
    else:
        process_traffic()