import React from 'react';
import { Alert } from '../../lib/types';
import { StatusBadge } from '../ui/StatusBadge';
import { SeverityBar } from '../ui/SeverityBar';
import { useMapStore } from '../../hooks/useMapStore';

interface AlertCardProps {
  alert: Alert;
}

const tierBorderClass: Record<string, string> = {
  CRITICAL: 'alert-card-critical',
  WARNING: 'alert-card-warning',
  WATCH: 'alert-card-watch',
};

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
      className={tierBorderClass[alert.alert_tier] || ''}
      onClick={handleClick}
      style={{
        padding: '14px 16px',
        borderRadius: '12px',
        cursor: alert.h3_cell ? 'pointer' : 'default',
        backgroundColor: isSelected ? 'rgba(103, 232, 249, 0.06)' : 'rgba(255, 255, 255, 0.02)',
        border: isSelected ? '1px solid rgba(103, 232, 249, 0.2)' : '1px solid transparent',
        transition: 'all 0.2s ease',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
      }}
      onMouseLeave={(e) => {
        if (!isSelected) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
        <StatusBadge tier={alert.alert_tier} />
        <span className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
          {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      
      <p style={{ 
        fontSize: '13px', 
        fontWeight: 500, 
        color: 'var(--text-primary)',
        marginBottom: '4px',
        lineHeight: 1.4
      }}>
        {alert.location}
      </p>
      
      <p style={{ 
        fontSize: '11px', 
        color: 'var(--text-secondary)',
        marginBottom: '10px',
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
        lineHeight: 1.4,
      }}>
        {alert.explanation}
      </p>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span className="mono" style={{ fontSize: '10px', color: 'var(--text-secondary)', width: '30px' }}>
          {alert.severity.toFixed(2)}
        </span>
        <SeverityBar severity={alert.severity} height="3px" />
      </div>
    </div>
  );
};
