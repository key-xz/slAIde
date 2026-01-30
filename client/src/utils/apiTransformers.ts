/**
 * API response transformation utilities
 */

import type { SlideSpec, SlideContent, GenerateResponse } from '../types'
import { generateSlideId } from './idGenerator'

/**
 * transform API slide response to SlideSpec format
 */
export function transformApiSlideToSlideSpec(
  apiSlide: GenerateResponse['slides'][0],
  images?: Record<string, string>
): SlideSpec {
  const placeholders: SlideContent[] = apiSlide.placeholders.map((ph) => {
    const placeholder: SlideContent = {
      idx: ph.idx,
      type: ph.type,
    }
    
    if (ph.type === 'text' && ph.content !== undefined) {
      placeholder.content = ph.content
    }
    
    if (ph.type === 'image' && ph.image_index !== undefined) {
      placeholder.image_index = ph.image_index
      
      // include image data if available
      if (images) {
        const imageKey = `image_${ph.image_index}`
        if (images[imageKey]) {
          placeholder.imageData = images[imageKey]
        }
      }
    }
    
    return placeholder
  })
  
  return {
    id: generateSlideId(),
    layout_name: apiSlide.layout_name,
    placeholders,
  }
}

/**
 * transform full API response to SlideSpec array
 */
export function transformApiResponseToSlides(response: GenerateResponse): SlideSpec[] {
  return response.slides.map((slide) =>
    transformApiSlideToSlideSpec(slide, response.images)
  )
}

/**
 * extract image data from API response
 */
export function extractImageDataFromResponse(
  response: GenerateResponse
): Record<string, string> {
  return response.images || {}
}
