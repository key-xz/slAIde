import { supabase } from '../lib/supabase'
import type { StylingRules, Template, LayoutRow } from '../types'

// re-export types for convenience
export type { Template, LayoutRow }

// save a complete template with all its layouts
export async function saveTemplate(
  name: string,
  stylingRules: StylingRules,
  description?: string
): Promise<{ template: Template; layouts: LayoutRow[] }> {
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    throw new Error('user must be authenticated to save templates')
  }

  // insert or update template
  const { data: template, error: templateError } = await supabase
    .from('templates')
    .upsert({
      user_id: user.id,
      name,
      description,
      slide_size: stylingRules.slide_size,
      theme_data: stylingRules.theme_data,
      custom_theme: stylingRules.customTheme,
    }, {
      onConflict: 'user_id,name',
    })
    .select()
    .single()

  if (templateError) {
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

  // insert new layouts
  const layoutsToInsert = stylingRules.layouts.map(layout => ({
    template_id: template.id,
    name: layout.name,
    master_name: layout.master_name,
    layout_idx: layout.layout_idx,
    placeholders: layout.placeholders,
    shapes: layout.shapes,
    category: layout.category,
    category_confidence: layout.categoryConfidence,
    category_rationale: layout.categoryRationale,
  }))

  const { data: layouts, error: layoutsError } = await supabase
    .from('layouts')
    .insert(layoutsToInsert)
    .select()

  if (layoutsError) {
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
export async function getTemplate(templateId: string): Promise<StylingRules | null> {
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

  return stylingRules
}

// delete a template (cascades to layouts)
export async function deleteTemplate(templateId: string): Promise<void> {
  const { error } = await supabase
    .from('templates')
    .delete()
    .eq('id', templateId)

  if (error) {
    throw new Error(`failed to delete template: ${error.message}`)
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
