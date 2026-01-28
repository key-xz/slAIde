import { useState } from 'react'
import * as api from '../services/api'
import type { StylingRules, Layout, PlaceholderInput } from '../types'

export function useSlideGenerator() {
  const [file, setFile] = useState<File | null>(null)
  const [rules, setRules] = useState<StylingRules | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [selectedLayout, setSelectedLayout] = useState<Layout | null>(null)
  const [inputs, setInputs] = useState<Record<string, PlaceholderInput>>({})
  const [generating, setGenerating] = useState(false)
  const [generatedFile, setGeneratedFile] = useState<string | null>(null)

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setRules(null)
      setSelectedLayout(null)
      setInputs({})
      setGeneratedFile(null)
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

  const handleLayoutSelect = (layout: Layout) => {
    setSelectedLayout(layout)
    setInputs({})
    setGeneratedFile(null)
  }

  const handleTextInput = (idx: string, value: string) => {
    setInputs(prev => ({
      ...prev,
      [idx]: { type: 'text', value }
    }))
  }

  const handleImageInput = async (idx: string, file: File) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const base64 = reader.result as string
      setInputs(prev => ({
        ...prev,
        [idx]: { type: 'image', value: base64 }
      }))
    }
    reader.readAsDataURL(file)
  }

  const handleGenerateSlide = async () => {
    if (!selectedLayout) {
      setError('Please select a layout first')
      return
    }

    setGenerating(true)
    setError(null)

    try {
      const data = await api.generateSlide(selectedLayout.name, inputs)
      setGeneratedFile(data.file)
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
    selectedLayout,
    inputs,
    generating,
    generatedFile,
    handleFileChange,
    handleUpload,
    handleLayoutSelect,
    handleTextInput,
    handleImageInput,
    handleGenerateSlide,
  }
}
