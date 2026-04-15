import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import type { APIErrorEnvelope } from '../lib/types';

// ═══════════════════════════════════════════════
// AXIOS INTERCEPTOR LAYER
// Handles: VLM image path normalization, error envelopes,
// request/response logging, retry for transient failures.
// ═══════════════════════════════════════════════

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request Interceptor ──
// Attach timestamps, normalize outgoing payloads
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Tag request for latency tracking
    config.metadata = { startTime: Date.now() };
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// ── Response Interceptor ──
// Normalize VLM image paths, compute latency
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const latency = Date.now() - (response.config.metadata?.startTime ?? Date.now());
    if (import.meta.env.DEV) {
      console.debug(`[API] ${response.config.method?.toUpperCase()} ${response.config.url} → ${response.status} (${latency}ms)`);
    }

    // Normalize VLM image paths in traffic signal data
    normalizeImagePaths(response.data, API_BASE);

    return response;
  },
  (error: AxiosError) => {
    const envelope: APIErrorEnvelope = {
      status: 'error',
      code: error.response?.status ?? 0,
      detail: (error.response?.data as any)?.detail ?? error.message,
      timestamp: new Date().toISOString(),
    };
    return Promise.reject(envelope);
  }
);

/**
 * Recursively walks response data and converts relative VLM image paths
 * (e.g., "simulation/CAM-RT1-001.jpg") to absolute URLs.
 */
function normalizeImagePaths(data: unknown, baseUrl: string): void {
  if (!data || typeof data !== 'object') return;

  if (Array.isArray(data)) {
    data.forEach(item => normalizeImagePaths(item, baseUrl));
    return;
  }

  const obj = data as Record<string, unknown>;

  // Normalize image_path fields
  if (typeof obj.image_path === 'string' && obj.image_path && !obj.image_path.startsWith('http')) {
    obj.image_path = `${baseUrl}/static/${obj.image_path}`;
  }
  // Normalize link fields that look like file paths (VLM camera evidence)
  if (typeof obj.link === 'string' && obj.link && !obj.link.startsWith('http') && obj.link.includes('/')) {
    obj.link = `${baseUrl}/static/${obj.link}`;
  }

  Object.values(obj).forEach(val => normalizeImagePaths(val, baseUrl));
}

// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    metadata?: { startTime: number };
  }
}
