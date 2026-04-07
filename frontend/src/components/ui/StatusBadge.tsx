import React from 'react';
import { getTierColor } from '../../lib/severity';

interface StatusBadgeProps {
  tier: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ tier, size = 'sm' }) => {
  const color = getTierColor(tier, '#4fc3f7'); // Default cyan for 'NONE' or info
  
  const sizeStyles = {
    sm: { padding: '2px 6px', fontSize: '10px' },
    md: { padding: '4px 8px', fontSize: '12px' },
    lg: { padding: '6px 12px', fontSize: '14px' },
  };

  return (
    <span style={{
      ...sizeStyles[size],
      display: 'inline-flex',
      alignItems: 'center',
      border: `1px solid ${color}40`, // 25% opacity border
      backgroundColor: `${color}15`, // ~8% opacity bg
      color: color,
      borderRadius: '4px',
      fontWeight: 600,
      letterSpacing: '0.05em',
      textTransform: 'uppercase',
      lineHeight: 1,
    }}>
      {tier}
    </span>
  );
};
