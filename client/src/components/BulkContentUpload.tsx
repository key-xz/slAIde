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
    <div className="bulk-content-upload">
      <div className="content-section">
        <h3>Enter Your Content</h3>
        <p className="helper-text">
          Paste or type your content here. It can be unorganized notes, bullet points, or
          paragraphs. The AI will organize it into slides.
        </p>
        <textarea
          value={contentText}
          onChange={(e) => setContentText(e.target.value)}
          placeholder="Enter your content here...&#10;&#10;Example:&#10;- Introduction to our product&#10;- Key features: fast, reliable, easy to use&#10;- Customer testimonials&#10;- Pricing plans&#10;- Call to action"
          rows={12}
          className="content-textarea"
        />
      </div>

      <div className="images-section">
        <h3>Upload Images (Optional)</h3>
        <p className="helper-text">
          Upload images that should be included in your presentation. The AI will pair them with
          relevant content.
        </p>
        
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleImageUpload}
          id="bulk-image-upload"
          className="file-input"
        />
        <label htmlFor="bulk-image-upload" className="file-input-label">
          Choose Images
        </label>

        {images.length > 0 && (
          <div className="image-preview-grid">
            {images.map((img, idx) => (
              <div key={idx} className="image-preview-item">
                <img src={img.preview} alt={img.filename} />
                <div className="image-preview-overlay">
                  <span className="image-filename">{img.filename}</span>
                  <button
                    onClick={() => removeImage(idx)}
                    className="remove-image-btn"
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

      <div className="generate-section">
        <button
          onClick={handleGenerate}
          disabled={generating || !contentText.trim()}
          className="generate-deck-btn"
        >
          {generating ? 'Generating Deck...' : 'Generate Deck with AI'}
        </button>
        {images.length > 0 && (
          <p className="info-text">
            {images.length} image{images.length !== 1 ? 's' : ''} ready to include
          </p>
        )}
      </div>
    </div>
  )
}
