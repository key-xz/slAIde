import { useState } from 'react'
import type { SlideSpec, Layout, StylingRules } from '../types'
import { LayoutPreviewSelector } from './LayoutPreviewSelector'

interface SlideCardProps {
  slide: SlideSpec
  slideNumber: number
  layout: Layout | undefined
  rules: StylingRules
  onUpdate: (slideId: string, updatedSlide: SlideSpec) => void
  onDelete: (slideId: string) => void
  onRegenerate?: (slideId: string) => void
  isDragging?: boolean
  regenerating?: boolean
  previewImage?: string
}

export function SlideCard({
  slide,
  slideNumber,
  layout,
  rules,
  onUpdate,
  onDelete,
  onRegenerate,
  isDragging,
  regenerating,
  previewImage,
}: SlideCardProps) {
  const [isEditing, setIsEditing] = useState<number | null>(null)
  const [showRegenerateModal, setShowRegenerateModal] = useState(false)
  const [showLayoutSelector, setShowLayoutSelector] = useState(false)

  const handleContentUpdate = (placeholderIdx: number, newContent: string) => {
    const updatedPlaceholders = slide.placeholders.map(ph =>
      ph.idx === placeholderIdx ? { ...ph, content: newContent } : ph
    )
    onUpdate(slide.id, { ...slide, placeholders: updatedPlaceholders })
    setIsEditing(null)
  }

  const handleLayoutChange = (newLayoutName: string) => {
    const newLayout = rules.layouts.find(l => l.name === newLayoutName)
    if (!newLayout) return

    const newTextPlaceholders = newLayout.placeholders.filter(p => p.type === 'text')
    const newImagePlaceholders = newLayout.placeholders.filter(p => p.type === 'image')
    const oldTextContent = slide.placeholders.filter(p => p.type === 'text')
    const oldImageContent = slide.placeholders.filter(p => p.type === 'image')

    if (newTextPlaceholders.length < oldTextContent.length || 
        newImagePlaceholders.length < oldImageContent.length) {
      if (!confirm('new layout has fewer placeholders. some content may be lost. continue?')) {
        return
      }
    }

    const newPlaceholders = newLayout.placeholders.map((ph, idx) => {
      if (ph.type === 'text') {
        const oldContent = oldTextContent[idx]?.content || ''
        return {
          idx: ph.idx,
          type: 'text' as const,
          content: oldContent,
        }
      } else {
        const oldImage = oldImageContent[idx]
        return {
          idx: ph.idx,
          type: 'image' as const,
          image_index: oldImage?.image_index,
          imageData: oldImage?.imageData,
        }
      }
    })

    onUpdate(slide.id, { ...slide, layout_name: newLayoutName, placeholders: newPlaceholders })
  }

  const getPlaceholderStyle = (placeholder: any) => {
    const slideWidth = rules.slide_size.width
    const slideHeight = rules.slide_size.height
    
    return {
      position: 'absolute' as const,
      left: `${(placeholder.position.left / slideWidth) * 100}%`,
      top: `${(placeholder.position.top / slideHeight) * 100}%`,
      width: `${(placeholder.position.width / slideWidth) * 100}%`,
      height: `${(placeholder.position.height / slideHeight) * 100}%`,
    }
  }

  if (!layout) {
    return (
      <div className={`bg-white border-2 border-gray-200 rounded-lg overflow-hidden transition-all cursor-move ${isDragging ? 'opacity-40 cursor-grabbing' : ''}`}>
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
          <span className="font-semibold text-blue-600 text-sm">slide {slideNumber}</span>
          <button onClick={() => onDelete(slide.id)} className="bg-red-600 text-white border-none rounded w-7 h-7 flex items-center justify-center cursor-pointer text-lg leading-none transition-colors hover:bg-red-700 flex-shrink-0">
            ✕
          </button>
        </div>
        <div className="p-4">
          <p className="text-red-600 text-sm p-4 text-center">layout "{slide.layout_name}" not found</p>
        </div>
      </div>
    )
  }

  const aspectRatio = rules.slide_size.height / rules.slide_size.width

  const layoutsByCategory: Record<string, typeof rules.layouts> = {}
  
  rules.layouts.forEach(layout => {
    const cat = layout.category || 'uncategorized'
    if (!layoutsByCategory[cat]) {
      layoutsByCategory[cat] = []
    }
    layoutsByCategory[cat].push(layout)
  })

  const handleRegenerateClick = () => {
    setShowRegenerateModal(true)
  }

  const confirmRegenerate = () => {
    setShowRegenerateModal(false)
    if (onRegenerate) {
      onRegenerate(slide.id)
    }
  }

  return (
    <>
      <div className={`bg-white border-2 border-gray-200 rounded-lg overflow-hidden transition-all cursor-move hover:border-blue-600 hover:shadow-[0_4px_12px_rgba(0,102,204,0.15)] ${isDragging ? 'opacity-40 cursor-grabbing' : ''} ${regenerating ? 'opacity-60' : ''}`}>
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex justify-between items-center gap-2">
          <span className="font-semibold text-blue-600 text-xs whitespace-nowrap">slide {slideNumber}</span>

          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowLayoutSelector(true)
            }}
            disabled={regenerating}
            className="flex-1 px-2 py-1 border border-gray-300 rounded text-[10px] bg-white hover:border-blue-500 hover:bg-blue-50 min-w-0 disabled:opacity-50 transition-colors text-left truncate"
            title="change layout (click for preview)"
          >
            {slide.layout_name}
          </button>

          {onRegenerate && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleRegenerateClick()
              }}
              disabled={regenerating}
              className="px-2 py-1 bg-purple-600 text-white rounded text-[10px] hover:bg-purple-700 transition-colors flex-shrink-0 disabled:opacity-50"
              title="use AI to regenerate this slide"
            >
              {regenerating ? '...' : 'AI'}
            </button>
          )}

          <button 
            onClick={() => onDelete(slide.id)} 
            className="text-gray-400 hover:text-red-600 text-sm p-1 flex-shrink-0" 
            title="delete"
          >
            ✕
          </button>
        </div>

      <div className="p-4">
        {previewImage ? (
          <div className="relative w-full rounded overflow-hidden border border-gray-200">
            <img 
              src={previewImage} 
              alt={`Slide ${slideNumber} preview`}
              className="w-full h-auto"
            />
            <div className="absolute top-2 right-2 bg-black/60 text-white text-[10px] px-2 py-1 rounded">
              rendered preview
            </div>
          </div>
        ) : (
          <div className="relative w-full bg-white border border-gray-100 rounded overflow-hidden" style={{ paddingBottom: `${aspectRatio * 100}%` }}>
            <div className="absolute top-0 left-0 w-full h-full">
              {slide.placeholders.map(placeholder => {
                const layoutPlaceholder = layout.placeholders.find(p => p.idx === placeholder.idx)
                if (!layoutPlaceholder) return null

                const style = getPlaceholderStyle(layoutPlaceholder)

                if (placeholder.type === 'text') {
                  const isCurrentlyEditing = isEditing === placeholder.idx

                  return (
                    <div
                      key={placeholder.idx}
                      className="border border-dashed border-gray-200 flex items-center justify-center overflow-hidden cursor-text p-1 hover:border-blue-400 hover:bg-blue-50/30"
                      style={style}
                      onClick={() => !isCurrentlyEditing && setIsEditing(placeholder.idx)}
                    >
                      {isCurrentlyEditing ? (
                        <textarea
                          className="w-full h-full border-none outline-none resize-none text-[10px] leading-tight p-0 bg-blue-50"
                          value={placeholder.content || ''}
                          onChange={(e) => {
                            const updatedPlaceholders = slide.placeholders.map(ph =>
                              ph.idx === placeholder.idx ? { ...ph, content: e.target.value } : ph
                            )
                            onUpdate(slide.id, { ...slide, placeholders: updatedPlaceholders })
                          }}
                          onBlur={(e) => handleContentUpdate(placeholder.idx, e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Escape') {
                              setIsEditing(null)
                            }
                          }}
                          autoFocus
                        />
                      ) : (
                        <div className="w-full h-full overflow-auto text-[10px] leading-tight text-gray-800 whitespace-pre-wrap break-words">
                          {placeholder.content || '...'}
                        </div>
                      )}
                    </div>
                  )
                }

                if (placeholder.type === 'image') {
                  return (
                    <div
                      key={placeholder.idx}
                      className="border border-dashed border-gray-200 flex items-center justify-center overflow-hidden bg-gray-50/50"
                      style={style}
                    >
                      {placeholder.imageData ? (
                        <img src={placeholder.imageData} alt="" className="w-full h-full object-contain" />
                      ) : (
                        <div className="text-gray-300 text-[8px]">img</div>
                      )}
                    </div>
                  )
                }

                return null
              })}
            </div>
          </div>
        )}
      </div>
    </div>

    {showRegenerateModal && (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowRegenerateModal(false)}>
        <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
          <h3 className="text-lg font-semibold mb-3">regenerate slide with AI?</h3>
          <p className="text-sm text-gray-600 mb-4">
            the AI will analyze this slide's content and may choose a different layout (including special layouts) 
            to better present the information. this action cannot be undone.
          </p>
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowRegenerateModal(false)}
              className="px-4 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50 transition-colors"
            >
              cancel
            </button>
            <button
              onClick={confirmRegenerate}
              className="px-4 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors"
            >
              regenerate
            </button>
          </div>
        </div>
      </div>
    )}

    {showLayoutSelector && (
      <LayoutPreviewSelector
        currentLayoutName={slide.layout_name}
        layouts={rules.layouts}
        rules={rules}
        onSelect={handleLayoutChange}
        onClose={() => setShowLayoutSelector(false)}
      />
    )}
  </>
  )
}
