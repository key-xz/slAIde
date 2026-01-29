import type { StylingRules, Layout } from '../types'

interface LayoutManagerProps {
  rules: StylingRules
  onDeleteLayout: (layoutName: string) => void
}

export function LayoutManager({ rules, onDeleteLayout }: LayoutManagerProps) {
  const aspectRatio = rules.slide_size.height / rules.slide_size.width

  return (
    <div className="my-8">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">layouts ({rules.layouts.length})</h3>
      </div>
      
      <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6">
        {rules.layouts.map((layout: Layout, idx: number) => (
          <div key={idx} className="group bg-white border border-gray-200 rounded-lg overflow-hidden hover:border-blue-400 transition-all shadow-sm">
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <span className="text-[10px] font-mono text-gray-500 uppercase truncate pr-4" title={layout.name}>
                {layout.name}
              </span>
              <button 
                onClick={() => onDeleteLayout(layout.name)}
                className="text-gray-400 hover:text-red-600 transition-colors p-1"
                title="remove layout"
              >
                ✕
              </button>
            </div>
            
            <div className="p-4">
              <div 
                className="relative w-full bg-gray-50 border border-gray-100 rounded overflow-hidden mb-3"
                style={{ paddingBottom: `${aspectRatio * 100}%` }}
              >
                <div className="absolute top-0 left-0 w-full h-full">
                  {layout.shapes?.map((shape: any, sIdx: number) => {
                    const slideWidth = rules.slide_size.width
                    const slideHeight = rules.slide_size.height
                    
                    return (
                      <div
                        key={`static-${sIdx}`}
                        className="absolute border border-gray-200 bg-gray-100/20"
                        style={{
                          left: `${(shape.position.left / slideWidth) * 100}%`,
                          top: `${(shape.position.top / slideHeight) * 100}%`,
                          width: `${(shape.position.width / slideWidth) * 100}%`,
                          height: `${(shape.position.height / slideHeight) * 100}%`,
                        }}
                      />
                    )
                  })}

                  {layout.placeholders.map((ph) => {
                    const slideWidth = rules.slide_size.width
                    const slideHeight = rules.slide_size.height
                    
                    return (
                      <div
                        key={ph.idx}
                        className={`absolute border flex items-center justify-center text-[6px] font-bold rounded-sm group/ph ${
                          ph.type === 'text' ? 'border-blue-200 bg-blue-50/30 text-blue-300' : 'border-amber-200 bg-amber-50/30 text-amber-300'
                        }`}
                        style={{
                          left: `${(ph.position.left / slideWidth) * 100}%`,
                          top: `${(ph.position.top / slideHeight) * 100}%`,
                          width: `${(ph.position.width / slideWidth) * 100}%`,
                          height: `${(ph.position.height / slideHeight) * 100}%`,
                        }}
                      >
                        {ph.type === 'text' ? 'T' : 'IMG'}
                        
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover/ph:block bg-gray-800 text-white text-[8px] px-1.5 py-0.5 rounded whitespace-nowrap z-10">
                          x: {Math.round(ph.position.left / 914400 * 100) / 100}", 
                          y: {Math.round(ph.position.top / 914400 * 100) / 100}" 
                          ({Math.round(ph.position.width / 914400 * 100) / 100}" x {Math.round(ph.position.height / 914400 * 100) / 100}")
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="flex flex-wrap gap-1">
                {layout.placeholders.map((ph) => (
                  <span key={ph.idx} className="px-1 py-0.5 bg-gray-50 text-gray-400 rounded-[2px] text-[8px] font-medium uppercase tracking-tighter border border-gray-100">
                    {ph.type}
                  </span>
                ))}
                {layout.placeholders.length === 0 && (
                  <span className="text-[8px] text-gray-300 italic uppercase tracking-tighter">no placeholders</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
