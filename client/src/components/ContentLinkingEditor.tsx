import { useState, useEffect } from 'react'
import type { TaggedImage, TextChunk } from '../types'

interface ContentLinkingEditorProps {
  images: TaggedImage[]
  onImagesChange: (images: TaggedImage[]) => void
  chunks: TextChunk[]
  onChunksChange: (chunks: TextChunk[]) => void
  rawText: string
  onRawTextChange: (text: string) => void
}

export function ContentLinkingEditor({ 
  images, 
  onImagesChange, 
  chunks, 
  onChunksChange,
  rawText,
  onRawTextChange 
}: ContentLinkingEditorProps) {
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null)

  useEffect(() => {
    if (rawText.trim() && chunks.length === 0) {
      autoDetectChunks(rawText)
    } else if (!rawText.trim()) {
      onChunksChange([])
    }
  }, [rawText])

  const autoDetectChunks = (text: string) => {
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

    onChunksChange(newChunks)
    if (newChunks.length > 0 && !selectedChunkId) {
      setSelectedChunkId(newChunks[0].id)
    }
  }

  const toggleImageLink = (imageId: string) => {
    if (!selectedChunkId) return

    onChunksChange(chunks.map(chunk => {
      if (chunk.id === selectedChunkId) {
        const isLinked = chunk.linkedImageIds.includes(imageId)
        return {
          ...chunk,
          linkedImageIds: isLinked
            ? chunk.linkedImageIds.filter(id => id !== imageId)
            : [...chunk.linkedImageIds, imageId]
        }
      }
      return chunk
    }))
  }

  const isImageLinkedToChunk = (imageId: string, chunkId: string) => {
    const chunk = chunks.find(c => c.id === chunkId)
    return chunk?.linkedImageIds.includes(imageId) || false
  }

  const isImageLinkedAnywhere = (imageId: string) => {
    return chunks.some(chunk => chunk.linkedImageIds.includes(imageId))
  }

  const splitChunk = (chunkId: string, splitIndex: number) => {
    const chunkIndex = chunks.findIndex(c => c.id === chunkId)
    if (chunkIndex === -1) return

    const chunk = chunks[chunkIndex]
    const text1 = chunk.text.substring(0, splitIndex).trim()
    const text2 = chunk.text.substring(splitIndex).trim()

    if (!text1 || !text2) return

    const newChunks = [...chunks]
    newChunks.splice(chunkIndex, 1,
      {
        id: `chunk-${Date.now()}-a`,
        text: text1,
        startIndex: chunk.startIndex,
        endIndex: chunk.startIndex + text1.length,
        linkedImageIds: [],
      },
      {
        id: `chunk-${Date.now()}-b`,
        text: text2,
        startIndex: chunk.startIndex + text1.length + 1,
        endIndex: chunk.endIndex,
        linkedImageIds: chunk.linkedImageIds,
      }
    )

    onChunksChange(newChunks)
  }

  const mergeWithNextChunk = (chunkId: string) => {
    const chunkIndex = chunks.findIndex(c => c.id === chunkId)
    if (chunkIndex === -1 || chunkIndex === chunks.length - 1) return

    const chunk = chunks[chunkIndex]
    const nextChunk = chunks[chunkIndex + 1]

    const mergedText = `${chunk.text}\n\n${nextChunk.text}`
    const mergedImageIds = Array.from(new Set([...chunk.linkedImageIds, ...nextChunk.linkedImageIds]))

    const newChunks = [...chunks]
    newChunks.splice(chunkIndex, 2, {
      id: `chunk-${Date.now()}-merged`,
      text: mergedText,
      startIndex: chunk.startIndex,
      endIndex: nextChunk.endIndex,
      linkedImageIds: mergedImageIds,
    })

    onChunksChange(newChunks)
  }

  const getChunkImageCount = (chunkId: string) => {
    const chunk = chunks.find(c => c.id === chunkId)
    return chunk?.linkedImageIds.length || 0
  }

  const selectedChunk = chunks.find(c => c.id === selectedChunkId)

  return (
    <div className="flex flex-col gap-4">
      {chunks.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h4 className="text-sm font-semibold mb-3 text-gray-700">content chunks</h4>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {chunks.map((chunk, idx) => {
                const isSelected = chunk.id === selectedChunkId
                const imageCount = chunk.linkedImageIds.length

                return (
                  <div
                    key={chunk.id}
                    className={`p-3 rounded border-2 cursor-pointer transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300 bg-white'
                    }`}
                    onClick={() => setSelectedChunkId(chunk.id)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs font-bold text-gray-400 uppercase">
                        chunk {idx + 1}
                      </span>
                      <div className="flex gap-1">
                        {imageCount > 0 && (
                          <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-medium">
                            🖼️ {imageCount}
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-3">
                      {chunk.text}
                    </p>
                    {isSelected && (
                      <div className="mt-3 pt-3 border-t border-gray-200 flex gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            if (idx < chunks.length - 1) {
                              mergeWithNextChunk(chunk.id)
                            }
                          }}
                          disabled={idx === chunks.length - 1}
                          className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          merge with next
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h4 className="text-sm font-semibold mb-3 text-gray-700">
              select images for chunk {chunks.findIndex(c => c.id === selectedChunkId) + 1}
              {selectedChunk && (
                <span className="text-xs font-normal text-gray-500 ml-2">
                  (click images to link/unlink)
                </span>
              )}
            </h4>

            {!selectedChunkId && (
              <p className="text-sm text-gray-500 italic">
                ← select a chunk on the left first
              </p>
            )}

            {images.length === 0 ? (
              <p className="text-sm text-gray-500 italic">
                no images uploaded yet. add images in step 2 above.
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-3 max-h-[600px] overflow-y-auto">
                {images.map((img) => {
                  const isLinkedToSelected = selectedChunkId ? isImageLinkedToChunk(img.id, selectedChunkId) : false
                  const isLinkedElsewhere = !isLinkedToSelected && isImageLinkedAnywhere(img.id)

                  return (
                    <div
                      key={img.id}
                      className={`relative rounded-lg overflow-hidden border-2 cursor-pointer transition-all ${
                        isLinkedToSelected
                          ? 'border-green-500 ring-2 ring-green-200'
                          : isLinkedElsewhere
                          ? 'border-gray-300 opacity-60'
                          : 'border-gray-200 hover:border-blue-400'
                      } ${!selectedChunkId ? 'cursor-not-allowed opacity-50' : ''}`}
                      onClick={() => selectedChunkId && toggleImageLink(img.id)}
                    >
                      <div className="aspect-square bg-gray-50">
                        <img
                          src={img.preview}
                          alt={img.filename}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-2 bg-white">
                        <p className="text-xs text-gray-600 truncate" title={img.filename}>
                          {img.filename}
                        </p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {img.tags.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                        {isLinkedToSelected && (
                          <div className="mt-1">
                            <span className="text-[10px] font-bold text-green-600 uppercase">
                              ✓ linked
                            </span>
                          </div>
                        )}
                        {isLinkedElsewhere && (
                          <div className="mt-1">
                            <span className="text-[10px] text-gray-500">
                              linked elsewhere
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

