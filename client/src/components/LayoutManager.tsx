import type { StylingRules, Layout } from '../types'
import { LayoutCategoryManager } from './LayoutCategoryManager'

interface LayoutManagerProps {
  rules: StylingRules
  onDeleteLayout: (layoutName: string) => void
  onCategoryChange: (layoutName: string, categoryId: string) => void
  onAddCustomCategory: (categoryName: string) => void
}

export function LayoutManager({ rules, onDeleteLayout, onCategoryChange, onAddCustomCategory }: LayoutManagerProps) {
  const aspectRatio = rules.slide_size.height / rules.slide_size.width
  const availableCategories = rules.layoutCategories || []

  const categoryCounts = rules.layouts.reduce((acc, layout) => {
    const cat = layout.category || 'uncategorized'
    acc[cat] = (acc[cat] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="my-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">layouts ({rules.layouts.length})</h3>
        <div className="text-xs text-gray-500">
          {Object.entries(categoryCounts).slice(0, 3).map(([cat, count]) => (
            <span key={cat}>{count} {cat} · </span>
          ))}
          {Object.keys(categoryCounts).length > 3 && '...'}
        </div>
      </div>
      <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-gray-700">
        <strong>AI-categorized:</strong> layouts are semantically categorized by AI into groups like title slides, 
        dividers, content slides, etc. You can manually adjust categories or add custom ones.
      </div>
      
      <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-6">
        {rules.layouts.map((layout: Layout, idx: number) => {
          const categoryInfo = availableCategories.find(c => c.id === layout.category)
          
          return (
            <div key={idx} className="group bg-white border-2 border-gray-200 rounded-lg overflow-hidden transition-all shadow-sm hover:border-blue-400">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1 min-w-0 pr-2">
                    <div className="text-[10px] font-mono text-gray-500 uppercase truncate mb-1" title={layout.name}>
                      {layout.name}
                    </div>
                    {categoryInfo && (
                      <div className="text-[9px] text-blue-600 font-medium">
                        {categoryInfo.name}
                      </div>
                    )}
                  </div>
                  <button 
                    onClick={() => onDeleteLayout(layout.name)}
                    className="text-gray-400 hover:text-red-600 transition-colors p-1 flex-shrink-0"
                    title="remove layout"
                  >
                    ✕
                  </button>
                </div>
                
                <LayoutCategoryManager
                  layout={layout}
                  availableCategories={availableCategories}
                  onCategoryChange={onCategoryChange}
                  onAddCustomCategory={onAddCustomCategory}
                />
              </div>
            
            <div className="p-4">
              <div 
                className="relative w-full bg-gray-50 border border-gray-100 rounded overflow-hidden mb-3"
                style={{ paddingBottom: `${aspectRatio * 100}%` }}
              >
                <div className="absolute top-0 left-0 w-full h-full">
                  {(layout.shapes || []).map((shape: any, sIdx: number) => {
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
          )
        })}
      </div>
    </div>
  )
}
