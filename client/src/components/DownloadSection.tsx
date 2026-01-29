import { downloadBase64File } from '../utils/placeholderHelpers'

interface DownloadSectionProps {
  generatedFile: string
}

export function DownloadSection({ generatedFile }: DownloadSectionProps) {
  const handleDownload = () => {
    downloadBase64File(
      generatedFile,
      'generated-slide.pptx',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    )
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
