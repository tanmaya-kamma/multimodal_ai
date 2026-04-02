import React from 'react';

interface NavGroupProps {
  title: string;
  children: React.ReactNode;
}

export const NavGroup: React.FC<NavGroupProps> = ({ title, children }) => {
  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: 'var(--text-secondary)',
        marginBottom: '8px',
        paddingLeft: '14px',
        fontWeight: 600
      }}>
        {title}
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {children}
      </div>
    </div>
  );
};
