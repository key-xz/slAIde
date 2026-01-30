import type { Layout, StylingRules } from '../types'

interface LayoutPreviewSelectorProps {
  currentLayoutName: string
  layouts: Layout[]
  rules: StylingRules
  onSelect: (layoutName: string) => void
  onClose: () => void
}

export function LayoutPreviewSelector({
  currentLayoutName,
  layouts,
  rules,
  onSelect,
  onClose,
}: LayoutPreviewSelectorProps) {
  const layoutsByCategory: Record<string, Layout[]> = {}
  
  layouts.forEach(layout => {
    const cat = layout.category || 'uncategorized'
    if (!layoutsByCategory[cat]) {
      layoutsByCategory[cat] = []
    }
    layoutsByCategory[cat].push(layout)
  })

  const categories = Object.keys(layoutsByCategory).sort()

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

  const aspectRatio = rules.slide_size.height / rules.slide_size.width

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" 
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold">select layout</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {categories.map(category => (
            <div key={category} className="mb-8 last:mb-0">
              <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
                {category}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {layoutsByCategory[category].map(layout => {
                  const isCurrent = layout.name === currentLayoutName
                  
                  return (
                    <button
                      key={layout.name}
                      onClick={() => {
                        onSelect(layout.name)
                        onClose()
                      }}
                      className={`
                        relative group cursor-pointer transition-all
                        ${isCurrent 
                          ? 'ring-2 ring-blue-500 shadow-lg' 
                          : 'hover:ring-2 hover:ring-blue-300 hover:shadow-md'
                        }
                        rounded-lg overflow-hidden bg-white border border-gray-200
                      `}
                    >
                      <div className="p-3">
                        <div 
                          className="relative w-full bg-gray-50 rounded border border-gray-200 overflow-hidden"
                          style={{ paddingBottom: `${aspectRatio * 100}%` }}
                        >
                          <div className="absolute inset-0">
                            {layout.placeholders.map(placeholder => {
                              const style = getPlaceholderStyle(placeholder)
                              
                              return (
                                <div
                                  key={placeholder.idx}
                                  className={`
                                    border border-dashed
                                    ${placeholder.type === 'text' 
                                      ? 'border-blue-300 bg-blue-50/30' 
                                      : 'border-purple-300 bg-purple-50/30'
                                    }
                                  `}
                                  style={style}
                                >
                                  <div className="w-full h-full flex items-center justify-center text-[8px] text-gray-400">
                                    {placeholder.type === 'text' ? 'T' : 'I'}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                        
                        <div className="mt-2 text-xs font-medium text-gray-700 truncate text-left">
                          {layout.name}
                        </div>
                        <div className="text-[10px] text-gray-500 text-left">
                          {layout.placeholders.filter(p => p.type === 'text').length} text, {' '}
                          {layout.placeholders.filter(p => p.type === 'image').length} image
                        </div>
                      </div>

                      {isCurrent && (
                        <div className="absolute top-2 right-2 bg-blue-500 text-white text-[10px] px-2 py-1 rounded-full font-medium">
                          current
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
