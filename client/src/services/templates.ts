import { supabase } from '../lib/supabase'
import type { StylingRules, Template, LayoutRow } from '../types'

// re-export types for convenience
export type { Template, LayoutRow }

// download template file from storage
export async function downloadTemplateFile(filePath: string): Promise<Blob> {
  const { data, error } = await supabase.storage
    .from('templates')
    .download(filePath)
  
  if (error) {
    throw new Error(`failed to download template file: ${error.message}`)
  }
  
  return data
}

function toNumber(value: any): number {
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : 0
}

function toStringSafe(value: any): string {
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return ''
  try {
    return String(value)
  } catch {
    return ''
  }
}

function sanitizeSlideSize(slideSize: any): { width: number; height: number } {
  return {
    width: toNumber(slideSize?.width),
    height: toNumber(slideSize?.height),
  }
}

function sanitizePosition(pos: any) {
  return {
    left: toNumber(pos?.left),
    top: toNumber(pos?.top),
    width: toNumber(pos?.width),
    height: toNumber(pos?.height),
  }
}

function sanitizePlaceholders(placeholders: any): any[] {
  if (!Array.isArray(placeholders)) return []
  return placeholders.map((ph) => ({
    idx: toNumber(ph?.idx),
    type: toStringSafe(ph?.type),
    name: toStringSafe(ph?.name),
    position: sanitizePosition(ph?.position),
  }))
}

function sanitizeShapes(shapes: any): any[] | null {
  if (!Array.isArray(shapes)) return null
  // keep only geometry needed for preview; drop everything else
  return shapes.map((s) => ({
    position: sanitizePosition(s?.position),
  }))
}

// save a complete template with all its layouts
export async function saveTemplate(
  name: string,
  stylingRules: StylingRules,
  description?: string,
  file?: File
): Promise<{ template: Template; layouts: LayoutRow[] }> {
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    throw new Error('user must be authenticated to save templates')
  }

  // upload file to storage if provided
  let filePath: string | null = null
  if (file) {
    const fileExt = file.name.split('.').pop()
    const fileName = `${user.id}/${Date.now()}.${fileExt}`
    
    const { error: uploadError } = await supabase.storage
      .from('templates')
      .upload(fileName, file, {
        upsert: false,
      })
    
    if (uploadError) {
      throw new Error(`failed to upload template file: ${uploadError.message}`)
    }
    
    filePath = fileName
  }

  // important: only store plain json fields (avoids cyclic refs from extraction output)
  const slideSize = sanitizeSlideSize(stylingRules.slide_size)

  const templatePayload = {
    user_id: user.id,
    name,
    description,
    slide_size: slideSize,
    theme_data: null,
    custom_theme: null,
    file_path: filePath,
  }

  // insert or update template
  const { data: template, error: templateError } = await supabase
    .from('templates')
    .upsert(templatePayload, {
      onConflict: 'user_id,name',
    })
    .select()
    .single()

  if (templateError) {
    console.error('supabase error saving template:', templateError)
    throw new Error(`failed to save template: ${templateError.message}`)
  }

  // delete existing layouts for this template (cascade)
  const { error: deleteError } = await supabase
    .from('layouts')
    .delete()
    .eq('template_id', template.id)

  if (deleteError) {
    throw new Error(`failed to delete old layouts: ${deleteError.message}`)
  }

  // insert new layouts (sanitize to plain json)
  const layoutsToInsert = stylingRules.layouts.map((layout) => ({
    template_id: template.id,
    name: toStringSafe(layout?.name),
    master_name: toStringSafe((layout as any)?.master_name),
    layout_idx: toNumber((layout as any)?.layout_idx),
    placeholders: sanitizePlaceholders((layout as any)?.placeholders),
    shapes: sanitizeShapes((layout as any)?.shapes),
    category: toStringSafe((layout as any)?.category) || null,
    category_confidence: typeof (layout as any)?.categoryConfidence === 'number' ? (layout as any).categoryConfidence : null,
    category_rationale: toStringSafe((layout as any)?.categoryRationale) || null,
  }))

  const { data: layouts, error: layoutsError } = await supabase
    .from('layouts')
    .insert(layoutsToInsert)
    .select()

  if (layoutsError) {
    console.error('supabase error saving layouts:', layoutsError)
    throw new Error(`failed to save layouts: ${layoutsError.message}`)
  }

  return { template, layouts: layouts || [] }
}

