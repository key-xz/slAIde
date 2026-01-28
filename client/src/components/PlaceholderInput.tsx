import type { Placeholder, PlaceholderInput as PlaceholderInputType } from '../types'
import { getPlaceholderTypeLabel, isImagePlaceholder } from '../utils/placeholderHelpers'
import { APP_CONSTANTS } from '../config'

interface PlaceholderInputProps {
  placeholder: Placeholder
  value?: PlaceholderInputType
  onTextInput: (idx: string, value: string) => void
  onImageInput: (idx: string, file: File) => void
}

export function PlaceholderInput({
  placeholder,
  value,
  onTextInput,
  onImageInput,
}: PlaceholderInputProps) {
  const isImage = isImagePlaceholder(placeholder.type)
  const idx = String(placeholder.idx)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onImageInput(idx, file)
    }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onTextInput(idx, e.target.value)
  }

  return (
    <div className="placeholder-input">
      <h4>
        {placeholder.name} ({getPlaceholderTypeLabel(placeholder.type)})
      </h4>
      {isImage ? (
        <div className="image-input">
          <input
            type="file"
            accept={APP_CONSTANTS.acceptedImageTypes.join(',')}
            onChange={handleFileChange}
          />
          {value?.type === 'image' && (
            <div className="image-preview">
              <img
                src={value.value}
                alt="Preview"
                style={{ maxWidth: '200px', maxHeight: '150px' }}
              />
            </div>
          )}
        </div>
      ) : (
        <div className="text-input">
          <textarea
            value={value?.value || ''}
            onChange={handleTextChange}
            placeholder={`Enter ${getPlaceholderTypeLabel(placeholder.type).toLowerCase()}`}
            rows={3}
            style={{ width: '100%' }}
          />
        </div>
      )}
    </div>
  )
}
