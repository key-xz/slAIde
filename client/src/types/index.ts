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

export interface Shape {
  type: string
  name?: string
  position: {
    left: number
    top: number
    width: number
    height: number
  }
  properties?: Record<string, unknown>
}

export interface Layout {
  name: string
  master_name: string
  layout_idx: number
  placeholders: Placeholder[]
  shapes?: Shape[]
  category?: string
  categoryConfidence?: number
  categoryRationale?: string
  is_special?: boolean
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

export interface MasterSlide {
  name: string
  properties?: Record<string, unknown>
}

export interface SlideData {
  layout_name: string
  placeholders: Placeholder[]
}

export interface StylingRules {
  slide_size: {
    width: number
    height: number
  }
  masters: MasterSlide[]
  slides: SlideData[]
  layouts: Layout[]
  layoutCategories?: LayoutCategory[]
  theme_data?: {
    fonts: ThemeSettings['fonts']
    color_scheme: ThemeSettings['colors']
    format_scheme: Record<string, unknown>
    backgrounds: unknown[]
    theme_raw: unknown
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

export interface AIGeneratedSlide {
  layout_name: string
  layout_rationale?: string
  content: Record<string, string>
}

export interface ContentStructure {
  slides: AIGeneratedSlide[]
  deck_summary?: {
    title?: string
    topic?: string
    key_themes?: string[]
  }
}

export interface ContentWithLinks {
  chunks: TextChunk[]
  images: TaggedImage[]
  aiGeneratedStructure?: ContentStructure
}

export interface Template {
  id: string
  user_id: string
  name: string
  description?: string
  slide_size: {
    width: number
    height: number
  }
  theme_data?: any
  custom_theme?: any
  file_path?: string
  created_at: string
  updated_at: string
}

export interface LayoutRow {
  id: string
  template_id: string
  name: string
  master_name: string
  layout_idx: number
  placeholders: Placeholder[]
  shapes?: Shape[]
  category?: string
  category_confidence?: number
  category_rationale?: string
  created_at: string
  updated_at: string
}

export interface APIResponse<T = unknown> {
  success: boolean
  message?: string
  error?: string
  data?: T
}

export interface GenerateResponse {
  slides: Array<{
    layout_name: string
    placeholders: Array<{
      idx: number
      type: string
      content?: string
      image_index?: number
    }>
  }>
  images?: Record<string, string>
}

export interface OverflowDetail {
  slide_index: number
  layout_name: string
  placeholder_idx: number
  placeholder_name: string
  overflow_ratio: number
  original_content: string
}

export interface TextOverflowError {
  error: string
  overflow?: {
    violation_count: number
    details: OverflowDetail[]
    slide_specs: SlideSpec[]
  }
}

export type AIModel = 'fast' | 'openai' | 'kimi'
