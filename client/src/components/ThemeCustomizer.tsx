import { useState } from 'react'
import type { ThemeSettings } from '../types'

interface ThemeCustomizerProps {
  currentTheme: ThemeSettings
  onThemeUpdate: (theme: ThemeSettings) => void
}

export function ThemeCustomizer({ currentTheme, onThemeUpdate }: ThemeCustomizerProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [theme, setTheme] = useState<ThemeSettings>(currentTheme)

  const handleFontChange = (category: 'title' | 'body', property: 'name' | 'size', value: string | number) => {
    const updatedTheme = {
      ...theme,
      fonts: {
        ...theme.fonts,
        [category]: {
          ...theme.fonts[category],
          [property]: value
        }
      }
    }
    setTheme(updatedTheme)
  }

  const handleColorChange = (colorName: string, value: string) => {
    const updatedTheme = {
      ...theme,
      colors: {
        ...theme.colors,
        [colorName]: {
          type: 'rgb' as const,
          value: value.replace('#', '')
        }
      }
    }
    setTheme(updatedTheme)
  }

  const handleApply = () => {
    onThemeUpdate(theme)
  }

  const handleReset = () => {
    setTheme(currentTheme)
  }

  // Common font options
  const fontOptions = [
    'Arial', 'Calibri', 'Times New Roman', 'Helvetica', 'Georgia',
    'Verdana', 'Comic Sans MS', 'Impact', 'Courier New', 'Trebuchet MS',
    'Neue Haas Grotesk Text Pro', 'Montserrat', 'Roboto', 'Open Sans', 'Lato'
  ]

  // Common PowerPoint theme colors
  const commonColors = [
    { name: 'dk1', label: 'Text/Background - Dark 1', default: '#000000' },
    { name: 'lt1', label: 'Text/Background - Light 1', default: '#FFFFFF' },
    { name: 'dk2', label: 'Text/Background - Dark 2', default: '#44546A' },
    { name: 'lt2', label: 'Text/Background - Light 2', default: '#E7E6E6' },
    { name: 'accent1', label: 'Accent 1', default: '#4472C4' },
    { name: 'accent2', label: 'Accent 2', default: '#ED7D31' },
    { name: 'accent3', label: 'Accent 3', default: '#A5A5A5' },
    { name: 'accent4', label: 'Accent 4', default: '#FFC000' },
    { name: 'accent5', label: 'Accent 5', default: '#5B9BD5' },
    { name: 'accent6', label: 'Accent 6', default: '#70AD47' }
  ]

  return (
    <div className="my-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex justify-between items-center cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <h4 className="m-0 text-base font-semibold text-gray-800 flex items-center gap-2">
          <span>🎨</span>
          <span>Theme Customization</span>
        </h4>
        <button className="text-gray-600 hover:text-gray-900 transition-colors">
          {isExpanded ? '▲' : '▼'}
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-6">
          {/* Font Settings */}
          <div className="space-y-4">
            <h5 className="text-sm font-semibold text-gray-700 border-b border-gray-300 pb-2">Font Settings</h5>
            
            <div className="grid grid-cols-2 gap-4">
              {/* Title Font */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Title Font</label>
                <select
                  value={theme.fonts.title.name}
                  onChange={(e) => handleFontChange('title', 'name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {fontOptions.map(font => (
                    <option key={font} value={font}>{font}</option>
                  ))}
                </select>
              </div>

              {/* Title Font Size */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Title Font Size (pt)</label>
                <input
                  type="number"
                  min="10"
                  max="96"
                  value={theme.fonts.title.size}
                  onChange={(e) => handleFontChange('title', 'size', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Body Font */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Body Font</label>
                <select
                  value={theme.fonts.body.name}
                  onChange={(e) => handleFontChange('body', 'name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {fontOptions.map(font => (
                    <option key={font} value={font}>{font}</option>
                  ))}
                </select>
              </div>

              {/* Body Font Size */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Body Font Size (pt)</label>
                <input
                  type="number"
                  min="8"
                  max="72"
                  value={theme.fonts.body.size}
                  onChange={(e) => handleFontChange('body', 'size', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Color Settings */}
          <div className="space-y-4">
            <h5 className="text-sm font-semibold text-gray-700 border-b border-gray-300 pb-2">Color Scheme</h5>
            
            <div className="grid grid-cols-2 gap-4">
              {commonColors.map(({ name, label, default: defaultColor }) => {
                const currentColor = theme.colors[name]?.value || defaultColor.replace('#', '')
                return (
                  <div key={name} className="space-y-1">
                    <label className="block text-xs font-medium text-gray-600">{label}</label>
                    <div className="flex gap-2 items-center">
                      <input
                        type="color"
                        value={`#${currentColor}`}
                        onChange={(e) => handleColorChange(name, e.target.value)}
                        className="w-12 h-8 rounded border border-gray-300 cursor-pointer"
                      />
                      <input
                        type="text"
                        value={`#${currentColor}`}
                        onChange={(e) => handleColorChange(name, e.target.value)}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="#000000"
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-300">
            <button
              onClick={handleApply}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition-colors text-sm"
            >
              Apply Theme Changes
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md font-medium hover:bg-gray-300 transition-colors text-sm"
            >
              Reset
            </button>
          </div>

          <p className="text-xs text-gray-500 italic">
            Note: Theme changes will apply to all slides when you generate the presentation.
          </p>
        </div>
      )}
    </div>
  )
}
