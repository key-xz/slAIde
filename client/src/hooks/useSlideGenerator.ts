import { useState, useEffect } from 'react'
import * as api from '../services/api'
import * as templateApi from '../services/templates'
import type { StylingRules, SlideSpec, TaggedImage, Template } from '../types'
import { useAuth } from '../contexts/AuthContext'

export function useSlideGenerator() {
  const { user } = useAuth()
  const [file, setFile] = useState<File | null>(null)
  const [rules, setRules] = useState<StylingRules | null>(null)
  const [currentTemplateId, setCurrentTemplateId] = useState<string | null>(null)
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generatedFile, setGeneratedFile] = useState<string | null>(null)
  const [slides, setSlides] = useState<SlideSpec[]>([])
  const [previewLoading, setPreviewLoading] = useState(false)
  const [contentStructure, setContentStructure] = useState<any>(null)
  const [preprocessing, setPreprocessing] = useState(false)
  const [imageStore, setImageStore] = useState<TaggedImage[]>([])
  const [regeneratingSlideId, setRegeneratingSlideId] = useState<string | null>(null)

  // load user's templates when authenticated
  useEffect(() => {
    if (user) {
      loadTemplates()
    } else {
      setTemplates([])
      setRules(null)
      setCurrentTemplateId(null)
    }
  }, [user])

  const loadTemplates = async () => {
    try {
      const userTemplates = await templateApi.getUserTemplates()
      setTemplates(userTemplates)
      
      // auto-load the most recently used template
      if (userTemplates.length > 0 && !rules) {
        const mostRecent = userTemplates[0]
        await loadTemplate(mostRecent.id)
      }
    } catch (err) {
      console.error('failed to load templates:', err)
    }
  }

  const loadTemplate = async (templateId: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const stylingRules = await templateApi.getTemplate(templateId)
      if (stylingRules) {
        setRules(stylingRules)
        setCurrentTemplateId(templateId)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to load template')
    } finally {
      setLoading(false)
    }
  }

  const saveCurrentTemplate = async (name: string, description?: string) => {
    if (!rules) {
      throw new Error('no rules to save')
    }

    try {
      const { template } = await templateApi.saveTemplate(name, rules, description)
      setCurrentTemplateId(template.id)
      await loadTemplates() // refresh template list
      return template
    } catch (err) {
      throw err
    }
  }

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setRules(null)
      setGeneratedFile(null)
      setSlides([])
    }
  }

  const handleUpload = async (templateName?: string) => {
    if (!file) {
      setError('please select a file first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await api.extractRules(file)
      setRules(data)
      
      // auto-save if user is authenticated
      if (user) {
        const name = templateName || file.name.replace('.pptx', '')
        const { template } = await templateApi.saveTemplate(name, data)
        setCurrentTemplateId(template.id)
        await loadTemplates()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'an error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handlePreprocessContent = async (content: any) => {
    setPreprocessing(true)
    setError(null)
    setImageStore(content.images)

    try {
      // if ai has already generated structure (intelligent chunking), use it directly
      if (content.aiGeneratedStructure) {
        setContentStructure(content.aiGeneratedStructure)
      } else {
        // traditional flow: preprocess manual chunks
        const data = await api.preprocessContentWithLinks(
          content.chunks,
          content.images,
          rules?.layouts || []
        )
        setContentStructure(data.structure)
      }
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
      const data = await api.generateSlidePreview(contentText, images)
      
      setImageStore(images.map((img, idx) => ({
        id: `img-${Date.now()}-${idx}`,
        filename: img.filename,
        data: img.data,
        preview: img.data,
        tags: []
      })))
      
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

  const handleDeleteLayout = async (layoutName: string) => {
    if (!rules) return

    // optimistically update UI
    const updatedRules = {
      ...rules,
      layouts: rules.layouts.filter((l) => l.name !== layoutName),
    }
    setRules(updatedRules)

    // if we have a saved template, delete from database
    if (currentTemplateId && user) {
      try {
        await templateApi.deleteLayout(currentTemplateId, layoutName)
        await loadTemplates()
      } catch (err) {
        // rollback on error
        setRules(rules)
        setError(err instanceof Error ? err.message : 'failed to delete layout')
      }
    }
  }

  const handleDeleteTemplate = async (templateId: string) => {
    try {
      await templateApi.deleteTemplate(templateId)
      
      // if deleting current template, clear state
      if (templateId === currentTemplateId) {
        setRules(null)
        setCurrentTemplateId(null)
      }
      
      await loadTemplates()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to delete template')
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
    templates,
    currentTemplateId,
    handleFileChange,
    handleUpload,
    handlePreprocessContent,
    handleGenerateFromStructure,
    handleGeneratePreview,
    handleGenerateDeck,
    handleDeleteLayout,
    handleDeleteTemplate,
    handleRegenerateSlide,
    loadTemplate,
    loadTemplates,
    saveCurrentTemplate,
    setSlides,
    setRules,
    setContentStructure,
  }
}
