import { config, API_ENDPOINTS } from '../config'
import type { StylingRules, PlaceholderInput } from '../types'

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
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

export async function getRules(): Promise<StylingRules> {
  return fetchApi<StylingRules>(API_ENDPOINTS.getRules, {
    method: 'GET',
  })
}

export async function generateSlide(
  layoutName: string,
  inputs: Record<string, PlaceholderInput>
): Promise<{ success: boolean; message: string; file: string }> {
  return fetchApi(API_ENDPOINTS.generateSlide, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      layout_name: layoutName,
      inputs,
    }),
  })
}

export async function checkHealth(): Promise<{ status: string }> {
  return fetchApi(API_ENDPOINTS.health, {
    method: 'GET',
  })
}
