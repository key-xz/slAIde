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
    <div className="download-section">
      <h2>4. download generated slides</h2>
      <button onClick={handleDownload}>Download PowerPoint</button>
    </div>
  )
}
