import { useState } from 'react'
import type { Layout, LayoutCategory } from '../types'

interface LayoutCategoryManagerProps {
  layout: Layout
  availableCategories: LayoutCategory[]
  onCategoryChange: (layoutName: string, categoryId: string) => void
  onAddCustomCategory: (categoryName: string) => void
}

export function LayoutCategoryManager({ 
  layout, 
  availableCategories, 
  onCategoryChange,
  onAddCustomCategory 
}: LayoutCategoryManagerProps) {
  const [showCustomInput, setShowCustomInput] = useState(false)
  const [customCategory, setCustomCategory] = useState('')

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (e.target.value === 'custom') {
      setShowCustomInput(true)
    } else {
      onCategoryChange(layout.name, e.target.value)
    }
  }

  const handleCustomSubmit = () => {
    if (customCategory.trim()) {
      onAddCustomCategory(customCategory.trim())
      onCategoryChange(layout.name, customCategory.trim())
      setCustomCategory('')
      setShowCustomInput(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <select
          value={layout.category || ''}
          onChange={handleCategoryChange}
          className="px-2 py-1 text-xs border rounded"
        >
          <option value="">uncategorized</option>
          
          <optgroup label="Standard Categories">
            {availableCategories
              .filter(c => c.isPredefined)
              .map(cat => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))
            }
          </optgroup>
          
          {availableCategories.some(c => !c.isPredefined) && (
            <optgroup label="Custom Categories">
              {availableCategories
                .filter(c => !c.isPredefined)
                .map(cat => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))
              }
            </optgroup>
          )}
          
          <option value="custom">+ add custom category</option>
        </select>
        
        {layout.categoryConfidence !== undefined && layout.categoryConfidence !== null && (
          <span className="text-[10px] text-gray-500">
            {(layout.categoryConfidence * 100).toFixed(0)}% confident
          </span>
        )}
      </div>
      
      {showCustomInput && (
        <div className="flex gap-1">
          <input
            type="text"
            value={customCategory}
            onChange={(e) => setCustomCategory(e.target.value)}
            placeholder="category name..."
            className="flex-1 px-2 py-1 text-xs border rounded"
            autoFocus
          />
          <button onClick={handleCustomSubmit} className="px-2 py-1 text-xs bg-blue-600 text-white rounded">
            add
          </button>
          <button onClick={() => setShowCustomInput(false)} className="px-2 py-1 text-xs border rounded">
            cancel
          </button>
        </div>
      )}
      
      {layout.categoryRationale && (
        <div className="text-[10px] text-gray-600 italic">
          {layout.categoryRationale}
        </div>
      )}
    </div>
  )
}
