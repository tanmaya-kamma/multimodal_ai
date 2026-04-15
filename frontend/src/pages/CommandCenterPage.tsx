import React, { useEffect } from 'react';
import { CommandCenterShell } from '../components/command-center/CommandCenterShell';
import { useMapStore } from '../hooks/useMapStore';

/**
 * CommandCenterPage — Phase 2 implementation.
 * Renders the full-bleed Command Center Shell with Bento glassmorphism overlays.
 */
export const CommandCenterPage: React.FC = () => {
  const setActiveView = useMapStore(s => s.setActiveView);

  useEffect(() => {
    setActiveView('command-center');
  }, [setActiveView]);

  return <CommandCenterShell />;
};
