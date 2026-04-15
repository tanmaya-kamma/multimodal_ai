import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useAlerts } from '../hooks/useAlerts';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const mapContainer = useRef<HTMLDivElement>(null);
  const [time, setTime] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  
  const { data: alertsData, isFetching } = useAlerts();

  // Clock
  useEffect(() => {
    const updateTime = () => setTime(new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    updateTime();
    const int = setInterval(updateTime, 1000);
    return () => clearInterval(int);
  }, []);

  // Background Map
  useEffect(() => {
    if (!mapContainer.current) return;
    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [-77.102, 38.880],
      zoom: 12.5,
      pitch: 45,
      interactive: false,
      attributionControl: false
    });
    return () => m.remove();
  }, []);

  const handleInitiate = () => {
    setIsScanning(true);
    setTimeout(() => {
      navigate('/command-center');
    }, 1500); // 1.5s matching scanning animation
  };

  const recentAlerts = alertsData?.alerts?.slice(0, 5) || [];

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      width: '100vw', height: '100vh', overflow: 'hidden', background: '#0a0a0a',
      position: 'relative', color: 'var(--text-primary)'
    }}>
      {/* Background Map */}
      <div 
        ref={mapContainer}
        style={{
          position: 'absolute', top: '-10%', left: '-10%', width: '120%', height: '120%', 
          filter: 'brightness(0.2) blur(10px)', zIndex: 0 
        }}
      />

      {/* Decorative Grid */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1,
        backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px)',
        backgroundSize: '40px 40px', pointerEvents: 'none'
      }} />

      {/* Corner Telemetry (Pointer-events none on wrapper) */}
      <div style={{ position: 'absolute', top: 32, left: 32, zIndex: 10, pointerEvents: 'none' }}>
        <div style={{ pointerEvents: 'auto', display: 'flex', flexDirection: 'column', gap: '4px', fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: 'var(--text-secondary)' }}>
          <div style={{ color: 'var(--text-primary)', fontWeight: 600, letterSpacing: '0.1em' }}>LOCAL TIME</div>
          <div style={{ color: 'var(--accent-cyan)' }}>{time}</div>
          <div style={{ marginTop: '8px' }}>ARLINGTON_VA // [38.880° N, 77.102° W]</div>
        </div>
      </div>

      <div style={{ position: 'absolute', top: 32, right: 32, zIndex: 10, pointerEvents: 'none', textAlign: 'right' }}>
        <div style={{ pointerEvents: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600, letterSpacing: '0.1em' }}>SAT LINK</span>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--status-optimal)', boxShadow: '0 0 8px var(--status-optimal)' }} />
          </div>
          <div style={{ color: 'var(--status-optimal)' }}>STR: 98.4% [SECURE]</div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600, letterSpacing: '0.1em' }}>API PULSE</span>
            <div style={{ 
              width: '6px', height: '6px', borderRadius: '50%', 
              background: isFetching ? 'var(--status-neutral)' : 'rgba(255,255,255,0.2)',
              boxShadow: isFetching ? '0 0 10px var(--status-neutral)' : 'none',
              transition: 'all 0.2s'
            }} />
          </div>
          <div>{isFetching ? 'SYNCING...' : 'IDLE'}</div>
        </div>
      </div>

      <div style={{ position: 'absolute', bottom: 32, left: 32, zIndex: 10, pointerEvents: 'none' }}>
        <div style={{ 
          pointerEvents: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', 
          background: 'rgba(10,10,12,0.85)', padding: '16px', borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.05)', position: 'relative', overflow: 'hidden'
        }}>
          {/* VLM Scanline background */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
            background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.02) 2px, rgba(255,255,255,0.02) 4px)',
            pointerEvents: 'none',
          }} />
          <div style={{
            position: 'absolute', top: 0, left: '-10%', width: '10%', height: '100%',
            background: 'linear-gradient(to right, transparent, rgba(56, 189, 248, 0.15), transparent)',
            animation: 'vlmScanline 4s linear infinite',
            pointerEvents: 'none'
          }} />
          
          <div style={{ fontSize: '18px', filter: 'grayscale(1)', zIndex: 1, opacity: 0.8 }}>👁️</div>
          <div style={{ zIndex: 1, fontFamily: "'JetBrains Mono', monospace", fontSize: '10px' }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>VLM READINESS</span>
            <br/><span style={{ color: 'var(--status-neutral)', filter: 'drop-shadow(0 0 4px var(--status-neutral))' }}>AWAITING SENSOR MESH</span>
          </div>
        </div>
      </div>

      <div style={{ position: 'absolute', bottom: 32, right: 32, zIndex: 10, pointerEvents: 'none', textAlign: 'right', width: '300px' }}>
        <div style={{ pointerEvents: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', fontFamily: "'JetBrains Mono', monospace", fontSize: '10px' }}>
          <div style={{ color: 'var(--text-primary)', fontWeight: 600, letterSpacing: '0.1em', paddingBottom: '4px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            RECENT DETECTIONS
          </div>
          {recentAlerts.length === 0 ? (
            <div style={{ color: 'var(--text-secondary)' }}>NO ACTIVE ALERTS</div>
          ) : (
            recentAlerts.map(a => (
              <div key={a.h3_cell} style={{ color: 'var(--text-secondary)', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '200px' }}>{a.location.toUpperCase()}</span>
                <span style={{ color: a.alert_tier === 'CRITICAL' ? 'var(--status-critical)' : 'var(--status-warning)' }}>[{a.alert_tier}]</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Central Hub */}
      <main style={{
        position: 'relative', zIndex: 20, width: '100%', maxWidth: '800px',
        padding: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center',
        background: 'rgba(20, 24, 33, 0.75)', backdropFilter: 'blur(30px)',
        borderRadius: '40px', border: '1px solid rgba(255,255,255,0.05)',
        boxShadow: 'inset 4px 4px 8px rgba(255,255,255,0.05), inset -4px -4px 8px rgba(0,0,0,0.3)'
      }}>
        <h1 style={{
          fontSize: '3.5rem', fontWeight: 800, letterSpacing: '-0.02em', margin: '0 0 16px 0',
          color: 'var(--text-primary)', lineHeight: 1.1, textAlign: 'center'
        }}>
          Solaris <span style={{ color: 'var(--status-neutral)', textShadow: '0 0 20px rgba(56,189,248,0.4)' }}>Command</span>
        </h1>
        <p style={{
          fontSize: '1.25rem', color: 'var(--text-secondary)', marginBottom: '56px',
          lineHeight: 1.6, textAlign: 'center', maxWidth: '600px'
        }}>
          Real-time geospatial intelligence fused with structural sensor data.
          Anticipate multi-vector supply chain disruption.
        </p>

        <button
          className="biometric-btn"
          onClick={handleInitiate}
          disabled={isScanning}
          style={{
            padding: '24px 64px', fontSize: '1.25rem', fontWeight: 700, letterSpacing: '0.1em',
            borderRadius: '16px', cursor: isScanning ? 'default' : 'pointer', textTransform: 'uppercase',
            position: 'relative', overflow: 'hidden'
          }}
        >
          {isScanning ? 'Syncing...' : 'Initiate Deployment'}
        </button>
      </main>

      {/* Scanning Animation Overlay */}
      {isScanning && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, height: '4px',
          background: '#fff', boxShadow: '0 0 20px #fff, 0 0 40px var(--status-neutral)',
          zIndex: 9999, animation: 'scannerDrop 1.5s cubic-bezier(0.65, 0, 0.35, 1) forwards'
        }} />
      )}
    </div>
  );
};