// get all templates for the current user
export async function getUserTemplates(): Promise<Template[]> {
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    return []
  }

  const { data, error } = await supabase
    .from('templates')
    .select('*')
    .eq('user_id', user.id)
    .order('updated_at', { ascending: false })

  if (error) {
    throw new Error(`failed to fetch templates: ${error.message}`)
  }

  return data || []
}

// get a specific template with its layouts
export async function getTemplate(
  templateId: string
): Promise<{ rules: StylingRules; template: Template } | null> {
  const { data: template, error: templateError } = await supabase
    .from('templates')
    .select('*')
    .eq('id', templateId)
    .single()

  if (templateError) {
    throw new Error(`failed to fetch template: ${templateError.message}`)
  }

  const { data: layouts, error: layoutsError } = await supabase
    .from('layouts')
    .select('*')
    .eq('template_id', templateId)
    .order('layout_idx')

  if (layoutsError) {
    throw new Error(`failed to fetch layouts: ${layoutsError.message}`)
  }

  // reconstruct styling rules
  const stylingRules: StylingRules = {
    slide_size: template.slide_size,
    theme_data: template.theme_data,
    customTheme: template.custom_theme,
    masters: [], // not stored in db currently
    slides: [], // not stored in db currently
    layouts: (layouts || []).map(layout => ({
      name: layout.name,
      master_name: layout.master_name,
      layout_idx: layout.layout_idx,
      placeholders: layout.placeholders,
      shapes: layout.shapes,
      category: layout.category,
      categoryConfidence: layout.category_confidence,
      categoryRationale: layout.category_rationale,
    })),
  }

  return { rules: stylingRules, template: template as Template }
}

// delete a template (cascades to layouts)
export async function deleteTemplate(templateId: string): Promise<void> {
  // delete layouts first so this works even if db cascade isn't configured
  const { error: layoutsError } = await supabase
    .from('layouts')
    .delete()
    .eq('template_id', templateId)

  if (layoutsError) {
    throw new Error(`failed to delete template layouts: ${layoutsError.message}`)
  }

  const { error: templateError } = await supabase
    .from('templates')
    .delete()
    .eq('id', templateId)

  if (templateError) {
    throw new Error(`failed to delete template: ${templateError.message}`)
  }
}

// update template metadata
export async function updateTemplate(
  templateId: string,
  updates: { name?: string; description?: string }
): Promise<Template> {
  const { data, error } = await supabase
    .from('templates')
    .update(updates)
    .eq('id', templateId)
    .select()
    .single()

  if (error) {
    throw new Error(`failed to update template: ${error.message}`)
  }

  return data
}

// delete a specific layout from a template
export async function deleteLayout(
  templateId: string,
  layoutName: string
): Promise<void> {
  const { error } = await supabase
    .from('layouts')
    .delete()
    .eq('template_id', templateId)
    .eq('name', layoutName)

  if (error) {
    throw new Error(`failed to delete layout: ${error.message}`)
  }
}

// get all layouts across all user templates with template info
export async function getAllUserLayouts(): Promise<Array<LayoutRow & { template: Template }>> {
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    return []
  }

  const { data, error } = await supabase
    .from('layouts')
    .select(`
      *,
      template:templates(*)
    `)
    .eq('templates.user_id', user.id)
    .order('created_at', { ascending: false })

  if (error) {
    throw new Error(`failed to fetch all layouts: ${error.message}`)
  }

  return (data || []) as Array<LayoutRow & { template: Template }>
}
