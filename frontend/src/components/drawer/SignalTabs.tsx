import React, { useState, useEffect } from 'react';
import { WeatherSignal, TrafficSignal, NewsSignal } from '../../lib/types';
import { SeverityBar } from '../ui/SeverityBar';

interface SignalTabsProps {
  signals: {
    weather: WeatherSignal[];
    traffic: TrafficSignal[];
    news: NewsSignal[];
  };
  initialTab?: 'weather' | 'traffic' | 'news';
}

export const SignalTabs: React.FC<SignalTabsProps> = ({ signals, initialTab = 'weather' }) => {
  const [activeTab, setActiveTab] = useState<'weather' | 'traffic' | 'news'>(initialTab);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  const tabs = [
    { id: 'weather', label: `Weather (${signals.weather?.length || 0})` },
    { id: 'traffic', label: `Traffic (${signals.traffic?.length || 0})` },
    { id: 'news', label: `News (${signals.news?.length || 0})` },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Tab Headers */}
      <div style={{ 
        display: 'flex', 
        borderBottom: '1px solid var(--border-subtle)',
        marginBottom: '16px'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'weather' | 'traffic' | 'news')}
            style={{
              flex: 1,
              padding: '10px 0',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid var(--accent-cyan)' : '2px solid transparent',
              color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ minHeight: '120px' }}>
        
        {/* Weather */}
        {activeTab === 'weather' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {signals.weather?.length === 0 && <p style={{fontSize: '13px', color: 'var(--text-secondary)'}}>No recent weather signals.</p>}
            {signals.weather?.map((s, i) => (
              <div key={i} style={{ background: 'var(--bg-elevated)', padding: '12px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <strong style={{ fontSize: '13px' }}>{s.alert_type || 'Forecast'}</strong>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {new Date(s.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', width: '30px' }}>Sev:</span>
                  <SeverityBar severity={s.severity} height="3px" width="100px" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Traffic */}
        {activeTab === 'traffic' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {signals.traffic?.length === 0 && <p style={{fontSize: '13px', color: 'var(--text-secondary)'}}>No recent traffic signals.</p>}
            {signals.traffic?.map((s, i) => (
              <div key={i} style={{ background: 'var(--bg-elevated)', padding: '12px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <strong style={{ fontSize: '13px' }}>Camera {s.camera_id}</strong>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {new Date(s.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: '#ffb74d', marginBottom: '8px' }}>
                  {s.anomaly || s.congestion || 'Normal conditions'}
                </div>
                {s.image && (
                  <img src={s.image} alt="Traffic feed" style={{ width: '100%', borderRadius: '4px', marginBottom: '8px', opacity: 0.8 }} />
                )}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', width: '30px' }}>Sev:</span>
                  <SeverityBar severity={s.severity} height="3px" width="100px" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* News */}
        {activeTab === 'news' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {signals.news?.length === 0 && <p style={{fontSize: '13px', color: 'var(--text-secondary)'}}>No recent news signals.</p>}
            {signals.news?.map((s, i) => (
              <div key={i} style={{ background: 'var(--bg-elevated)', padding: '12px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <strong style={{ fontSize: '13px', color: 'var(--accent-cyan)' }}>{s.source}</strong>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {new Date(s.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p style={{ fontSize: '13px', marginBottom: '8px', lineHeight: 1.4 }}>{s.title}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', width: '30px' }}>Sev:</span>
                  <SeverityBar severity={s.severity} height="3px" width="100px" />
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
};
