import React from 'react';

interface SourceLink {
  source_name: string;
  description: string;
  link: string;
}

interface SourceLinksProps {
  links: SourceLink[];
}

export const SourceLinks: React.FC<SourceLinksProps> = ({ links }) => {
  if (!links || links.length === 0) return null;

  return (
    <div style={{ marginTop: 'auto', paddingTop: '24px' }}>
      <h3 style={{
        fontSize: '11px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: 'var(--text-secondary)',
        marginBottom: '12px',
        fontWeight: 600,
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '8px'
      }}>
        Source Evidence
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {links.map((item, i) => (
          <a 
            key={i}
            href={item.link} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              flexDirection: 'column',
              padding: '10px 12px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              textDecoration: 'none',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-cyan)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-subtle)';
              e.currentTarget.style.transform = 'none';
            }}
          >
            <span style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '2px' }}>
              {item.source_name}
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
              {item.description}
            </span>
          </a>
        ))}
      </div>
    </div>
  );
};
