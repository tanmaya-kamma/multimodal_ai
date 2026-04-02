// Map backend tiers/severities to frontend styling tokens

export function getTierColor(tier: string, defaultColor = '#ffffff'): string {
  switch (tier.toUpperCase()) {
    case 'CRITICAL':
      return '#f44336';
    case 'WARNING':
      return '#ff9800';
    case 'WATCH':
      return '#ffeb3b';
    case 'NONE':
    default:
      return defaultColor;
  }
}

export function getSeverityFillOpacity(severity: number): number {
  if (severity >= 0.7) return 0.8;
  if (severity >= 0.45) return 0.55;
  if (severity >= 0.25) return 0.3;
  return 0.15;
}

export function getSeverityFillColor(severity: number): string {
  if (severity >= 0.7) return '#f44336';
  if (severity >= 0.45) return '#ff9800';
  if (severity >= 0.25) return '#ffeb3b';
  return '#ffeb3b'; // Base watch color format
}
