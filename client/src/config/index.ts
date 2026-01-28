export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  env: import.meta.env.MODE,
  isProd: import.meta.env.PROD,
  isDev: import.meta.env.DEV,
} as const

export const API_ENDPOINTS = {
  extractRules: '/api/extract-rules',
  getRules: '/api/rules',
  generateSlide: '/api/generate-slide',
  generateDeck: '/api/generate-deck',
  health: '/api/health',
} as const

export const APP_CONSTANTS = {
  maxFileSize: 50 * 1024 * 1024,
  acceptedFileTypes: ['.pptx'],
  acceptedImageTypes: ['image/*'],
} as const
