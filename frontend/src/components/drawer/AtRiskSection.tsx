import React from 'react';
import { POIAtRisk, RoadAtRisk } from '../../lib/types';

interface AtRiskSectionProps {
  pois: POIAtRisk[];
  roads: RoadAtRisk[];
}

export const AtRiskSection: React.FC<AtRiskSectionProps> = ({ pois, roads }) => {
  if (!pois?.length && !roads?.length) {
    return <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>No critical assets found in this cell.</div>;
  }

  const gas = pois?.filter(p => p.type === 'gas_station') || [];
  const groceries = pois?.filter(p => ['supermarket', 'convenience', 'greengrocer'].includes(p.type)) || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {gas.length > 0 && (
        <div>
          <h4 style={{ fontSize: '12px', color: '#f44336', marginBottom: '8px', fontWeight: 600 }}>⛽ Gas Stations at Risk</h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {gas.map((p, i) => (
              <li key={i} style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                {p.name !== 'Unnamed' ? p.name : 'Unknown Station'} 
                <span style={{ color: 'var(--text-secondary)', marginLeft: '6px' }}>{p.address}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {groceries.length > 0 && (
        <div>
          <h4 style={{ fontSize: '12px', color: '#4caf50', marginBottom: '8px', fontWeight: 600 }}>🛒 Grocery Stores at Risk</h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {groceries.map((p, i) => (
              <li key={i} style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                {p.name !== 'Unnamed' ? p.name : 'Unknown Market'}
                <span style={{ color: 'var(--text-secondary)', marginLeft: '6px' }}>{p.address}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {roads.length > 0 && (
        <div>
          <h4 style={{ fontSize: '12px', color: '#ff9800', marginBottom: '8px', fontWeight: 600 }}>🛣️ Corridors Affected</h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {roads.map((r, i) => (
              <li key={i} style={{ 
                fontSize: '12px', 
                backgroundColor: 'rgba(255, 152, 0, 0.1)', 
                color: '#ffb74d',
                padding: '4px 8px',
                borderRadius: '4px',
                border: '1px solid rgba(255, 152, 0, 0.3)'
              }}>
                {r.ref ? `${r.ref} - ${r.name}` : r.name}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
