import React from 'react';
import { Alert } from '../../lib/types';
import { StatusBadge } from '../ui/StatusBadge';
import { SeverityBar } from '../ui/SeverityBar';
import { useMapStore } from '../../hooks/useMapStore';

interface AlertCardProps {
  alert: Alert;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const { selectedCell, selectCell } = useMapStore();
  const isSelected = selectedCell === alert.h3_cell;

  const handleClick = () => {
    if (alert.h3_cell) {
      selectCell(alert.h3_cell);
    }
  };

  return (
    <div 
      onClick={handleClick}
      style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-subtle)',
        cursor: alert.h3_cell ? 'pointer' : 'default',
        backgroundColor: isSelected ? 'var(--bg-elevated)' : 'transparent',
        transition: 'background-color 0.2s',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) e.currentTarget.style.backgroundColor = 'rgba(26, 26, 26, 0.4)';
      }}
      onMouseLeave={(e) => {
        if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <StatusBadge tier={alert.alert_tier} />
        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      
      <p style={{ 
        fontSize: '13px', 
        fontWeight: 500, 
        color: 'var(--text-primary)',
        marginBottom: '6px',
        lineHeight: 1.4
      }}>
        {alert.location}
      </p>
      
      <p style={{ 
        fontSize: '12px', 
        color: 'var(--text-secondary)',
        marginBottom: '12px',
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden'
      }}>
        {alert.explanation}
      </p>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '11px', color: 'var(--text-secondary)', width: '30px' }}>
          {alert.severity.toFixed(2)}
        </span>
        <SeverityBar severity={alert.severity} height="3px" />
      </div>
    </div>
  );
};
