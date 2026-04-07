import React from 'react';
import { getSeverityFillColor } from '../../lib/severity';

interface SeverityBarProps {
  severity: number; // 0.0 to 1.0
  width?: string;
  height?: string;
}

export const SeverityBar: React.FC<SeverityBarProps> = ({ 
  severity, 
  width = '100%', 
  height = '4px' 
}) => {
  const color = getSeverityFillColor(severity);
  const percentage = Math.max(5, Math.min(100, severity * 100));

  return (
    <div style={{
      width,
      height,
      backgroundColor: 'var(--bg-elevated)',
      borderRadius: '2px',
      overflow: 'hidden',
      position: 'relative'
    }}>
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        height: '100%',
        width: `${percentage}%`,
        backgroundColor: color,
        boxShadow: `0 0 10px ${color}`,
        transition: 'width 0.5s ease-out'
      }} />
    </div>
  );
};
