import { useState } from 'react'
import * as api from '../services/api'
import type { StylingRules, SlideSpec, ContentWithLinks, TaggedImage, TextChunk } from '../types'

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
  const [contentWithLinks, setContentWithLinks] = useState<ContentWithLinks | null>(null)
  const [imageStore, setImageStore] = useState<TaggedImage[]>([])
  const [regeneratingSlideId, setRegeneratingSlideId] = useState<string | null>(null)

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

  const handlePreprocessContent = async (content: ContentWithLinks) => {
    setPreprocessing(true)
    setError(null)
    setContentWithLinks(content)
    setImageStore(content.images)

    try {
      const data = await api.preprocessContentWithLinks(
        content.chunks,
        content.images,
        rules?.layouts || []
      )
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
      const data = await api.generateSlidePreviewWithLinks(contentStructure, imageStore, rules?.layouts || [])
      
      const slidesWithData: SlideSpec[] = data.slides.map((slide: any, index: number) => ({
        id: `slide-${Date.now()}-${index}`,
        layout_name: slide.layout_name,
        placeholders: slide.placeholders.map((ph: any) => {
          if (ph.type === 'image' && ph.image_id) {
            const image = imageStore.find(img => img.id === ph.image_id)
            return {
              idx: ph.idx,
              type: ph.type,
              image_index: ph.image_index,
              imageData: image?.data,
            }
          }
          return {
            idx: ph.idx,
            type: ph.type,
            content: ph.content,
            image_index: ph.image_index,
            imageData: undefined,
          }
        }),
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

      const data = await api.generateDeckFromSlides(
        slidesForAPI, 
        imageStore, 
        rules?.customTheme
      )
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

  const handleCategoryChange = async (layoutName: string, categoryId: string) => {
    try {
      await api.updateLayoutCategory(layoutName, categoryId)
      
      if (rules) {
        setRules({
          ...rules,
          layouts: rules.layouts.map(l => 
            l.name === layoutName ? { ...l, category: categoryId, category_confidence: 1.0 } : l
          )
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to update category')
    }
  }

  const handleAddCustomCategory = async (categoryName: string) => {
    try {
      const result = await api.addCustomCategory(categoryName)
      
      if (rules && result.category) {
        setRules({
          ...rules,
          layoutCategories: [...(rules.layoutCategories || []), result.category]
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to add category')
    }
  }

  const handleRegenerateSlide = async (slideId: string) => {
    setRegeneratingSlideId(slideId)
    setError(null)

    try {
      const slide = slides.find(s => s.id === slideId)
      if (!slide || !rules) {
        throw new Error('slide or rules not found')
      }

      const slideIndex = slides.findIndex(s => s.id === slideId)
      const contextSlides = slides.filter(s => s.id !== slideId).map(s => ({
        layout_name: s.layout_name,
        placeholders: s.placeholders,
      }))

      const data = await api.regenerateSingleSlide(
        slide,
        imageStore,
        rules.layouts,
        contextSlides
      )

      const regeneratedSlide: SlideSpec = {
        ...slide,
        layout_name: data.slide.layout_name,
        placeholders: data.slide.placeholders.map((ph: any) => {
          if (ph.type === 'image' && ph.image_id) {
            const image = imageStore.find(img => img.id === ph.image_id)
            return {
              idx: ph.idx,
              type: ph.type,
              image_index: ph.image_index,
              imageData: image?.data,
            }
          }
          return {
            idx: ph.idx,
            type: ph.type,
            content: ph.content,
            image_index: ph.image_index,
            imageData: undefined,
          }
        }),
      }

      const updatedSlides = [...slides]
      updatedSlides[slideIndex] = regeneratedSlide
      setSlides(updatedSlides)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to regenerate slide')
    } finally {
      setRegeneratingSlideId(null)
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
    regeneratingSlideId,
    handleFileChange,
    handleUpload,
    handlePreprocessContent,
    handleGenerateFromStructure,
    handleGeneratePreview,
    handleGenerateDeck,
    handleDeleteLayout,
    handleCategoryChange,
    handleAddCustomCategory,
    handleRegenerateSlide,
    setSlides,
    setRules,
    setContentStructure,
  }
}
