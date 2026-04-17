# GRIDCORE OMNI: Solaris HUD Stabilization

This repository contains the stabilized GRIDCORE OMNI platform, featuring the **Solaris HUD** (Claymorphic Bento UI, Blue POIs, Glowing Heatmap).

## 🛠 Golden CLI Sequence (Stabilization Flow)

Execute these commands in order to re-initialize the environment and verify the fusion pipeline:

1. **Cleanup**: `python -c "import os; [os.remove(f) for f in ['app/data/supply_chain.db'] if os.path.exists(f)]"`
2. **Re-initialize DB & Simulation**: `curl -X POST http://localhost:8000/arlington/simulate -H "Content-Type: application/json" -d "{ \"mode\": \"reset\" }"`
3. **Trigger Fusion**: `curl -X POST http://localhost:8000/arlington/fusion/rebuild`

---

## 🛰 Postman Sequential Routing Suite

Use the following JSON payloads for the `POST /arlington/routes/analyze` endpoint.

### Test 1: Avoidance (Rosslyn \u2192 Alexandria)
*Objective: Verify OSRM pipe calculates alternates via I-395/GW Parkway.*
```json
{
  "source": { "lat": 38.892, "lon": -77.0722, "name": "Rosslyn" },
  "destinations": [
    { "lat": 38.8048, "lon": -77.0469, "name": "Alexandria" }
  ]
}
```

### Test 2: Logistics (H3-Flooded Sequential Chain)
*Objective: Evaluate sequential status for Whole Foods and Shirlington waypoints.*
```json
{
  "source": { "lat": 38.8812, "lon": -77.091, "name": "HQ" },
  "destinations": [
    { "lat": 38.886, "lon": -77.0945, "name": "Whole Foods" },
    { "lat": 38.840, "lon": -77.086, "name": "Shirlington" }
  ]
}
```

### Test 3: Hybrid (Per-Destination Status Flags)
*Objective: Verify the `destination_results` array includes specific status strings.*
```json
{
  "source": { "lat": 38.8812, "lon": -77.091, "name": "HQ" },
  "destinations": [
    { "lat": 38.895, "lon": -77.084, "name": "Clarendon" },
    { "lat": 38.862, "lon": -77.059, "name": "Pentagon City" }
  ]
}
```

---

## 🏗 Environment Setup

### Backend
1. Install dependencies: `pip install -r requirements.txt`
2. Start API: `uvicorn app.api.main:app --reload --port 8000`

### Frontend
1. Navigate to: `cd frontend`
2. Install: `npm install`
3. Launch Solaris HUD: `npm run dev`

---

## 📡 News Source Integration
Teammate Notes: The `alerts/active` endpoint now correctly exposes `processed_news` data. You can begin fixing the news article source logic in `app/sources/news/` immediately.
