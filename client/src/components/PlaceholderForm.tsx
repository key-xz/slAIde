import type { Layout, PlaceholderInput as PlaceholderInputType } from '../types'
import { PlaceholderInput } from './PlaceholderInput'

interface PlaceholderFormProps {
  layout: Layout
  inputs: Record<string, PlaceholderInputType>
  generating: boolean
  onTextInput: (idx: string, value: string) => void
  onImageInput: (idx: string, file: File) => void
  onGenerate: () => void
}

export function PlaceholderForm({
  layout,
  inputs,
  generating,
  onTextInput,
  onImageInput,
  onGenerate,
}: PlaceholderFormProps) {
  return (
    <div className="placeholder-form">
      <h2>3. fill placeholders for "{layout.name}"</h2>
      {layout.placeholders.map((ph) => (
        <PlaceholderInput
          key={ph.idx}
          placeholder={ph}
          value={inputs[String(ph.idx)]}
          onTextInput={onTextInput}
          onImageInput={onImageInput}
        />
      ))}
      <button onClick={onGenerate} disabled={generating}>
        {generating ? 'generating...' : 'generate'}
      </button>
    </div>
  )
}
