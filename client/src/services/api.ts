import { config, API_ENDPOINTS } from '../config'
import type { StylingRules, TaggedImage, TextChunk } from '../types'

export class ApiError extends Error {
  statusCode?: number
  data?: any
  
  constructor(
    message: string,
    statusCode?: number,
    data?: any
  ) {
    super(message)
    this.name = 'ApiError'
    this.statusCode = statusCode
    this.data = data
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${config.apiBaseUrl}${endpoint}`
  
  try {
    const response = await fetch(url, options)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.error || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      )
    }
    
    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    
    throw new ApiError(
      error instanceof Error ? error.message : 'An unexpected error occurred'
    )
  }
}

export async function extractRules(file: File): Promise<StylingRules> {
  const formData = new FormData()
  formData.append('file', file)
  
  return fetchApi<StylingRules>(API_ENDPOINTS.extractRules, {
    method: 'POST',
    body: formData,
  })
}

export async function loadTemplateFile(
  file: File,
  layouts: any[],
  slideSize: { width: number; height: number }
): Promise<{ success: boolean; message: string }> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('layouts', JSON.stringify(layouts))
  formData.append('slide_size', JSON.stringify(slideSize))

  return fetchApi<{ success: boolean; message: string }>('/api/load-template', {
    method: 'POST',
    body: formData,
  })
}

export async function getRules(): Promise<StylingRules> {
  return fetchApi<StylingRules>(API_ENDPOINTS.getRules, {
    method: 'GET',
  })
}

export async function checkHealth(): Promise<{ status: string }> {
  return fetchApi(API_ENDPOINTS.health, {
    method: 'GET',
  })
}

export async function generateDeck(
  contentText: string,
  images: Array<{ filename: string; data: string }>,
  layouts?: any[],
  slideSize?: { width: number; height: number }
): Promise<{ success: boolean; message: string; file: string; slides_count: number }> {
  return fetchApi(API_ENDPOINTS.generateDeck, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content_text: contentText,
      images,
      layouts,
      slide_size: slideSize,
    }),
  })
}

export async function preprocessContent(
  contentText: string,
  numImages: number
): Promise<{ success: boolean; structure: any }> {
  return fetchApi('/api/preprocess-content', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content_text: contentText,
      num_images: numImages,
    }),
  })
}

export async function generateSlidePreview(
  structuredContent: any,
  images: Array<{ filename: string; data: string }>
): Promise<{ slides: any[] }> {
  return fetchApi('/api/preview-slides', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      structured_content: structuredContent,
      images,
    }),
  })
}

export async function generateDeckFromSlides(
  slides: any[],
  images: Array<{ filename: string; data: string }>,
  customTheme?: any,
  layouts?: any[],
  slideSize?: { width: number; height: number }
): Promise<{ success: boolean; message: string; file: string; slides_count: number }> {
  return fetchApi(API_ENDPOINTS.generateDeck, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content_text: '',
      images,
      slides,
      customTheme,
      layouts,
      slide_size: slideSize,
    }),
  })
}

export async function intelligentChunk(
  rawText: string,
  images: TaggedImage[],
  layouts: any[],
  slideSize?: { width: number; height: number }
): Promise<{ success: boolean; structure: any; deck_summary: any }> {
  return fetchApi('/api/intelligent-chunk', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      raw_text: rawText,
      images: images.map(img => ({
        id: img.id,
        filename: img.filename,
        data: img.data,
        tags: img.tags,
        visionDescription: img.visionDescription,
        visionLabels: img.visionLabels,
      })),
      layouts,
      slide_size: slideSize,
    }),
  })
}

export async function preprocessContentWithLinks(
  chunks: TextChunk[],
  images: TaggedImage[],
  layouts: any[],
  slideSize?: { width: number; height: number }
): Promise<{ success: boolean; structure: any }> {
  return fetchApi('/api/preprocess-content', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content_chunks: chunks.map(chunk => ({
        id: chunk.id,
        text: chunk.text,
        linked_image_ids: chunk.linkedImageIds,
      })),
      images: images.map(img => ({
        id: img.id,
        filename: img.filename,
        data: img.data,
        tags: img.tags,
      })),
      layouts,
      slide_size: slideSize,
    }),
  })
}

export async function generateSlidePreviewWithLinks(
  structuredContent: any,
  images: TaggedImage[],
  layouts: any[]
): Promise<{ slides: any[] }> {
  return fetchApi('/api/preview-slides', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      structured_content: structuredContent,
      images: images.map(img => ({
        id: img.id,
        filename: img.filename,
        data: img.data,
        tags: img.tags,
      })),
      layouts,
    }),
  })
}

export async function toggleLayoutSpecial(
  layoutName: string,
  isSpecial: boolean
): Promise<{ success: boolean; message: string }> {
  return fetchApi('/api/toggle-layout-special', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      layout_name: layoutName,
      is_special: isSpecial,
    }),
  })
}

export async function regenerateSingleSlide(
  slide: any,
  images: TaggedImage[],
  layouts: any[],
  contextSlides: any[]
): Promise<{ success: boolean; slide: any }> {
  return fetchApi('/api/regenerate-slide', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      slide: {
        layout_name: slide.layout_name,
        placeholders: slide.placeholders,
      },
      images: images.map(img => ({
        id: img.id,
        filename: img.filename,
        data: img.data,
        tags: img.tags,
      })),
      layouts,
      context_slides: contextSlides,
    }),
  })
}

export async function analyzeImage(imageData: string) {
  return fetchApi('/api/analyze-image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_data: imageData })
  })
}

