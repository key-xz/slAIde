import { useState } from 'react'
import type { SlideSpec, Layout, StylingRules } from '../types'

interface SlideCardProps {
  slide: SlideSpec
  slideNumber: number
  layout: Layout | undefined
  rules: StylingRules
  onUpdate: (slideId: string, updatedSlide: SlideSpec) => void
  onDelete: (slideId: string) => void
  isDragging?: boolean
}

export function SlideCard({
  slide,
  slideNumber,
  layout,
  rules,
  onUpdate,
  onDelete,
  isDragging,
}: SlideCardProps) {
  const [isEditing, setIsEditing] = useState<number | null>(null)

  const handleContentUpdate = (placeholderIdx: number, newContent: string) => {
    const updatedPlaceholders = slide.placeholders.map(ph =>
      ph.idx === placeholderIdx ? { ...ph, content: newContent } : ph
    )
    onUpdate(slide.id, { ...slide, placeholders: updatedPlaceholders })
    setIsEditing(null)
  }

  const getPlaceholderStyle = (placeholder: any) => {
    const slideWidth = rules.slide_size.width
    const slideHeight = rules.slide_size.height
    const scale = 0.4 // Scale down for preview
    
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
          <span className="font-semibold text-blue-600 text-sm">Slide {slideNumber}</span>
          <button onClick={() => onDelete(slide.id)} className="bg-red-600 text-white border-none rounded w-7 h-7 flex items-center justify-center cursor-pointer text-lg leading-none transition-colors hover:bg-red-700 flex-shrink-0">
            ✕
          </button>
        </div>
        <div className="p-4">
          <p className="text-red-600 text-sm p-4 text-center">Layout "{slide.layout_name}" not found</p>
        </div>
      </div>
    )
  }

  const aspectRatio = rules.slide_size.height / rules.slide_size.width

  return (
    <div className={`bg-white border-2 border-gray-200 rounded-lg overflow-hidden transition-all cursor-move hover:border-blue-600 hover:shadow-[0_4px_12px_rgba(0,102,204,0.15)] ${isDragging ? 'opacity-40 cursor-grabbing' : ''}`}>
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
        <div className="flex gap-4 items-center flex-1">
          <span className="font-semibold text-blue-600 text-sm">Slide {slideNumber}</span>
          <span className="text-gray-500 text-xs overflow-hidden text-ellipsis whitespace-nowrap">{slide.layout_name}</span>
        </div>
        <button onClick={() => onDelete(slide.id)} className="bg-red-600 text-white border-none rounded w-7 h-7 flex items-center justify-center cursor-pointer text-lg leading-none transition-colors hover:bg-red-700 flex-shrink-0" title="Delete slide">
          ✕
        </button>
      </div>

      <div className="p-4">
        <div className="relative w-full bg-white border border-gray-200 rounded overflow-hidden shadow-[0_2px_4px_rgba(0,0,0,0.05)]" style={{ paddingBottom: `${aspectRatio * 100}%` }}>
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
                    className="border border-dashed border-gray-300 flex items-center justify-center overflow-hidden cursor-text p-2 hover:border-blue-600 hover:bg-blue-600/5"
                    style={style}
                    onClick={() => !isCurrentlyEditing && setIsEditing(placeholder.idx)}
                  >
                    {isCurrentlyEditing ? (
                      <textarea
                        className="w-full h-full border-none outline-none resize-none text-xs leading-snug p-0 bg-blue-600/10"
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
                      <div className="w-full h-full overflow-auto text-xs leading-snug text-gray-900 whitespace-pre-wrap break-words">
                        {placeholder.content || 'Click to edit'}
                      </div>
                    )}
                  </div>
                )
              }

              if (placeholder.type === 'image') {
                return (
                  <div
                    key={placeholder.idx}
                    className="border border-dashed border-gray-300 flex items-center justify-center overflow-hidden bg-gray-50"
                    style={style}
                  >
                    {placeholder.imageData ? (
                      <img src={placeholder.imageData} alt={`Image ${placeholder.image_index}`} className="w-full h-full object-contain" />
                    ) : (
                      <div className="text-gray-400 text-xs text-center">Image {placeholder.image_index}</div>
                    )}
                  </div>
                )
              }

              return null
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
