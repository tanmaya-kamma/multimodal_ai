import sys
from pathlib import Path

# Add the project root to sys.path
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from app.fusion.route_analysis import analyze_routes
import json

source = {"name": "Ballston", "lat": 38.8816, "lon": -77.1110}
destinations = [
    {"name": "Pentagon City", "lat": 38.8625, "lon": -77.0597}
]

try:
    result = analyze_routes(source, destinations)
    print("Success:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"FAILED with error: {e}")
    import traceback
    traceback.print_exc()
