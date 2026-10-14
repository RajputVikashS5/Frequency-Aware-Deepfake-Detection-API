import type { AnalysisMode } from '@/types/analysis';

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  demoMode: (import.meta.env.VITE_DEMO_MODE ?? 'true') === 'true',
  endpoints: {
    analyze: '/api/analyze',
    health: '/api/health',
  },
  maxImageSizeBytes: 10 * 1024 * 1024,
  acceptedImageTypes: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'],
  acceptedImageExtensions: ['.jpg', '.jpeg', '.png', '.webp'],
  requestTimeoutMs: 60_000,
  historyStorageKey: 'truthlens_history',
  themeStorageKey: 'truthlens_theme',
  defaultMode: 'text_image' as AnalysisMode,
  paginationPageSize: 8,
};

export type AppConfig = typeof config;
