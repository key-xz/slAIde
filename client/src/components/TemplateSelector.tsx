import type { Template } from '../types'

interface TemplateSelectorProps {
  templates: Template[]
  currentTemplateId: string | null
  onSelectTemplate: (templateId: string) => void
  onDeleteTemplate: (templateId: string) => void
  loading?: boolean
}

export function TemplateSelector({
  templates,
  currentTemplateId,
  onSelectTemplate,
  onDeleteTemplate,
  loading,
}: TemplateSelectorProps) {
  if (templates.length === 0) {
    return (
      <div className="my-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-gray-700">
        no saved templates yet. upload a powerpoint template to get started.
      </div>
    )
  }

  return (
    <div className="my-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        saved templates ({templates.length})
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => {
          const isActive = template.id === currentTemplateId
          
          return (
            <div
              key={template.id}
              className={`relative group bg-white border-2 rounded-lg p-4 transition-all ${
                isActive
                  ? 'border-blue-500 shadow-md'
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }`}
            >
              <button
                onClick={() => !isActive && onSelectTemplate(template.id)}
                disabled={loading || isActive}
                className="w-full text-left"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 text-sm truncate pr-2">
                    {template.name}
                  </h4>
                  {isActive && (
                    <span className="flex-shrink-0 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                      active
                    </span>
                  )}
                </div>
                
                {template.description && (
                  <p className="text-xs text-gray-500 mb-2 line-clamp-2">
                    {template.description}
                  </p>
                )}
                
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>
                    {template.slide_size?.width}x{template.slide_size?.height}
                  </span>
                  <span>
                    {new Date(template.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </button>
              
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  if (confirm(`delete template "${template.name}"?`)) {
                    onDeleteTemplate(template.id)
                  }
                }}
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-600 p-1"
                title="delete template"
              >
                ✕
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
