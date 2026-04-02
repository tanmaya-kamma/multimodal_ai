import React from 'react';

export const SidebarHeader: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '20px 24px',
      borderBottom: '1px solid var(--border-subtle)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ 
          width: '28px', 
          height: '28px', 
          background: 'var(--accent-cyan)',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--bg-primary)',
          fontWeight: 'bold',
          fontSize: '18px'
        }}>
          ⬡
        </div>
        <div>
          <h1 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Multimodal AI
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Supply Chain Intelligence
          </p>
        </div>
      </div>
      
      <button style={{
        background: 'transparent',
        border: '1px solid var(--border-default)',
        color: 'var(--text-primary)',
        padding: '6px 12px',
        borderRadius: '6px',
        fontSize: '12px',
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--bg-elevated)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
      }}>
        Sign In
      </button>
    </div>
  );
};
