import { LoadingIndicator } from './LoadingIndicator'

interface SlideStructure {
  slide_number: number
  slide_type: string
  layout_name: string
  placeholders: Array<{
    idx: number
    type: 'text' | 'image'
    content?: string
    image_index?: number
    capacity_label?: string
  }>
  notes: string
}

interface StructureData {
  structure: SlideStructure[]
  deck_summary: {
    total_slides: number
    flow_description: string
    key_message: string
  }
}

interface ContentStructurePreviewProps {
  structure: StructureData
  onApprove: () => void
  onEdit: (editedStructure: StructureData) => void
  loading: boolean
}

export function ContentStructurePreview({
  structure,
  onApprove,
  onEdit,
  loading,
}: ContentStructurePreviewProps) {
  const getSlideTypeColor = (type: string) => {
    switch (type) {
      case 'title':
        return 'bg-purple-50 border-purple-200 text-purple-700'
      case 'key_message':
        return 'bg-blue-50 border-blue-200 text-blue-700'
      case 'section_divider':
        return 'bg-indigo-50 border-indigo-200 text-indigo-700'
      case 'content':
        return 'bg-gray-50 border-gray-200 text-gray-700'
      case 'conclusion':
        return 'bg-green-50 border-green-200 text-green-700'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700'
    }
  }

  if (loading) {
    return (
      <LoadingIndicator 
        stage="generating" 
        detail="Creating slide previews with your approved structure"
      />
    )
  }

  return (
    <div className="my-8 p-6 bg-white rounded-lg border border-gray-200">
      <div className="mb-6">
        <h3 className="text-xl font-semibold">outline</h3>
      </div>

      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm">
        <p className="font-semibold text-blue-900 mb-1">key message</p>
        <p className="text-blue-800 mb-3">{structure.deck_summary.key_message}</p>
        <p className="text-gray-600 italic text-xs">{structure.deck_summary.flow_description}</p>
      </div>

      <div className="space-y-4 mb-6">
        {structure.structure.map((slide) => {
          const textPlaceholders = slide.placeholders.filter((ph) => ph.type === 'text')
          const imagePlaceholders = slide.placeholders.filter((ph) => ph.type === 'image')

          return (
            <div
              key={slide.slide_number}
              className={`p-4 rounded-lg border ${getSlideTypeColor(slide.slide_type)}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-lg">#{slide.slide_number}</span>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded bg-white/50">
                    {slide.slide_type}
                  </span>
                  {imagePlaceholders.length > 0 && (
                    <span className="text-xs text-amber-700">
                      📷 {imagePlaceholders.length}
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-gray-400 font-mono uppercase">
                  {slide.layout_name}
                </span>
              </div>

              <div className="space-y-3">
                {textPlaceholders.map((ph, idx) => (
                  <div key={ph.idx} className="text-sm">
                    {ph.capacity_label && (
                      <span className="text-[9px] text-gray-400 uppercase block mb-1">
                        {ph.capacity_label}
                      </span>
                    )}
                    {idx === 0 && textPlaceholders.length > 1 ? (
                      <strong className="block text-base">{ph.content}</strong>
                    ) : (
                      <p className="whitespace-pre-wrap text-gray-700">{ph.content}</p>
                    )}
                  </div>
                ))}
                {imagePlaceholders.length > 0 && (
                  <div className="mt-2 p-2 bg-amber-50 border border-amber-100 rounded text-xs text-amber-800 italic">
                    {imagePlaceholders.map((ph) => (
                      <div key={ph.idx}>
                        [image {ph.image_index} will be placed in placeholder {ph.idx}]
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {slide.notes && (
                <div className="mt-3 pt-3 border-t border-black/5">
                  <p className="text-[11px] text-gray-500 leading-relaxed italic">
                    {slide.notes}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="flex gap-3 justify-end">
        <button
          onClick={() => onEdit(structure)}
          className="px-4 py-2 text-gray-500 text-sm font-medium hover:text-gray-800"
        >
          edit
        </button>
        <button
          onClick={onApprove}
          className="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition-colors text-sm"
        >
          generate slides
        </button>
      </div>
    </div>
  )
}
