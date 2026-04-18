// Map backend tiers/severities to Solaris Clay frontend tokens

export function getTierColor(tier: string, defaultColor = '#71717a'): string {
  switch (tier.toUpperCase()) {
    case 'CRITICAL':
      return '#F87171';
    case 'WARNING':
      return '#FB923C';
    case 'WATCH':
      return '#FBBF24';
    case 'NONE':
    default:
      return defaultColor;
  }
}

export function getSeverityFillOpacity(severity: number): number {
  if (severity >= 0.7) return 0.75;
  if (severity >= 0.45) return 0.5;
  if (severity >= 0.25) return 0.3;
  return 0.12;
}

export function getSeverityFillColor(severity: number): string {
  if (severity >= 0.7) return '#F87171';   // Critical
  if (severity >= 0.45) return '#FBBF24';  // Watch
  if (severity >= 0.25) return '#34D399';  // Optimal
  return '#34D399';
}
