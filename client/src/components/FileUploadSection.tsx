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
    <div className="my-8">
      <h2 className="text-lg font-semibold mb-4">Template</h2>
      <input
        type="file"
        accept={APP_CONSTANTS.acceptedFileTypes.join(',')}
        onChange={handleChange}
        className="block my-4 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />
      <button 
        onClick={() => onUpload()}
        disabled={!file || loading}
        className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
      >
        {loading ? 'Processing...' : 'Upload Template'}
      </button>
    </div>
  )
}
