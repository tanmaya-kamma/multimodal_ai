"""
map_viewer.py — Debug viewer for Arlington, VA base layer.
Location: app/api/map_viewer.py
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

viewer_router = APIRouter()


@viewer_router.get("/viewer", response_class=HTMLResponse)
async def map_viewer():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arlington, VA — Supply Chain Base Layer</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0a; }
            #map { width: 100vw; height: 100vh; }

            #loader {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(10,10,10,0.92); z-index: 9999;
                display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                color: #e0e0e0;
            }
            #loader h2 { font-size: 1.4rem; margin-bottom: 16px; }
            #loader .status { font-size: 0.9rem; color: #888; margin-top: 8px; }
            .spinner {
                width: 40px; height: 40px;
                border: 3px solid #333; border-top-color: #4fc3f7;
                border-radius: 50%; animation: spin 0.8s linear infinite;
            }
            @keyframes spin { to { transform: rotate(360deg); } }

            #panel {
                position: fixed; top: 12px; right: 12px; z-index: 1000;
                background: rgba(20, 20, 20, 0.9); border: 1px solid #333;
                border-radius: 10px; padding: 14px 18px;
                color: #ddd; font-size: 0.85rem;
                backdrop-filter: blur(8px); min-width: 220px;
            }
            #panel h3 {
                margin: 0 0 10px 0; font-size: 0.95rem;
                color: #4fc3f7; border-bottom: 1px solid #333;
                padding-bottom: 6px;
            }
            #panel label {
                display: flex; align-items: center; gap: 8px;
                padding: 4px 0; cursor: pointer;
            }
            #panel label:hover { color: #fff; }
            .legend-color {
                width: 14px; height: 4px; border-radius: 2px; display: inline-block;
            }
            .layer-status {
                font-size: 0.7rem; margin-left: auto; color: #666;
            }
            .layer-status.ok { color: #4caf50; }
            .layer-status.err { color: #ef5350; }
        </style>
    </head>
    <body>
        <div id="loader">
            <div class="spinner"></div>
            <h2>Loading Arlington, VA Base Layer</h2>
            <div class="status" id="load-status">Connecting to API...</div>
        </div>

        <div id="panel">
            <h3>Supply Chain — Arlington, VA</h3>
            <label>
                <input type="checkbox" id="tog-boundary" checked>
                <span class="legend-color" style="background:#4fc3f7"></span>
                County Boundary
                <span class="layer-status" id="stat-boundary">...</span>
            </label>
            <label>
                <input type="checkbox" id="tog-major" checked>
                <span class="legend-color" style="background:#ff9800"></span>
                Major Roads (freight)
                <span class="layer-status" id="stat-major">...</span>
            </label>
            <label>
                <input type="checkbox" id="tog-secondary" checked>
                <span class="legend-color" style="background:#a5d6a7"></span>
                Primary/Secondary
                <span class="layer-status" id="stat-secondary">...</span>
            </label>
            <label>
                <input type="checkbox" id="tog-railways" checked>
                <span class="legend-color" style="background:#ab47bc"></span>
                Freight Railways
                <span class="layer-status" id="stat-railways">...</span>
            </label>
        </div>

        <div id="map"></div>

        <script>
        const map = L.map('map', {
            center: [38.8816, -77.0910],
            zoom: 13,
            zoomControl: true,
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OSM &copy; CARTO',
            maxZoom: 19
        }).addTo(map);

        const API = '';

        const layers = {
            boundary: L.layerGroup().addTo(map),
            major: L.layerGroup().addTo(map),
            secondary: L.layerGroup().addTo(map),
            railways: L.layerGroup().addTo(map),
        };

        function setStatus(msg) {
            document.getElementById('load-status').textContent = msg;
        }

        function setLayerStatus(id, text, isError) {
            const el = document.getElementById('stat-' + id);
            el.textContent = text;
            el.className = 'layer-status ' + (isError ? 'err' : 'ok');
        }

        const roadColors = {
            motorway: '#ff9800', motorway_link: '#ff9800',
            trunk: '#ffc107', trunk_link: '#ffc107',
            primary: '#a5d6a7', secondary: '#81c784',
        };

        // ── Layer loaders ──

        async function loadBoundary() {
            try {
                const res = await fetch(API + '/arlington/boundary');
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                const rings = data.outer_rings || [];
                rings.forEach(ring => {
                    L.polyline(ring.map(p => [p.lat, p.lon]), {
                        color: '#4fc3f7', weight: 2.5, opacity: 0.8, dashArray: '8,6'
                    }).addTo(layers.boundary);
                });
                setLayerStatus('boundary', rings.length + ' rings', false);
            } catch (e) {
                console.error('Boundary:', e);
                setLayerStatus('boundary', 'failed', true);
            }
        }

        async function loadMajorRoads() {
            try {
                const res = await fetch(API + '/arlington/roads/major');
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                const roads = data.roads || [];
                roads.forEach(road => {
                    const coords = road.coordinates.map(p => [p.lat, p.lon]);
                    const color = roadColors[road.highway_type] || '#aaa';
                    const w = road.highway_type.startsWith('motorway') ? 2.5 : 2;
                    const line = L.polyline(coords, { color, weight: w, opacity: 0.7 }).addTo(layers.major);
                    const label = road.ref ? road.ref + ' — ' + road.name : road.name;
                    if (label !== 'Unnamed') line.bindPopup('<b>' + label + '</b><br>' + road.highway_type);
                });
                setLayerStatus('major', roads.length + ' roads', false);
            } catch (e) {
                console.error('Major roads:', e);
                setLayerStatus('major', 'failed', true);
            }
        }

        async function loadSecondaryRoads() {
            try {
                const res = await fetch(API + '/arlington/roads/secondary');
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                const roads = data.roads || [];
                roads.forEach(road => {
                    const coords = road.coordinates.map(p => [p.lat, p.lon]);
                    const color = roadColors[road.highway_type] || '#a5d6a7';
                    const line = L.polyline(coords, { color, weight: 1.2, opacity: 0.5 }).addTo(layers.secondary);
                    if (road.name !== 'Unnamed') line.bindPopup('<b>' + road.name + '</b><br>' + road.highway_type);
                });
                setLayerStatus('secondary', roads.length + ' roads', false);
            } catch (e) {
                console.error('Secondary roads:', e);
                setLayerStatus('secondary', 'failed', true);
            }
        }

        async function loadRailways() {
            try {
                const res = await fetch(API + '/arlington/railways');
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                const rws = data.railways || [];
                rws.forEach(rw => {
                    const coords = rw.coordinates.map(p => [p.lat, p.lon]);
                    const line = L.polyline(coords, {
                        color: '#ab47bc', weight: 1.5, opacity: 0.5, dashArray: '4,4'
                    }).addTo(layers.railways);
                    const parts = [rw.name, rw.operator].filter(x => x && x !== 'Unnamed');
                    const usage = rw.usage || rw.service || '';
                    if (parts.length) line.bindPopup('<b>' + parts.join(' — ') + '</b><br>Usage: ' + usage);
                });
                setLayerStatus('railways', rws.length + ' lines', false);
            } catch (e) {
                console.error('Railways:', e);
                setLayerStatus('railways', 'failed', true);
            }
        }

        // ── Layer toggles ──
        ['boundary','major','secondary','railways'].forEach(name => {
            document.getElementById('tog-' + name).onchange = function() {
                this.checked ? map.addLayer(layers[name]) : map.removeLayer(layers[name]);
            };
        });

        // ── Init ──
        async function init() {
            setStatus('Loading layers from server...');

            await loadBoundary();
            await loadMajorRoads();
            await loadSecondaryRoads();
            await loadRailways();

            setStatus('All layers loaded!');
            setTimeout(() => {
                document.getElementById('loader').style.display = 'none';
            }, 500);
        }

        init();
        </script>
    </body>
    </html>
    """