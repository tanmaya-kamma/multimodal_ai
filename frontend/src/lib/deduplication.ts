import type { Alert } from './types';

/** 
 * Deduplicates alerts using ContentHash digest when available,
 * falling back to a deterministic fingerprint of cell + tier + explanation.
 */
export function deduplicateAlerts(alerts: Alert[]): Alert[] {
  const seen = new Map<string, Alert>();
  
  for (const alert of alerts) {
    const key = getAlertFingerprint(alert);
    const existing = seen.get(key);
    
    // Keep the more recent alert
    if (!existing || new Date(alert.timestamp) > new Date(existing.timestamp)) {
      seen.set(key, alert);
    }
  }
  
  return Array.from(seen.values()).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

function getAlertFingerprint(alert: Alert): string {
  // If the alert carries a SHA-256 content hash, use it directly
  // (this comes from VLMEvidence.content_hash in the fused packet)
  if ((alert as any).content_hash?.digest) {
    return (alert as any).content_hash.digest;
  }
  
  // Deterministic fingerprint: cell + tier + first 80 chars of explanation
  return `${alert.h3_cell}::${alert.alert_tier}::${alert.explanation.substring(0, 80)}`;
}
