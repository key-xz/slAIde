import { useState } from 'react'
import * as api from '../services/api'
import type { StylingRules, SlideSpec } from '../types'

export function useSlideGenerator() {
  const [file, setFile] = useState<File | null>(null)
  const [rules, setRules] = useState<StylingRules | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generatedFile, setGeneratedFile] = useState<string | null>(null)
  const [slides, setSlides] = useState<SlideSpec[]>([])
  const [previewLoading, setPreviewLoading] = useState(false)

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setRules(null)
      setGeneratedFile(null)
      setSlides([])
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await api.extractRules(file)
      setRules(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const [imageStore, setImageStore] = useState<Array<{ filename: string; data: string }>>([])

  const handleGeneratePreview = async (
    contentText: string,
    images: Array<{ filename: string; data: string }>
  ) => {
    setPreviewLoading(true)
    setError(null)

    try {
      const data = await api.generateSlidePreview(contentText, images)
      
      // Store images for later use in final generation
      setImageStore(images)
      
      // Convert API response to SlideSpec format with image data
      const slidesWithData: SlideSpec[] = data.slides.map((slide: any, index: number) => ({
        id: `slide-${Date.now()}-${index}`,
        layout_name: slide.layout_name,
        placeholders: slide.placeholders.map((ph: any) => ({
          idx: ph.idx,
          type: ph.type,
          content: ph.content,
          image_index: ph.image_index,
          imageData: ph.type === 'image' && ph.image_index !== undefined 
            ? images[ph.image_index]?.data 
            : undefined,
        })),
      }))
      
      setSlides(slidesWithData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleGenerateDeck = async (slidesToGenerate: SlideSpec[]) => {
    setGenerating(true)
    setError(null)
    setGeneratedFile(null)

    try {
      // Convert SlideSpec back to API format
      const slidesForAPI = slidesToGenerate.map(slide => ({
        layout_name: slide.layout_name,
        placeholders: slide.placeholders.map(ph => ({
          idx: ph.idx,
          type: ph.type,
          ...(ph.type === 'text' ? { content: ph.content } : { image_index: ph.image_index }),
        })),
      }))

      const data = await api.generateDeckFromSlides(slidesForAPI, imageStore)
      setGeneratedFile(data.file)
      console.log(`Generated ${data.slides_count} slides successfully`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setGenerating(false)
    }
  }

  return {
    file,
    rules,
    loading,
    error,
    generating,
    generatedFile,
    slides,
    previewLoading,
    handleFileChange,
    handleUpload,
    handleGeneratePreview,
    handleGenerateDeck,
    setSlides,
  }
}
