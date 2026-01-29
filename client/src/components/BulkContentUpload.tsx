import { useState } from 'react'

interface ImageFile {
  filename: string
  data: string
  preview: string
}

interface BulkContentUploadProps {
  onPreprocess: (contentText: string, images: ImageFile[]) => void
  preprocessing: boolean
}

export type { ImageFile }

export function BulkContentUpload({ onPreprocess, preprocessing }: BulkContentUploadProps) {
  const [contentText, setContentText] = useState('')
  const [images, setImages] = useState<ImageFile[]>([])

  const handleTextFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      setContentText(text)
    }
    reader.readAsText(file)
    
    // Reset the input so the same file can be uploaded again
    e.target.value = ''
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    Array.from(files).forEach((file) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const base64 = reader.result as string
        setImages((prev) => [
          ...prev,
          {
            filename: file.name,
            data: base64,
            preview: base64,
          },
        ])
      }
      reader.readAsDataURL(file)
    })
  }

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index))
  }

  const handlePreprocess = () => {
    if (!contentText.trim()) {
      alert('Please enter some content first')
      return
    }
    onPreprocess(contentText, images)
  }

  return (
    <div className="flex flex-col gap-8 my-8">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Content</h3>
        
        <div className="flex gap-4 mb-4 items-center">
          <input
            type="file"
            accept=".txt,.md,.doc,.docx,text/plain"
            onChange={handleTextFileUpload}
            id="text-file-upload"
            className="hidden"
          />
          <label 
            htmlFor="text-file-upload" 
            className="inline-block px-4 py-2 bg-white text-blue-600 border border-blue-600 rounded cursor-pointer font-medium transition-all hover:bg-blue-50 text-sm"
          >
            Upload Text
          </label>
          {contentText && (
            <button
              onClick={() => setContentText('')}
              className="px-4 py-2 text-red-600 font-medium text-sm hover:underline"
              type="button"
            >
              Clear
            </button>
          )}
        </div>
        
        <textarea
          value={contentText}
          onChange={(e) => setContentText(e.target.value)}
          placeholder="Paste notes, bullet points, or raw text here..."
          rows={12}
          className="w-full min-h-[250px] p-4 border border-gray-200 rounded resize-y transition-colors focus:outline-none focus:border-blue-600 text-sm"
        />
      </div>

      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Images</h3>
        
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleImageUpload}
          id="bulk-image-upload"
          className="hidden"
        />
        <label 
          htmlFor="bulk-image-upload" 
          className="inline-block px-4 py-2 bg-white text-blue-600 border border-blue-600 rounded cursor-pointer font-medium transition-all hover:bg-blue-50 text-sm"
        >
          Add Images
        </label>

        {images.length > 0 && (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-4 mt-6">
            {images.map((img, idx) => (
              <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
                <img src={img.preview} alt={img.filename} className="w-full h-full object-cover" />
                <div className="absolute top-1 right-1">
                  <button
                    onClick={() => removeImage(idx)}
                    className="bg-black/50 text-white border-none rounded-full w-5 h-5 flex items-center justify-center cursor-pointer text-xs transition-colors hover:bg-red-600"
                    type="button"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col items-center gap-3">
        <button
          onClick={handlePreprocess}
          disabled={preprocessing || !contentText.trim()}
          className="px-8 py-3 bg-blue-600 text-white rounded-md cursor-pointer font-semibold transition-all hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {preprocessing ? 'Processing...' : 'Structure Presentation'}
        </button>
      </div>
    </div>
  )
}
