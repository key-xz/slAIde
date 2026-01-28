export interface Placeholder {
  idx: number
  type: string
  name: string
  position: {
    left: number
    top: number
    width: number
    height: number
  }
}

export interface Layout {
  name: string
  master_name: string
  layout_idx: number
  placeholders: Placeholder[]
}

export interface StylingRules {
  slide_size: {
    width: number
    height: number
  }
  masters: any[]
  slides: any[]
  layouts: Layout[]
}

export interface PlaceholderInput {
  type: 'text' | 'image'
  value: string
}

export interface SlideContent {
  idx: number
  type: 'text' | 'image'
  content?: string
  image_index?: number
  imageData?: string
}

export interface SlideSpec {
  id: string
  layout_name: string
  placeholders: SlideContent[]
}
