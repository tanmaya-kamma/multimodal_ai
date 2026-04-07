import React from 'react';
import { useMapStore, ActiveView } from '../../hooks/useMapStore';

interface NavItemProps {
  id: ActiveView;
  label: string;
  icon: React.ReactNode;
}

export const NavItem: React.FC<NavItemProps> = ({ id, label, icon }) => {
  const { activeView, setActiveView } = useMapStore();
  const isActive = activeView === id;

  return (
    <button
      onClick={() => setActiveView(id)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        width: '100%',
        padding: '10px 14px',
        backgroundColor: isActive ? 'var(--bg-elevated)' : 'transparent',
        border: '1px solid',
        borderColor: isActive ? 'var(--border-default)' : 'transparent',
        borderRadius: '8px',
        color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        fontWeight: isActive ? 500 : 400,
        textAlign: 'left'
      }}
      onMouseEnter={(e) => {
        if (!isActive) {
          e.currentTarget.style.color = 'var(--text-primary)';
          e.currentTarget.style.backgroundColor = 'rgba(26, 26, 26, 0.4)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isActive) {
          e.currentTarget.style.color = 'var(--text-secondary)';
          e.currentTarget.style.backgroundColor = 'transparent';
        }
      }}
    >
      <span style={{ 
        display: 'flex', 
        opacity: isActive ? 1 : 0.7,
        color: isActive ? 'var(--accent-cyan)' : 'inherit'
      }}>
        {icon}
      </span>
      {label}
    </button>
  );
};
