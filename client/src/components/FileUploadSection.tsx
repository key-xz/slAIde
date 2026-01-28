import { APP_CONSTANTS } from '../config'

interface FileUploadSectionProps {
  file: File | null
  loading: boolean
  onFileChange: (file: File | null) => void
  onUpload: () => void
}

export function FileUploadSection({
  file,
  loading,
  onFileChange,
  onUpload,
}: FileUploadSectionProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    onFileChange(selectedFile || null)
  }

  return (
    <div className="upload-section">
      <h2>1. upload powerpoint as template</h2>
      <input
        type="file"
        accept={APP_CONSTANTS.acceptedFileTypes.join(',')}
        onChange={handleChange}
      />
      <button onClick={onUpload} disabled={!file || loading}>
        {loading ? 'extracting...' : 'extract Rules'}
      </button>
    </div>
  )
}
