import { downloadBase64File } from '../utils/placeholderHelpers'
import type { SlideSpec } from '../types'

interface DownloadSectionProps {
  generatedFile: string | null
  overflowInfo: { count: number; details: any[] } | null
  slides: SlideSpec[]
  generating: boolean
  onGenerateWithCompression: () => void
  onGenerateWithOverflow: () => void
}

export function DownloadSection({ 
  generatedFile, 
  overflowInfo, 
  slides,
  generating,
  onGenerateWithCompression,
  onGenerateWithOverflow
}: DownloadSectionProps) {
  const handleDownload = () => {
    if (!generatedFile) return
    
    downloadBase64File(
      generatedFile,
      'generated-slide.pptx',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    )
  }

  if (overflowInfo) {
    return (
      <div className="my-8 p-6 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-shrink-0 text-yellow-600 text-2xl font-bold">!</div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold mb-2 text-yellow-900">content overflow detected</h2>
            <p className="text-sm text-yellow-800 mb-4">
              {overflowInfo.count} text {overflowInfo.count === 1 ? 'box' : 'boxes'} exceed their boundaries. 
              some content may be cut off or hidden in the presentation.
            </p>
            
            <div className="bg-yellow-100 p-3 rounded mb-4 text-xs">
              <p className="font-medium text-yellow-900 mb-2">overflowing text boxes:</p>
              <ul className="space-y-1 text-yellow-800">
                {overflowInfo.details.slice(0, 5).map((detail, i) => (
                  <li key={i}>
                    slide {detail.slide_num} - {detail.shape_name} ({detail.char_count} chars)
                  </li>
                ))}
                {overflowInfo.count > 5 && (
                  <li className="text-yellow-700">...and {overflowInfo.count - 5} more</li>
                )}
              </ul>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={onGenerateWithCompression}
            disabled={generating}
            className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? 'compressing...' : 'apply AI compression'}
          </button>
          <button
            onClick={onGenerateWithOverflow}
            disabled={generating}
            className="flex-1 px-6 py-3 bg-gray-600 text-white font-medium rounded hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            download as-is
          </button>
        </div>
        
        <p className="text-xs text-yellow-700 mt-3">
          tip: AI compression will intelligently reduce content to fit. downloading as-is will include overflow warnings.
        </p>
      </div>
    )
  }

  if (!generatedFile) {
    return null
  }

  return (
    <div className="my-8 p-4 bg-green-50 border border-green-200 rounded">
      <h2 className="text-lg font-semibold mb-3 text-green-900">download</h2>
      <button 
        onClick={handleDownload}
        className="px-6 py-2 bg-green-600 text-white font-medium rounded hover:bg-green-700 transition-colors"
      >
        download powerpoint
      </button>
    </div>
  )
}
