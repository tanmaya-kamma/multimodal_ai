import React, { useState } from 'react';
import { GlassCard } from '../ui/GlassCard';
import { useMapStore } from '../../hooks/useMapStore';
import { useCellDetail } from '../../hooks/useCellDetail';
import { SeverityBar } from '../ui/SeverityBar';

/**
 * VLMVisionCard — Compact PIP (Picture-in-Picture) window.
 * 280px width, positioned bottom-right inside clay-wrapper.
 */
export const VLMVisionCard: React.FC = () => {
  const selectedCell = useMapStore(s => s.selectedCell);
  const { data: cellDetail, isLoading } = useCellDetail(selectedCell);

  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);

  const cardWidth = 280;

  if (!selectedCell) {
    return (
      <GlassCard
        animation="slideInUp"
        animationDelay="0.1s"
        style={{
          width: `${cardWidth}px`,
          height: '220px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-secondary)',
        }}
      >
        <div style={{ fontSize: '28px', marginBottom: '12px', opacity: 0.3 }}>📷</div>
        <p style={{ fontSize: '12px' }}>Select an H3 cell with traffic alerts</p>
        <p style={{ fontSize: '10px', marginTop: '4px', opacity: 0.6 }}>to view VLM evidence feeds.</p>
      </GlassCard>
    );
  }

  if (isLoading) {
    return (
      <GlassCard
        animation="none"
        style={{
          width: `${cardWidth}px`,
          height: '220px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-secondary)',
        }}
      >
        <div style={{
          width: '18px',
          height: '18px',
          border: '2px solid var(--border-default)',
          borderTopColor: 'var(--accent-cyan)',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginRight: '10px',
        }} />
        <span style={{ fontSize: '12px' }}>Retrieving VLM payloads...</span>
      </GlassCard>
    );
  }

  // Find all traffic signals that have an image and physical evidence
  const vlmSignals = cellDetail?.signals?.traffic?.filter((s) => s.image && s.has_visual_evidence) || [];
  const latestSignal = vlmSignals[0];
  const baselineSignal = vlmSignals.length > 1 ? vlmSignals[1] : null;

  if (!latestSignal || !latestSignal.image || !latestSignal.has_visual_evidence) {
    return (
      <GlassCard
        animation="none"
        style={{
          width: `${cardWidth}px`,
          height: '220px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--status-critical)',
          position: 'relative',
          overflow: 'hidden',
          background: 'rgba(10, 10, 12, 0.85)'
        }}
      >
        {/* CRT Scanlines background */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.02) 2px, rgba(255,255,255,0.02) 4px)',
          pointerEvents: 'none',
        }} />
        {/* Animated No-Signal sweep */}
        <div style={{
          position: 'absolute', top: 0, left: '-10%', width: '10%', height: '100%',
          background: 'linear-gradient(to right, transparent, rgba(248, 113, 113, 0.15), transparent)',
          animation: 'vlmScanline 4s linear infinite',
          pointerEvents: 'none'
        }} />
        <div style={{ fontSize: '24px', marginBottom: '12px', opacity: 0.6, zIndex: 1, filter: 'grayscale(1)' }}>📡</div>
        <p style={{ fontSize: '13px', zIndex: 1, textTransform: 'uppercase', letterSpacing: '0.15em', fontWeight: 700, textShadow: '0 0 8px rgba(248, 113, 113, 0.5)' }}>No Signal</p>
        <p style={{ fontSize: '10px', zIndex: 1, marginTop: '8px', opacity: 0.6, fontFamily: "'JetBrains Mono', monospace" }}>VLM_FEED_DISCONNECTED</p>
      </GlassCard>
    );
  }

  const baseUrl = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
  const getAbsoluteUrl = (path: string) => {
    if (path.startsWith('http')) return path;
    const cleanPath = path.replace(/^(\/|\\)?static(\/|\\)/, '');
    return `${baseUrl}/static/${cleanPath}`;
  };

  const latestUrl = getAbsoluteUrl(latestSignal.image);
  const baselineUrl = baselineSignal ? getAbsoluteUrl(baselineSignal.image!) : latestUrl;

  const handleMouseDown = () => setIsDragging(true);
  const handleMouseUp = () => setIsDragging(false);
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const bounds = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - bounds.left) / bounds.width) * 100;
    setSliderPosition(Math.max(5, Math.min(95, x)));
  };

  const labelStyle: React.CSSProperties = {
    position: 'absolute',
    top: '8px',
    background: 'rgba(12, 14, 20, 0.7)',
    backdropFilter: 'blur(4px)',
    padding: '2px 6px',
    borderRadius: '4px',
    border: '1px solid var(--border-subtle)',
    color: 'var(--text-secondary)',
    fontSize: '9px',
    fontWeight: 600,
    letterSpacing: '0.05em',
    pointerEvents: 'none'
  };

  const analysisSummary = (latestSignal as any).analysis_summary;
  const anomalies: string[] = (latestSignal as any).detected_anomalies || [];

  return (
    <GlassCard
      animation="slideInUp"
      animationDelay="0.1s"
      style={{
        width: `${cardWidth}px`,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        padding: 0,
      }}
    >
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ 
            width: 6, height: 6, borderRadius: '50%', 
            background: 'var(--status-critical)', 
            animation: 'subtlePulse 2s infinite',
            boxShadow: '0 0 6px rgba(248, 113, 113, 0.4)',
          }} />
          <span className="mono" style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.04em' }}>
            CAM {latestSignal.camera_id}
          </span>
        </div>
        <span className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
          {new Date(latestSignal.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>
      </div>

      {/* Comparison Viewer */}
      <div 
        style={{ 
          height: '160px',
          position: 'relative', 
          background: '#000', 
          overflow: 'hidden', 
          cursor: (isDragging || baselineSignal) ? 'ew-resize' : 'default' 
        }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <img src={baselineUrl} style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', opacity: 0.85 }} />
        
        <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: baselineSignal ? `${sliderPosition}%` : '100%', overflow: 'hidden' }}>
          <img src={latestUrl} style={{ position: 'absolute', left: 0, top: 0, width: `${cardWidth}px`, height: '100%', objectFit: 'cover', opacity: 0.85 }} />
        </div>
        
        {baselineSignal && (
          <div className="vlm-comparison-slider" style={{ left: `${sliderPosition}%` }} onMouseDown={handleMouseDown} />
        )}

        {baselineSignal && (
          <>
            <div style={{ ...labelStyle, left: '8px' }}>LATEST</div>
            <div style={{ ...labelStyle, right: '8px' }}>BASELINE</div>
          </>
        )}
        
        {/* Scan line */}
        <div style={{
          position: 'absolute', top: 0, left: '-10%', width: '10%', height: '100%',
          background: 'linear-gradient(to right, transparent, rgba(103, 232, 249, 0.3), transparent)',
          animation: 'vlmScanline 3s linear infinite',
          pointerEvents: 'none'
        }} />

        {/* Analysis overlay */}
        <div style={{
          position: 'absolute', bottom: '10px', left: '10px', right: '10px',
          display: 'flex', flexDirection: 'column', gap: '4px', pointerEvents: 'none'
        }}>
          <div style={{
            alignSelf: 'flex-start',
            background: 'rgba(12, 14, 20, 0.7)',
            backdropFilter: 'blur(4px)',
            padding: '3px 8px', borderRadius: '4px',
            border: '1px solid rgba(251, 191, 36, 0.3)',
            color: 'var(--status-watch)', fontSize: '10px', fontWeight: 600,
          }}>
            DETECT: {latestSignal.anomaly || latestSignal.congestion || 'ANOMALY'}
            {analysisSummary && (
              <div style={{ marginTop: '3px', fontSize: '9px', fontWeight: 400, color: 'var(--text-primary)', opacity: 0.9 }}>
                {analysisSummary}
              </div>
            )}
          </div>
          {anomalies.length > 0 && (
            <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
              {anomalies.map((anomaly, idx) => (
                <span key={idx} style={{
                  background: 'rgba(248, 113, 113, 0.15)',
                  border: '1px solid rgba(248, 113, 113, 0.3)',
                  color: 'var(--status-critical)',
                  padding: '1px 5px', borderRadius: '8px',
                  fontSize: '8px', fontWeight: 600, textTransform: 'uppercase'
                }}>
                  {anomaly}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: '10px 14px',
        borderTop: '1px solid var(--border-default)',
        display: 'flex', alignItems: 'center',
      }}>
        <span style={{ fontSize: '10px', color: 'var(--text-secondary)', marginRight: '10px', letterSpacing: '0.04em' }}>
          CONFIDENCE
        </span>
        <SeverityBar severity={latestSignal.severity} height="3px" />
      </div>
    </GlassCard>
  );
};
