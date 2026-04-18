**SOLARIS**

# 🌐 Multimodal AI for Situational Awareness of Supply Chain Disruptions

**Real-time detection, scoring, and visualization of supply chain disruptions during disaster response operations — powered by attention-weighted multi-source data fusion.**

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [System Architecture](#system-architecture)
- [Data Sources](#data-sources)
- [Processing Pipeline](#processing-pipeline)
- [Fusion Engine](#fusion-engine)
- [Alert System](#alert-system)
- [Route Analysis](#route-analysis)
- [API Endpoints](#api-endpoints)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the System](#running-the-system)
- [Running a Demo Simulation](#running-a-demo-simulation)
- [Key Design Decisions](#key-design-decisions)
- [Environment Variables](#environment-variables)
- [License](#license)

---

## Overview

This system fuses multimodal data — weather APIs, traffic camera computer vision, and NLP-processed news feeds — through an attention-weighted fusion engine with **H3 hexagonal spatial indexing** to detect, score, and visualize supply chain disruptions. It provides emergency managers with actionable alerts, traceable source evidence, and AI-recommended alternate delivery routes.

The current deployment focuses on **Arlington County, Virginia** as the target area, covering 86 gas stations and 208 grocery stores across the county.

---

## Problem Statement

During a disaster, supply chains for critical resources (fuel, food) are disrupted. Emergency management operations require data from various sources to identify disruptions, but the data is disparate, hard to integrate, and difficult to interpret — impeding situational awareness.

## Solution

A visual application that ingests, processes, and fuses multimodal data to provide real-time alerts on supply chain disruptions, with traceable evidence and recommended response actions.

---

## System Architecture

The system follows a layered pipeline architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       DATA SOURCES                          │
├──────────┬──────────────┬────────────────┬──────────────────┤
│ Weather  │ Traffic Cams │   News / RSS   │  OpenStreetMap   │
│ (NWS API)│ (VDOT 511)   │ (ARLnow,       │ (Overpass API)   │
│          │              │  Google News,  │                  │
│          │              │  WTOP)         │                  │
└────┬─────┴──────┬───────┴───────┬────────┴────────┬─────────┘
     │            │               │                 │
     ▼            ▼               ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                         │
│  weather_source.py   traffic_source.py   news_source.py     │
│  (live API calls)    (image download)    (RSS parsing)      │
│  fetch_osm_data.py   fetch_poi_data.py                      │
│  (one-time static)   (one-time static)                      │
│                                                             │
│  Output: raw_weather, raw_traffic, raw_news tables          │
│          + static JSON files for OSM/POI data               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                         │
│                                                             │
│  weather_processor.py   Rule-based severity scoring         │
│  traffic_processor.py   OpenCV change detection +           │
│                         Gemini Vision API (VLM)             │
│  news_processor.py      Keyword NER + event classification  │
│  osm_processor.py       H3 spatial indexing of roads        │
│  poi_processor.py       H3 spatial indexing of POIs         │
│                                                             │
│  Common: H3 resolution 8 indexing, ISO 8601 UTC timestamps  │
│                                                             │
│  Output: processed_weather, processed_traffic,              │
│          processed_news, processed_roads,                   │
│          processed_pois, processed_railways tables          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      FUSION LAYER                           │
│                                                             │
│  fusion_engine.py    Attention-weighted multi-source fusion  │
│                      - Source reliability weights            │
│                      - Temporal decay (exponential)          │
│                      - Cross-source corroboration matrix     │
│                      - Event-type semantic matching          │
│                                                             │
│  route_analysis.py   Supply route disruption analysis        │
│                      - OSRM driving route calculation        │
│                      - H3 route-cell intersection            │
│                      - Alternate route recommendation        │
│                                                             │
│  Output: alerts table + real-time API responses             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                       │
│  main.py — CORS-enabled REST API serving all endpoints      │
│  Output: JSON responses to frontend dashboard               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 VISUALIZATION (Frontend)                     │
│  Interactive map with H3 heatmap overlay                    │
│  Alert panel with 6-field structured alerts                 │
│  Route analysis with compromised segment highlighting       │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### 1. Weather Data — National Weather Service (NWS) API
| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **URL**         | `https://api.weather.gov`                                              |
| **Cost**        | Free, no API key required                                              |
| **Endpoints**   | `/alerts/active/zone/VAZ054` (active alerts), `/gridpoints/{wfo}/{x},{y}/forecast/hourly` (hourly forecast) |
| **Coverage**    | 6 grid points spread across the county for spatial granularity         |
| **Frequency**   | Alerts: every 2 minutes — Forecast: every 30 minutes                   |
| **Data types**  | Flood warnings, severe storm warnings, tornado warnings, temperature, wind speed, precipitation probability |

### 2. Traffic Camera Data — VDOT 511 System
| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **URL**         | `https://511virginia.org`                                              |
| **Cost**        | Free, public access                                                    |
| **Cameras**     | 17 VDOT snapshot cameras across Arlington County                       |
| **Coverage**    | I-66 corridor, Fairfax Dr, Columbia Pike, Rosslyn, Pentagon City, Crystal City, Shirlington |
| **Frequency**   | Every 5 minutes                                                        |
| **Processing**  | Two-stage: OpenCV frame differencing (fast, free) → Claude Vision API (intelligent, on-demand) |
| **Data types**  | Road condition, congestion level, anomaly detection (flooding, debris, accidents) |

### 3. News Data — RSS Feeds
| Attribute          | Detail                                                              |
|--------------------|---------------------------------------------------------------------|
| **Sources**        | ARLnow (local), Google News (aggregated), WTOP (regional)          |
| **Method**         | RSS feed parsing                                                    |
| **Frequency**      | Every 15 minutes                                                    |
| **Deduplication**  | SHA256 hash of title + source prevents duplicate articles           |
| **Filtering**      | Keyword-based disaster relevance filter (30+ keywords)              |
| **Age filter**     | Only articles from last 7 days ingested                             |
| **Processing**     | Keyword NER for location extraction (40+ known Arlington locations), event type classification, severity scoring |

### 4. OpenStreetMap Data — Overpass API
| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **URL**         | `https://overpass-api.de/api/interpreter`                              |
| **Data fetched**| County boundary, major roads (motorways, trunks), primary/secondary roads, freight railways |
| **Frequency**   | One-time (stored as static JSON files)                                 |

### 5. Points of Interest (POI) — Overpass API
| Attribute       | Detail                                                                 |
|-----------------|------------------------------------------------------------------------|
| **Data fetched**| Gas stations (`amenity=fuel`), grocery stores (`shop=supermarket`, `convenience`, `greengrocer`) |
| **Coverage**    | 86 gas stations, 208 grocery stores across Arlington                   |
| **Frequency**   | One-time (stored as static JSON files)                                 |

---

## Processing Pipeline

### Spatial Normalization — H3 Hexagonal Indexing

All data sources are spatially normalized using Uber's **H3 hexagonal grid system at resolution 8** (~0.74 km² per hexagon). This enables spatial joins across different data types — a weather alert, traffic camera, and news article in the same H3 cell are recognized as corroborating signals.

| Geometry type             | H3 indexing method                             |
|---------------------------|------------------------------------------------|
| Single point (POI, camera)| `h3.latlng_to_cell(lat, lon, 8)` → one cell    |
| Polyline (road, railway)  | Index every coordinate → set of cells           |
| Zone (weather alert)      | Index at grid point locations → multiple cells   |

### Temporal Normalization

All timestamps are stored in **ISO 8601 UTC** format. The fusion engine applies exponential temporal decay with a **60-minute half-life** — a signal from 60 minutes ago receives 50% weight compared to a fresh signal.

### Weather Processing — Rule-Based Severity Scoring

NWS alert severity (Minor/Moderate/Severe/Extreme) is combined with event-type impact scores. A Flash Flood Warning scores 0.90, a Severe Thunderstorm Warning scores 0.80. Forecast data is scored based on precipitation probability, wind speed, temperature extremes, and forecast text keywords.

### Traffic Camera Processing — Hybrid CV Pipeline

**Stage 1: OpenCV Change Detection (Traditional CV)**
- Compares current frame against previous frame and day/night baseline images
- Gaussian blur + absolute differencing + thresholding
- Separate daytime and nighttime baselines prevent false positives from lighting changes
- Change score threshold of 0.35 — only significant changes proceed to Stage 2

**Stage 2: Gemini Vision API (Vision Language Model)**
- Only triggered when Stage 1 detects significant change (saves API cost)
- Sends camera image with structured prompt requesting JSON assessment
- Returns: road condition, congestion level, anomaly type, visibility, truck presence, severity, confidence
- Fallback: without API key, severity stays at 0 (no false alarms from camera noise)

### News Processing — NLP Pipeline

- **Location extraction**: Keyword matching against 40+ known Arlington locations, each mapped to lat/lon coordinates. Longest match first for specificity.
- **Event classification**: Articles categorized into: `flooding`, `road_closure`, `severe_storm`, `winter_storm`, `power_outage`, `accident`, `infrastructure`, `supply_disruption`, `emergency_alert`
- **Severity scoring**: Weighted keyword matching with top-3 diminishing weight formula
- **Confidence scoring**: Based on source reliability (ARLnow: 0.85, WTOP: 0.80, Google News: 0.70) plus location specificity bonus
- **Sentiment analysis**: Negative vs positive word counting

---

## Fusion Engine

### Attention-Weighted Multi-Source Fusion

Each signal receives a dynamic attention weight:

```
attention = source_reliability × temporal_freshness × self_confidence
```

| Component            | Formula                                  | Range       |
|----------------------|------------------------------------------|-------------|
| Source reliability   | Static weight per source type            | 0.70 - 0.90 |
| Temporal freshness   | `exp(-0.693 × age_minutes / 60)`        | 0.05 - 1.00 |
| Self confidence      | From the processor's own assessment      | 0.00 - 1.00 |

### Cross-Source Corroboration

A semantic similarity matrix checks if events from different sources match:
- "Flash Flood Warning" (weather) + "flooding" (traffic camera) → corroboration score **0.95**
- "Severe Thunderstorm Warning" (weather) + "road_closure" (news) → corroboration score **0.70**

When multiple sources corroborate, both severity and confidence are multiplied by a **corroboration bonus (up to 1.5x)**.

### Fused Severity Calculation

```
fused_severity = (Σ severity_i × attention_i) / (Σ attention_i) × corroboration_bonus
```

---

## Alert System

### Alert Tiers

| Tier         | Criteria                              | Meaning                                    |
|--------------|---------------------------------------|--------------------------------------------|
| 🔴 CRITICAL  | severity ≥ 0.70 AND 2+ sources       | Confirmed disruption, immediate action needed |
| 🟠 WARNING   | severity ≥ 0.45 AND 2+ sources       | Likely disruption, prepare response        |
| 🟡 WATCH     | severity ≥ 0.30 AND 1+ source        | Potential disruption, monitor closely      |

### Alert Output (6 fields)

Each alert provides:

1. **Location** — human-readable location (road names, area names)
2. **Explanation** — narrative combining evidence from all contributing sources
3. **Source links** — clickable reference to each data source (NWS URL, camera image path, news article URL)
4. **Severity** — fused score 0.0–1.0
5. **Confidence** — fused score 0.0–1.0
6. **Recommended actions** — event-specific steps tailored to affected POIs

---

## Route Analysis

### How It Works

1. User provides source and destination locations as text (addresses, place names, landmarks)
2. **Nominatim** geocoder converts text to lat/lon coordinates (biased to Arlington)
3. **OSRM** (Open Source Routing Machine) calculates up to 3 driving route alternatives
4. Each route is H3-indexed and checked against active disruption alerts
5. Routes are scored: compromised cells count + total severity
6. The safest alternative is recommended if the primary route is compromised

### Route Status

| Status                   | Meaning                                      |
|--------------------------|----------------------------------------------|
| `clear`                  | No compromised zones on this route           |
| `partially_compromised`  | Some sections pass through disrupted areas   |
| `severely_compromised`   | More than 50% of route cells are disrupted   |

### Alternate Route Recommendation
 clicking the alternate route suggestion button in the UI will show a safer unharmed route to deliver suplies.

---

## API Endpoints

### Base Layer (Static Data)

| Method | Endpoint                         | Description                                  |
|--------|----------------------------------|----------------------------------------------|
| GET    | `/`                              | Health check — server status + cached layers |
| GET    | `/arlington/bbox`                | Bounding box + center coordinates            |
| GET    | `/arlington/boundary`            | County boundary polyline                     |
| GET    | `/arlington/roads/major`         | Motorways and trunk roads                    |
| GET    | `/arlington/roads/secondary`     | Primary and secondary roads                  |
| GET    | `/arlington/railways`            | Freight railway lines                        |
| GET    | `/arlington/pois/gas-stations`   | Gas station locations                        |
| GET    | `/arlington/pois/grocery-stores` | Grocery store locations                      |
| GET    | `/arlington/base-layer`          | Summary of all available layers              |

### Fusion & Alerts

| Method | Endpoint                           | Description                                          |
|--------|------------------------------------|------------------------------------------------------|
| POST   | `/arlington/fusion/run`            | Trigger fresh fusion analysis                        |
| GET    | `/arlington/alerts/active`         | Get all active alerts with 6 output fields           |
| GET    | `/arlington/heatmap`               | H3 cells with severity + hexagon boundaries for map  |
| GET    | `/arlington/alerts/cell/{h3_cell}` | Drill-down: all signals + POIs + roads for one cell  |

### Route Analysis

| Method | Endpoint                       | Description                                       |
|--------|--------------------------------|---------------------------------------------------|
| POST   | `/arlington/routes/analyze`    | Analyze supply routes for disruptions + suggest alternates |

**Route analysis request body:**
```json
{
    "source": {"name": "Ballston"},
    "destinations": [
        {"name": "Pentagon City"},
        {"name": "Harris Teeter Crystal City"},
        {"name": "1550 Crystal Drive"}
    ]
}
```

---

## Technology Stack

| Component            | Technology                     | Purpose                                |
|----------------------|--------------------------------|----------------------------------------|
| Backend framework    | FastAPI (Python)               | REST API server                        |
| Database             | SQLite                         | Raw + processed signal storage         |
| Spatial indexing      | H3 (Uber)                     | Hexagonal grid for spatial fusion      |
| Map data             | OpenStreetMap / Overpass API   | Road network, boundary, POI data       |
| Weather data         | NWS API (api.weather.gov)      | Official weather alerts + forecasts    |
| Traffic cameras      | VDOT 511 system                | Road condition imagery                 |
| News ingestion       | RSS (feedparser)               | Local news article collection          |
| Computer vision      | OpenCV + Gemini Vision API     | Traffic image analysis                 |
| Geocoding            | Nominatim (OSM)                | Text-to-coordinates conversion         |
| Routing              | OSRM                           | Driving route calculation              |
| Scheduling           | Python threading               | Periodic data collection               |

---

## Database Schema

### Raw Tables (unprocessed ingested data)

| Table          | Key fields                                              |
|----------------|---------------------------------------------------------|
| `raw_weather`  | lat, lon, response_json, fetched_at                     |
| `raw_traffic`  | camera_id, image_path, lat, lon, fetched_at             |
| `raw_news`     | source_name, title, content, url, published_at, fetched_at |

### Processed Tables (H3 indexed + analyzed)

| Table                | Common fields                          | Source-specific fields                                   |
|----------------------|----------------------------------------|----------------------------------------------------------|
| `processed_weather`  | h3_cell, timestamp_utc, severity, confidence | alert_type, temperature, wind_speed, precipitation_mm |
| `processed_traffic`  | h3_cell, timestamp_utc, severity, confidence | camera_id, congestion_level, anomaly_type, image_path |
| `processed_news`     | h3_cell, timestamp_utc, severity, confidence | source_name, title, extracted_location, event_type, sentiment, urgency |
| `processed_pois`     | h3_cell                                | poi_type, name, address, lat, lon                        |
| `processed_roads`    | h3_cell                                | osm_id, road_name, highway_type, ref                     |
| `processed_railways` | h3_cell                                | osm_id, railway_name, usage, operator                    |

### Fusion Output

| Table    | Key fields                                                                                              |
|----------|---------------------------------------------------------------------------------------------------------|
| `alerts` | h3_cell, timestamp_utc, alert_tier, combined_severity, source_count, sources, affected_pois, affected_roads, description |

---

## Project Structure

```
app/
├── data/
│   ├── static/                    # OSM + POI JSON files
│   ├── camera_images/             # Traffic camera snapshots
│   │   ├── latest/
│   │   ├── previous/
│   │   ├── baseline_day/
│   │   └── baseline_night/
│   └── supply_chain.db            # SQLite database
│
├── db/
│   └── setup_db.py                # Database schema creation
│
├── sources/
│   ├── osm/
│   │   ├── fetch_osm_data.py      # One-time OSM data download
│   │   └── osm_processor.py       # H3 index roads + railways
│   ├── poi/
│   │   ├── fetch_poi_data.py      # One-time POI download
│   │   └── poi_processor.py       # H3 index gas stations + stores
│   ├── weather/
│   │   ├── weather_source.py      # NWS API ingestion
│   │   ├── weather_processor.py   # Severity scoring
│   │   └── weather_scheduler.py   # Runs every 2-30 min
│   ├── traffic/
│   │   ├── traffic_source.py      # VDOT camera image download
│   │   ├── traffic_processor.py   # OpenCV + Claude Vision
│   │   └── traffic_scheduler.py   # Runs every 5 min
│   └── news/
│       ├── news_source.py         # RSS feed ingestion
│       ├── news_processor.py      # NLP location + event extraction
│       └── news_scheduler.py      # Runs every 15 min
│
├── fusion/
│   ├── fusion_engine.py           # Attention-weighted fusion
│   └── route_analysis.py          # Supply route disruption check
│
├── simulation/
│   └── simulate_disaster.py       # Demo scenario injection
│
└── api/
    ├── main.py                    # FastAPI server
    └── map_viewer.py              # Debug map viewer
```

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- pip

### Initial Setup (one-time)

```bash
# 1. Install dependencies
install all libraries in requirements.txt

# 2. Initialize the database
python app/db/setup_db.py

# 3. Fetch static data (OSM roads, boundaries, POIs)
python app/sources/osm/fetch_osm_data.py
python app/sources/poi/fetch_poi_data.py

# 4. Process static data into H3 indexes
python app/sources/osm/osm_processor.py
python app/sources/poi/poi_processor.py
```

---

## Running the System

The system requires **4 terminals** for full operation:

```bash
# Terminal 1: API server
cd app/api && python main.py

# Terminal 2: Weather data (alerts every 2min, forecast every 30min)
cd app/sources/weather && python weather_scheduler.py

# Terminal 3: Traffic cameras (every 5min)
cd app/sources/traffic && python traffic_scheduler.py

# Terminal 4: News articles (every 15min)
cd app/sources/news && python news_scheduler.py
```

The FastAPI server will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger documentation.

---

## Running a Demo Simulation

To inject sample disaster scenarios for demonstration purposes:

```bash
python app/simulation/simulate_disaster.py
python app/fusion/fusion_engine.py
```

This populates the database with simulated signals and runs the fusion engine to generate alerts.

---

## Key Design Decisions

| Decision                           | Rationale                                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------------|
| H3 over PostGIS                    | H3 converts spatial queries to simple text matching. No database extensions needed.        |
| SQLite over PostgreSQL             | Zero setup, single-file database, portable for hackathon.                                  |
| Rule-based weather scoring         | Fast, free, predictable. No API cost per weather check.                                    |
| Hybrid CV (OpenCV + VLM)           | OpenCV handles 90% of frames at zero cost. VLM only called for anomalies.                  |
| Separate ingestion + processing    | Processors can be swapped without touching data collection. Each source is independently testable. |
| Attention-weighted fusion          | Dynamic weighting captures signal quality differences that simple averaging misses.        |
| OSRM for routing                   | Free, no API key, follows real road network (not straight lines).                          |
| Nominatim for geocoding            | Free, OSM-based, consistent with our map data source.                                      |

---

## Environment Variables

| Variable              | Required | Description                                   |
|-----------------------|----------|-----------------------------------------------|
| `GEMINI_API_KEY`   | Optional | Enables Gemini Vision API for traffic analysis. Without it, the system falls back to OpenCV-only mode (no false alarms, but reduced anomaly detection). |

---

## License

This project was developed for disaster response research and emergency management operations.
