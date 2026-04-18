import React from 'react';
import { getTierColor } from '../../lib/severity';

interface StatusBadgeProps {
  tier: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ tier, size = 'sm' }) => {
  const color = getTierColor(tier, '#67e8f9');
  
  const sizeStyles = {
    sm: { padding: '2px 7px', fontSize: '9px' },
    md: { padding: '3px 8px', fontSize: '10px' },
    lg: { padding: '5px 12px', fontSize: '12px' },
  };

  return (
    <span style={{
      ...sizeStyles[size],
      display: 'inline-flex',
      alignItems: 'center',
      border: `1px solid ${color}30`,
      backgroundColor: `${color}12`,
      color: color,
      borderRadius: '6px',
      fontWeight: 600,
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
      lineHeight: 1,
    }}>
      {tier}
    </span>
  );
};
