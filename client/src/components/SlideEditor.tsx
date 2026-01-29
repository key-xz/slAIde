import { useState } from 'react'
import type { SlideSpec, StylingRules } from '../types'
import { SlideCard } from './SlideCard'

interface SlideEditorProps {
  slides: SlideSpec[]
  rules: StylingRules
  onSlidesUpdate: (slides: SlideSpec[]) => void
  onGenerate: (slides: SlideSpec[]) => void
  generating: boolean
}

export function SlideEditor({ slides, rules, onSlidesUpdate, onGenerate, generating }: SlideEditorProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  const handleSlideUpdate = (slideId: string, updatedSlide: SlideSpec) => {
    const updatedSlides = slides.map(s => (s.id === slideId ? updatedSlide : s))
    onSlidesUpdate(updatedSlides)
  }

  const handleSlideDelete = (slideId: string) => {
    const updatedSlides = slides.filter(s => s.id !== slideId)
    onSlidesUpdate(updatedSlides)
  }

  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex !== null && draggedIndex !== index) {
      setDragOverIndex(index)
    }
  }

  const handleDragEnd = () => {
    if (draggedIndex !== null && dragOverIndex !== null && draggedIndex !== dragOverIndex) {
      const newSlides = [...slides]
      const [removed] = newSlides.splice(draggedIndex, 1)
      newSlides.splice(dragOverIndex, 0, removed)
      onSlidesUpdate(newSlides)
    }
    setDraggedIndex(null)
    setDragOverIndex(null)
  }

  const handleDragLeave = () => {
    setDragOverIndex(null)
  }

  return (
    <div className="my-8 p-6 bg-white rounded-lg border border-gray-200">
      <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
        <h3 className="m-0 text-lg font-semibold text-gray-900">slides ({slides.length})</h3>
        <button
          onClick={() => onGenerate(slides)}
          disabled={generating || slides.length === 0}
          className="px-4 py-2 bg-green-600 text-white rounded-md cursor-pointer font-medium transition-all hover:bg-green-700 disabled:bg-gray-300 text-sm"
        >
          {generating ? 'generating...' : 'download pptx'}
        </button>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-6">
        {slides.map((slide, index) => {
          const layout = rules.layouts.find(l => l.name === slide.layout_name)
          return (
            <div
              key={slide.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              onDragLeave={handleDragLeave}
              className={`transition-all ${dragOverIndex === index ? 'scale-95 opacity-50' : ''}`}
            >
              <SlideCard
                slide={slide}
                slideNumber={index + 1}
                layout={layout}
                rules={rules}
                onUpdate={handleSlideUpdate}
                onDelete={handleSlideDelete}
                isDragging={draggedIndex === index}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
