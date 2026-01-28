import { useState } from 'react'
import * as api from '../services/api'
import type { StylingRules } from '../types'

export function useSlideGenerator() {
  const [file, setFile] = useState<File | null>(null)
  const [rules, setRules] = useState<StylingRules | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generatedFile, setGeneratedFile] = useState<string | null>(null)

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setRules(null)
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

  const handleGenerateDeck = async (
    contentText: string,
    images: Array<{ filename: string; data: string }>
  ) => {
    setGenerating(true)
    setError(null)
    setGeneratedFile(null)

    try {
      const data = await api.generateDeck(contentText, images)
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
    handleFileChange,
    handleUpload,
    handleGenerateDeck,
  }
}
