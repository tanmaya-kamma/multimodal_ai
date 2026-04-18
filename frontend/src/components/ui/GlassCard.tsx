import React from 'react';

type GlowTier = 'critical' | 'watch' | 'optimal';

interface ClayCardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  animation?: 'clayPanelIn' | 'slideInLeft' | 'slideInUp' | 'none';
  animationDelay?: string;
  glowTier?: GlowTier;
  onClick?: () => void;
}

const glowClassMap: Record<GlowTier, string> = {
  critical: 'clay-glow-critical',
  watch: 'clay-glow-watch',
  optimal: 'clay-glow-optimal',
};

/**
 * ClayCard (formerly GlassCard)
 * 
 * Solaris Clay design system card with:
 * - Claymorphism dual inner shadows
 * - 24px border-radius
 * - Backdrop blur 20px
 * - pointer-events: auto (via .clay-card class)
 * - Optional status glow tier
 */
export const GlassCard: React.FC<ClayCardProps> = ({
  children,
  className = '',
  style = {},
  animation = 'clayPanelIn',
  animationDelay = '0s',
  glowTier,
  onClick,
}) => {
  const glowClass = glowTier ? glowClassMap[glowTier] : '';
  
  return (
    <div
      className={`clay-card ${glowClass} ${className}`}
      onClick={onClick}
      style={{
        animation: animation !== 'none'
          ? `${animation} 0.5s var(--ease-smooth) ${animationDelay} both`
          : undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
