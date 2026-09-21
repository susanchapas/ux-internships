import type { ScanConfig, StaticData } from './types';

declare global {
  interface Window {
    STATIC_DATA?: StaticData;
    STATIC_CONFIG?: ScanConfig;
    EARLY_CAREER_SOURCES?: unknown[];
  }
}

export function isStaticMode(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.STATIC_DATA !== 'undefined' &&
    window.STATIC_DATA !== null
  );
}

/**
 * Static builds use Firebase because they have no server API to call. Server
 * mode uses the Python cookie session so its authenticated CRUD endpoints and
 * the UI always agree about who is signed in. Firebase can still be selected
 * explicitly for development that does not use those endpoints.
 */
export function usesFirebaseAuth(): boolean {
  return isStaticMode() || import.meta.env.VITE_AUTH_MODE === 'firebase';
}

export function getStaticData(): StaticData | null {
  if (typeof window === 'undefined') return null;
  return window.STATIC_DATA || null;
}

export function getStaticConfig(): ScanConfig | null {
  if (typeof window === 'undefined') return null;
  return window.STATIC_CONFIG || null;
}

export function getEarlyCareerSources(): unknown[] {
  if (typeof window === 'undefined') return [];
  return window.EARLY_CAREER_SOURCES || [];
}
