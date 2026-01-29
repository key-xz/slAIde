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

export interface LayoutCategory {
  id: string
  name: string
  isPredefined: boolean
}

export interface Layout {
  name: string
  master_name: string
  layout_idx: number
  placeholders: Placeholder[]
  shapes?: any[]
  category?: string
  categoryConfidence?: number
  categoryRationale?: string
}

export interface ThemeSettings {
  fonts: {
    title: {
      name: string
      size: number
    }
    body: {
      name: string
      size: number
    }
  }
  colors: {
    [key: string]: {
      type: 'rgb' | 'theme'
      value: string
    }
  }
}

export interface StylingRules {
  slide_size: {
    width: number
    height: number
  }
  masters: any[]
  slides: any[]
  layouts: Layout[]
  layoutCategories?: LayoutCategory[]
  theme_data?: {
    fonts: ThemeSettings['fonts']
    color_scheme: ThemeSettings['colors']
    format_scheme: any
    backgrounds: any[]
    theme_raw: any
  }
  customTheme?: ThemeSettings
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

export interface TaggedImage {
  id: string
  filename: string
  data: string
  preview: string
  tags: string[]
  visionDescription?: string
  visionLabels?: string[]
  recommendedLayoutStyle?: string
  analyzedAt?: number
}

export interface TextChunk {
  id: string
  text: string
  startIndex: number
  endIndex: number
  linkedImageIds: string[]
}

export interface ContentWithLinks {
  chunks: TextChunk[]
  images: TaggedImage[]
}
