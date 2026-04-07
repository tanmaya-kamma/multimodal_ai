import React, { useState } from 'react';
import { Sidebar } from './Sidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div style={{
      display: 'flex',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      background: 'var(--bg-primary)',
      position: 'relative'
    }}>
      {/* 100% dynamic main area */}
      <main style={{
        flex: 1,
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0
      }}>
        {children}
      </main>

      {/* Floating Sidebar */}
      <div style={{
        position: 'absolute',
        top: 16,
        left: 16,
        bottom: 16,
        width: '350px',
        transform: isExpanded ? 'translateX(0)' : 'translateX(-370px)',
        transition: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        zIndex: 10,
        boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
        borderRadius: '12px',
        overflow: 'hidden',
        background: 'var(--bg-surface)'
      }}>
        <Sidebar />
      </div>

      {/* Toggle Button */}
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        title={isExpanded ? "Collapse Sidebar" : "Expand Intelligence Panel"}
        style={{
          position: 'absolute',
          top: 24,
          left: isExpanded ? 376 : 24,
          zIndex: 11,
          width: '40px',
          height: '40px',
          borderRadius: '8px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          backdropFilter: 'blur(8px)'
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.background = 'var(--bg-hover)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = 'var(--bg-surface)';
        }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {isExpanded ? (
            <polyline points="15 18 9 12 15 6"></polyline>
          ) : (
            <>
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </>
          )}
        </svg>
      </button>
    </div>
  );
};
