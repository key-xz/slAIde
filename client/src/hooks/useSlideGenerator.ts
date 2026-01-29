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
  const [contentStructure, setContentStructure] = useState<any>(null)
  const [preprocessing, setPreprocessing] = useState(false)
  const [contentText, setContentText] = useState('')
  const [imageStore, setImageStore] = useState<Array<{ filename: string; data: string }>>([])

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
      setError('please select a file first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await api.extractRules(file)
      setRules(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'an error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handlePreprocessContent = async (
    text: string, 
    images: Array<{ filename: string; data: string }>
  ) => {
    setPreprocessing(true)
    setError(null)
    setContentText(text)
    setImageStore(images)

    try {
      const data = await api.preprocessContent(text, images.length, rules?.layouts || [])
      setContentStructure(data.structure)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'an error occurred')
    } finally {
      setPreprocessing(false)
    }
  }

  const handleGenerateFromStructure = async () => {
    if (!contentStructure) {
      setError('no structure available to generate from')
      return
    }

    setPreviewLoading(true)
    setError(null)

    try {
      const data = await api.generateSlidePreview(contentStructure, imageStore, rules?.layouts || [])
      
      const slidesWithData: SlideSpec[] = data.slides.map((slide: any, index: number) => ({
        id: `slide-${Date.now()}-${index}`,
        layout_name: slide.layout_name,
        placeholders: slide.placeholders.map((ph: any) => ({
          idx: ph.idx,
          type: ph.type,
          content: ph.content,
          image_index: ph.image_index,
          imageData: ph.type === 'image' && ph.image_index !== undefined 
            ? imageStore[ph.image_index]?.data 
            : undefined,
        })),
      }))
      
      setSlides(slidesWithData)
      setContentStructure(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'an error occurred')
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleGeneratePreview = async (
    contentText: string,
    images: Array<{ filename: string; data: string }>
  ) => {
    setPreviewLoading(true)
    setError(null)

    try {
      const data = await api.generateSlidePreview(contentText, images, rules?.layouts || [])
      
      setImageStore(images)
      
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
      setError(err instanceof Error ? err.message : 'an error occurred')
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleGenerateDeck = async (slidesToGenerate: SlideSpec[]) => {
    setGenerating(true)
    setError(null)
    setGeneratedFile(null)

    try {
      const slidesForAPI = slidesToGenerate.map(slide => ({
        layout_name: slide.layout_name,
        placeholders: slide.placeholders.map(ph => ({
          idx: ph.idx,
          type: ph.type,
          ...(ph.type === 'text' ? { content: ph.content } : { image_index: ph.image_index }),
        })),
      }))

      const data = await api.generateDeckFromSlides(slidesForAPI, imageStore, rules?.layouts || [])
      setGeneratedFile(data.file)
      console.log(`generated ${data.slides_count} slides successfully`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'an error occurred')
    } finally {
      setGenerating(false)
    }
  }

  const handleDeleteLayout = (layoutName: string) => {
    if (rules) {
      setRules({
        ...rules,
        layouts: rules.layouts.filter((l) => l.name !== layoutName),
      })
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
    contentStructure,
    preprocessing,
    handleFileChange,
    handleUpload,
    handlePreprocessContent,
    handleGenerateFromStructure,
    handleGeneratePreview,
    handleGenerateDeck,
    handleDeleteLayout,
    setSlides,
    setContentStructure,
  }
}
