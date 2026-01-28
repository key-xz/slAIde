import type { StylingRules } from '../types'
import { getPlaceholderTypeLabel } from '../utils/placeholderHelpers'

interface RulesViewerProps {
  rules: StylingRules
}

export function RulesViewer({ rules }: RulesViewerProps) {
  return (
    <details className="rules-viewer">
      <summary>view rules</summary>
      <div>
        <h3>dimensions:</h3>
        <p>Width: {rules.slide_size.width}, Height: {rules.slide_size.height}</p>
        
        <h3>available layouts ({rules.layouts.length})</h3>
        {rules.layouts.map((layout, idx) => (
          <div key={idx}>
            <h4>{layout.name}</h4>
            <ul>
              {layout.placeholders.map((ph) => (
                <li key={ph.idx}>
                  {ph.name} - {getPlaceholderTypeLabel(ph.type)}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </details>
  )
}
