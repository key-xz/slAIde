import type { StylingRules } from '../types'
import { getPlaceholderTypeLabel } from '../utils/placeholderHelpers'

interface RulesViewerProps {
  rules: StylingRules
}

export function RulesViewer({ rules }: RulesViewerProps) {
  return (
    <details className="my-8 p-4 bg-gray-50 border border-gray-200 rounded">
      <summary className="cursor-pointer font-semibold text-gray-700 hover:text-gray-900">View Rules</summary>
      <div className="mt-4">
        <h3 className="font-semibold mb-2">Dimensions:</h3>
        <p className="mb-4">Width: {rules.slide_size.width}, Height: {rules.slide_size.height}</p>
        
        <h3 className="font-semibold mb-2">Available Layouts ({rules.layouts.length})</h3>
        {rules.layouts.map((layout, idx) => (
          <div key={idx} className="mb-4 p-3 bg-white rounded border border-gray-200">
            <h4 className="font-medium text-gray-900 mb-2">{layout.name}</h4>
            <ul className="list-disc list-inside text-sm text-gray-600">
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
