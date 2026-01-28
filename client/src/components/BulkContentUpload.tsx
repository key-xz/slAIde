import { useState } from 'react'

interface ImageFile {
  filename: string
  data: string
  preview: string
}

interface BulkContentUploadProps {
  onGenerate: (contentText: string, images: ImageFile[]) => void
  generating: boolean
}

export function BulkContentUpload({ onGenerate, generating }: BulkContentUploadProps) {
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

  const handleGenerate = () => {
    if (!contentText.trim()) {
      alert('Please enter some content first')
      return
    }
    onGenerate(contentText, images)
  }

  return (
    <div className="flex flex-col gap-8 my-8">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-2">Enter Your Content</h3>
        <p className="text-gray-500 text-sm mb-4">
          Type your content, paste it, or upload a text file. The AI will organize it into slides based on your template layouts.
        </p>
        
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
            className="inline-block px-6 py-3 bg-white text-blue-600 border-2 border-blue-600 rounded cursor-pointer font-medium transition-all hover:bg-blue-600 hover:text-white"
          >
            Upload Text File
          </label>
          {contentText && (
            <button
              onClick={() => setContentText('')}
              className="px-6 py-3 bg-red-600 text-white rounded cursor-pointer font-medium transition-colors hover:bg-red-700"
              type="button"
            >
              Clear
            </button>
          )}
        </div>
        
        <textarea
          value={contentText}
          onChange={(e) => setContentText(e.target.value)}
          placeholder="Enter your content here...&#10;&#10;Example:&#10;- Introduction to our product&#10;- Key features: fast, reliable, easy to use&#10;- Customer testimonials&#10;- Pricing plans&#10;- Call to action"
          rows={12}
          className="w-full min-h-[250px] p-4 border-2 border-gray-200 rounded resize-y transition-colors focus:outline-none focus:border-blue-600"
        />
      </div>

      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-2">Upload Images (Optional)</h3>
        <p className="text-gray-500 text-sm mb-4">
          Upload images that should be included in your presentation. The AI will pair them with
          relevant content.
        </p>
        
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
          className="inline-block px-6 py-3 bg-white text-blue-600 border-2 border-blue-600 rounded cursor-pointer font-medium transition-all hover:bg-blue-600 hover:text-white"
        >
          Choose Images
        </label>

        {images.length > 0 && (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-4 mt-6">
            {images.map((img, idx) => (
              <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border-2 border-gray-200 bg-gray-50">
                <img src={img.preview} alt={img.filename} className="w-full h-full object-cover" />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2 flex justify-between items-end">
                  <span className="text-white text-xs overflow-hidden text-ellipsis whitespace-nowrap flex-1">{img.filename}</span>
                  <button
                    onClick={() => removeImage(idx)}
                    className="bg-red-600/90 text-white border-none rounded-full w-6 h-6 flex items-center justify-center cursor-pointer text-base leading-none transition-colors hover:bg-red-600 flex-shrink-0 ml-2"
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

      <div className="bg-white p-6 rounded-lg border border-gray-200 flex flex-col items-center gap-3">
        <button
          onClick={handleGenerate}
          disabled={generating || !contentText.trim()}
          className="px-8 py-4 bg-blue-600 text-white rounded-md cursor-pointer text-lg font-semibold transition-all shadow-[0_2px_4px_rgba(0,102,204,0.2)] hover:bg-blue-700 hover:shadow-[0_4px_8px_rgba(0,102,204,0.3)] hover:-translate-y-0.5 disabled:bg-gray-300 disabled:cursor-not-allowed disabled:shadow-none disabled:transform-none"
        >
          {generating ? 'Generating Preview...' : 'Generate Slide Preview'}
        </button>
        {images.length > 0 && (
          <p className="text-gray-500 text-sm m-0">
            {images.length} image{images.length !== 1 ? 's' : ''} ready to include
          </p>
        )}
      </div>
    </div>
  )
}
