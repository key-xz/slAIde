import type { Layout } from '../types'

interface LayoutSelectorProps {
  layouts: Layout[]
  onLayoutSelect: (layout: Layout) => void
}

export function LayoutSelector({ layouts, onLayoutSelect }: LayoutSelectorProps) {
  return (
    <div className="layout-section">
      <h2>2. pick layout</h2>
      <div className="layout-list">
        {layouts.map((layout, idx) => (
          <div key={idx} className="layout-item">
            <button onClick={() => onLayoutSelect(layout)}>
              {layout.name} ({layout.placeholders.length} placeholders)
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
