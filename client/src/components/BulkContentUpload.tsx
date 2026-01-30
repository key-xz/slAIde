import { useState } from 'react'
import type { TaggedImage, ContentWithLinks, TextChunk } from '../types'
import { ContentLinkingEditor } from './ContentLinkingEditor'
import { LoadingIndicator } from './LoadingIndicator'
import * as api from '../services/api'

interface BulkContentUploadProps {
  onPreprocess: (contentWithLinks: ContentWithLinks) => void
  preprocessing: boolean
  layouts: any[]
  slideSize?: { width: number; height: number }
  aiModel?: string
  onCancelRequest?: () => void
}

const PREDEFINED_TAGS = [
  'logo',
  'graph',
  'chart',
  'profile',
  'icon',
  'screenshot',
  'diagram',
  'data',
  'brand',
]

export function BulkContentUpload({ onPreprocess, preprocessing, layouts, slideSize, aiModel, onCancelRequest }: BulkContentUploadProps) {
  const [images, setImages] = useState<TaggedImage[]>([])
  const [rawText, setRawText] = useState('')
  const [chunks, setChunks] = useState<TextChunk[]>([])
  const [useAiChunking, setUseAiChunking] = useState(true)
  const [aiChunking, setAiChunking] = useState(false)
  
  const isProcessing = preprocessing || aiChunking

  const generateUniqueId = () => `img-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

  const handleTextFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      setRawText(text)
      autoDetectChunks(text)
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  const autoDetectChunks = (text: string) => {
    if (!text.trim()) {
      setChunks([])
      return
    }

    // simple paragraph split as initial preview
    // ai will do intelligent chunking on backend considering layouts + images + text
    const paragraphs = text.split(/\n\n+/).filter(p => p.trim())
    let currentIndex = 0
    const newChunks: TextChunk[] = []

    paragraphs.forEach((paragraph, idx) => {
      const trimmed = paragraph.trim()
      const startIndex = text.indexOf(trimmed, currentIndex)
      const endIndex = startIndex + trimmed.length

      newChunks.push({
        id: `chunk-${Date.now()}-${idx}`,
        text: trimmed,
        startIndex,
        endIndex,
        linkedImageIds: [],
      })

      currentIndex = endIndex
    })

    setChunks(newChunks)
  }

  const handleAiChunking = async () => {
    if (!rawText.trim()) {
      alert('please enter some content first')
      return
    }

    setAiChunking(true)

    try {
      const controller = new AbortController()
      const result = await api.intelligentChunk(rawText, images, layouts, slideSize, aiModel || 'fast', controller.signal)
      
      // ai has already created the slide structure, pass it with deck_summary
      onPreprocess({
        chunks: [],
        images,
        aiGeneratedStructure: {
          structure: result.structure,
          deck_summary: result.deck_summary
        }
      })
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        alert('request cancelled')
      } else {
        const errorMessage = err instanceof Error ? err.message : 'unknown error'
        alert(`ai chunking failed: ${errorMessage}`)
        console.error('AI chunking error:', err)
      }
    } finally {
      setAiChunking(false)
    }
  }

  const handlePreprocess = () => {
    if (!rawText.trim()) {
      alert('please enter some content first')
      return
    }

    if (useAiChunking) {
      handleAiChunking()
      return
    }

    if (chunks.length === 0) {
      alert('no text chunks detected. make sure to separate content with blank lines.')
      return
    }

    onPreprocess({
      chunks,
      images,
    })
  }

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const newImagePromises = Array.from(files).map((file) => {
      return new Promise<TaggedImage>((resolve) => {
        const reader = new FileReader()
        reader.onloadend = () => {
          const base64 = reader.result as string
          resolve({
            id: generateUniqueId(),
            filename: file.name,
            data: base64,
            preview: base64,
            tags: [],
          })
        }
        reader.readAsDataURL(file)
      })
    })

    const newImages = await Promise.all(newImagePromises)
    setImages((prev) => [...prev, ...newImages])
    
    analyzeImagesInBackground(newImages)
    
    e.target.value = ''
  }

  const analyzeImagesInBackground = async (imagesToAnalyze: TaggedImage[]) => {
    for (const img of imagesToAnalyze) {
      try {
        const analysis = await api.analyzeImage(img.data) as {
          visionDescription?: string
          visionLabels?: string[]
          recommendedLayoutStyle?: string
        }
        
        setImages(prev => prev.map(i => 
          i.id === img.id 
            ? { 
                ...i, 
                visionDescription: analysis.visionDescription,
                visionLabels: analysis.visionLabels,
                recommendedLayoutStyle: analysis.recommendedLayoutStyle,
                analyzedAt: Date.now()
              }
            : i
        ))
      } catch (err) {
        console.error(`failed to analyze ${img.filename}:`, err)
      }
    }
  }

  const removeImage = (imageId: string) => {
    setImages((prev) => prev.filter((img) => img.id !== imageId))
  }

  const addTag = (imageId: string, tag: string) => {
    setImages((prev) =>
      prev.map((img) =>
        img.id === imageId && !img.tags.includes(tag)
          ? { ...img, tags: [...img.tags, tag] }
          : img
      )
    )
  }

  const removeTag = (imageId: string, tag: string) => {
    setImages((prev) =>
      prev.map((img) =>
        img.id === imageId
          ? { ...img, tags: img.tags.filter((t) => t !== tag) }
          : img
      )
    )
  }

  const bulkAddTag = (tag: string) => {
    setImages((prev) =>
      prev.map((img) =>
        !img.tags.includes(tag) ? { ...img, tags: [...img.tags, tag] } : img
      )
    )
  }

  return (
    <div className="flex flex-col gap-8 my-8">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">1. add content</h3>
        
        <div className="flex gap-4 mb-4 items-center">
          <input
            type="file"
            accept=".txt,.md,.doc,.docx,text/plain"
            onChange={handleTextFileUpload}
            id="text-file-upload"
            className="hidden"
          />
          <label 
            htmlFor="text-file-upload" 
            className="inline-block px-4 py-2 bg-white text-blue-600 border border-blue-600 rounded cursor-pointer font-medium transition-all hover:bg-blue-50 text-sm"
          >
            upload text file
          </label>
          {rawText && (
            <button
              onClick={() => {
                setRawText('')
                setChunks([])
              }}
              className="px-4 py-2 text-red-600 font-medium text-sm hover:underline"
              type="button"
            >
              clear
            </button>
          )}
        </div>
        
        <textarea
          value={rawText}
          onChange={(e) => {
            setRawText(e.target.value)
            autoDetectChunks(e.target.value)
          }}
          placeholder="paste your presentation content here. separate sections with blank lines (double enter) to create chunks..."
          rows={8}
          className="w-full p-4 border border-gray-200 rounded resize-y transition-colors focus:outline-none focus:border-blue-600 text-sm font-mono"
        />
        
        {chunks.length > 0 && (
          <p className="mt-2 text-xs text-gray-500">
            detected {chunks.length} chunk{chunks.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      {chunks.length > 0 && (
        <>
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">2. add image assets ({images.length})</h3>
              <div className="flex gap-2">
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImageUpload}
                  id="bulk-image-upload"
                  className="hidden"
                />
                <label 
                  htmlFor="bulk-image-upload" 
                  className="inline-block px-4 py-2 bg-white text-blue-600 border border-blue-600 rounded cursor-pointer font-medium transition-all hover:bg-blue-50 text-sm"
                >
                  add images
                </label>
              </div>
            </div>

            {images.length > 0 && (
              <>
                <div className="mb-4 p-3 bg-gray-50 rounded">
                  <p className="text-xs text-gray-600 mb-2 font-medium">quick tag all images:</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {PREDEFINED_TAGS.map((tag) => (
                      <button
                        key={tag}
                        onClick={() => bulkAddTag(tag)}
                        className="px-2 py-1 bg-white border border-gray-300 hover:border-blue-500 hover:bg-blue-50 rounded text-xs transition-colors"
                      >
                        + {tag}
                      </button>
                    ))}
                  </div>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      const input = e.currentTarget.elements.namedItem('bulkCustomTag') as HTMLInputElement
                      const customTag = input.value.trim()
                      if (customTag) {
                        bulkAddTag(customTag)
                        input.value = ''
                      }
                    }}
                    className="flex gap-2"
                  >
                    <input
                      type="text"
                      name="bulkCustomTag"
                      placeholder="custom tag for all images..."
                      className="flex-1 text-xs border border-gray-300 rounded px-2 py-1"
                    />
                    <button
                      type="submit"
                      className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 whitespace-nowrap"
                    >
                      tag all
                    </button>
                  </form>
                </div>

                <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-4">
                  {images.map((img) => (
                    <div key={img.id} className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                      <div className="relative aspect-square bg-gray-50">
                        <img src={img.preview} alt={img.filename} className="w-full h-full object-cover" />
                        <button
                          onClick={() => removeImage(img.id)}
                          className="absolute top-2 right-2 bg-black/50 text-white border-none rounded-full w-6 h-6 flex items-center justify-center cursor-pointer text-xs transition-colors hover:bg-red-600"
                          type="button"
                        >
                          ✕
                        </button>
                      </div>
                      <div className="p-3">
                        <p className="text-xs text-gray-600 truncate mb-2" title={img.filename}>
                          {img.filename}
                        </p>
                        
                        <div className="flex flex-wrap gap-1 mb-2">
                          {img.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium"
                            >
                              {tag}
                              <button
                                onClick={() => removeTag(img.id, tag)}
                                className="text-blue-700 hover:text-blue-900"
                              >
                                ✕
                              </button>
                            </span>
                          ))}
                        </div>

                        <div className="space-y-2">
                          <select
                            onChange={(e) => {
                              if (e.target.value) {
                                addTag(img.id, e.target.value)
                                e.target.value = ''
                              }
                            }}
                            className="w-full text-xs border border-gray-300 rounded px-2 py-1 bg-white"
                            defaultValue=""
                          >
                            <option value="" disabled>
                              add predefined tag...
                            </option>
                            {PREDEFINED_TAGS.filter(tag => !img.tags.includes(tag)).map((tag) => (
                              <option key={tag} value={tag}>
                                {tag}
                              </option>
                            ))}
                          </select>
                          
                          <form
                            onSubmit={(e) => {
                              e.preventDefault()
                              const input = e.currentTarget.elements.namedItem('customTag') as HTMLInputElement
                              const customTag = input.value.trim()
                              if (customTag && !img.tags.includes(customTag)) {
                                addTag(img.id, customTag)
                                input.value = ''
                              }
                            }}
                            className="flex gap-1"
                          >
                            <input
                              type="text"
                              name="customTag"
                              placeholder="custom tag..."
                              className="flex-1 text-xs border border-gray-300 rounded px-2 py-1"
                            />
                            <button
                              type="submit"
                              className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                            >
                              add
                            </button>
                          </form>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {!useAiChunking && (
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold mb-4">3. link images to content chunks</h3>
              
              <ContentLinkingEditor
                images={images}
                onImagesChange={setImages}
                chunks={chunks}
                onChunksChange={setChunks}
                rawText={rawText}
                onRawTextChange={(text) => {
                  setRawText(text)
                  autoDetectChunks(text)
                }}
              />
            </div>
          )}

          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={useAiChunking}
                  onChange={() => setUseAiChunking(true)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium">ai intelligent chunking</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={!useAiChunking}
                  onChange={() => setUseAiChunking(false)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium">manual chunk linking</span>
              </label>
            </div>

            {useAiChunking && (
              <p className="text-xs text-gray-600 max-w-2xl text-center">
                ai will analyze your text + images + layouts together to create optimized slide chunks.
                considers layout capacity, image relevance, and presentation flow.
              </p>
            )}

            {!useAiChunking && (
              <p className="text-xs text-gray-600 max-w-2xl text-center">
                manually link images to text chunks above. ai will then structure slides respecting your bindings.
              </p>
            )}
            
            <button
              onClick={handlePreprocess}
              disabled={isProcessing || !rawText.trim()}
              className="px-8 py-3 bg-blue-600 text-white rounded-md cursor-pointer font-semibold transition-all hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              generate slide structure
            </button>
            
            {!useAiChunking && (
              <p className="text-xs text-gray-500">
                {chunks.length} chunk{chunks.length !== 1 ? 's' : ''} • {images.length} image{images.length !== 1 ? 's' : ''} •{' '}
                {chunks.reduce((sum, c) => sum + c.linkedImageIds.length, 0)} link{chunks.reduce((sum, c) => sum + c.linkedImageIds.length, 0) !== 1 ? 's' : ''}
              </p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
