/**
 * application constants and configuration
 */

import type { AIModel } from '../types'

/**
 * AI model options
 */
export const AI_MODELS: Record<AIModel, { label: string; description: string }> = {
  fast: {
    label: 'Fast',
    description: 'quick and efficient for most tasks',
  },
  openai: {
    label: 'OpenAI',
    description: 'high quality GPT models',
  },
  kimi: {
    label: 'Kimi',
    description: 'kimi k2.5 model via openrouter',
  },
}

/**
 * default AI model
 */
export const DEFAULT_AI_MODEL: AIModel = 'fast'

/**
 * predefined content tags
 */
export const PREDEFINED_TAGS = [
  'diagram',
  'chart',
  'graph',
  'table',
  'screenshot',
  'logo',
  'photo',
  'illustration',
  'icon',
  'map',
]

/**
 * file upload constraints
 */
export const FILE_CONSTRAINTS = {
  maxImageSizeMB: 10,
  maxPptxSizeMB: 50,
  allowedImageTypes: ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'],
  allowedPptxType: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}

/**
 * default file names
 */
export const DEFAULT_FILENAMES = {
  downloadedPptx: 'generated-slide.pptx',
}

/**
 * UI configuration
 */
export const UI_CONFIG = {
  debounceDelayMs: 300,
  toastDurationMs: 3000,
  maxRecentTemplates: 10,
}

/**
 * API endpoints (relative to base URL)
 */
export const API_ENDPOINTS = {
  health: '/api/health',
  extractRules: '/api/extract-rules',
  loadTemplate: '/api/load-template',
  getRules: '/api/rules',
  generateSlides: '/api/generate',
  preprocessContent: '/api/preprocess-content',
  intelligentChunk: '/api/intelligent-chunk',
  validateContent: '/api/validate-content',
  download: '/api/download',
}
