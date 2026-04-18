import sys
from pathlib import Path

# Add app and fusion to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "app" / "fusion"))

from route_analysis import analyze_routes

source = {"name": "Ballston", "lat": 38.882, "lon": -77.112}
destinations = [
    {"name": "Pentagon City", "lat": 38.862, "lon": -77.059},
    {"name": "Crystal City", "lat": 38.856, "lon": -77.049}
]

print("Running route analysis test...")
result = analyze_routes(source, destinations)

import json
print(json.dumps(result, indent=2))
