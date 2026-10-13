/**
 * Central application configuration for ImageForensics AI.
 */
export const appConfig = {
  appName: import.meta.env.VITE_APP_NAME || 'ImageForensics AI',
  appVersion: '1.0.0-academic',
  
  // Demo Mode flag: Defaults to true unless explicitly disabled in .env
  isDemoMode: import.meta.env.VITE_DEMO_MODE !== 'false',

  // API Base URL for future FastAPI backend integration
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',

  // Feature toggles
  enableAuth: import.meta.env.VITE_ENABLE_AUTH !== 'false',

  // File limits and validation rules
  maxFileSizeBytes: 10 * 1024 * 1024, // 10 Megabytes
  allowedMimeTypes: ['image/jpeg', 'image/png', 'image/webp'],
  allowedExtensions: ['.jpg', '.jpeg', '.png', '.webp'],

  // Local storage keys
  storageKeys: {
    history: 'imageforensics_local_history',
    sessionUser: 'imageforensics_demo_user',
  },

  // Privacy and research disclaimers
  disclaimers: {
    demoNotice: 'DEMO DATA — NOT AN ACTUAL MODEL PREDICTION',
    privacyNotice: 'Uploaded images are analyzed in-memory or locally. Raw images are not permanently stored.',
    researchNotice: 'Frequency-domain analysis provides probabilistic forensic indicators. It does not constitute legal proof of authenticity.',
  },
};
