import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div style={{
      display: 'flex',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      background: '#0a0a0a'
    }}>
      {/* 35% fixed left sidebar representing components */}
      <div style={{
        width: '35%',
        minWidth: '320px',
        maxWidth: '450px',
        height: '100%',
        flexShrink: 0,
        zIndex: 10,
        boxShadow: '4px 0 24px rgba(0,0,0,0.6)',
      }}>
        <Sidebar />
      </div>
      
      {/* 65% dynamic main area for Hero */}
      <main style={{
        flex: 1,
        height: '100%',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px',
        background: 'radial-gradient(circle at center, #1a1a24 0%, #0a0a0a 100%)'
      }}>
        <div style={{
          textAlign: 'center',
          maxWidth: '800px',
          animation: 'fade-in 1s ease-out'
        }}>
          <h1 style={{
            fontSize: '4rem',
            fontWeight: 800,
            letterSpacing: '-0.02em',
            margin: '0 0 24px 0',
            color: 'var(--text-primary)',
            lineHeight: 1.1
          }}>
            Multimodal Supply Chain <br/>
            <span style={{ 
              background: 'linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>Disruption Engine</span>
          </h1>
          
          <p style={{
            fontSize: '1.25rem',
            color: 'var(--text-secondary)',
            marginBottom: '48px',
            lineHeight: 1.6
          }}>
            Real-time geospatial intelligence fused with news, weather, and traffic data. 
            Anticipate infrastructure breakdown up to 24 hours in advance.
          </p>

          <button
            onClick={() => navigate('/map')}
            style={{
              padding: '16px 48px',
              fontSize: '1.1rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              background: 'transparent',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.4)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)';
            }}
          >
            Sign In / Enter Dashboard
          </button>
        </div>
        
        {/* Decorative Grid Background Elements */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
          pointerEvents: 'none',
          zIndex: -1
        }} />
      </main>
    </div>
  );
};
