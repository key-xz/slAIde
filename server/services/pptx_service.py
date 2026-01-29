import os
import tempfile
import base64
from io import BytesIO
from pptx import Presentation
from utils.pptx_extractors import (
    extract_master_properties,
    extract_shape_properties
)
from utils.style_extractor import (
    extract_placeholder_complete_styling,
    apply_placeholder_styling
)
from utils.slide_layout_extractor import extract_all_slides_as_layouts
from utils.slide_generator import generate_slide_from_template


class PPTXService:
    def __init__(self):
        self.stored_rules = None
        self.template_path = None
        self.uploaded_images = {}
    
    def cleanup_template(self):
        if self.template_path and os.path.exists(self.template_path):
            try:
                os.unlink(self.template_path)
                self.template_path = None
            except Exception as e:
                print(f"error cleaning up template: {e}")
    
    def extract_rules_from_file(self, file_storage):
        self.cleanup_template()
        self.uploaded_images = {}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp:
            file_storage.save(tmp.name)
            self.template_path = tmp.name
        
        try:
            prs = Presentation(self.template_path)
            
            if len(prs.slides) == 0:
                raise ValueError('The uploaded presentation has no slides. Please upload a presentation with at least one example slide.')
            
            extraction_result = extract_all_slides_as_layouts(prs, self.template_path)
            layouts = extraction_result['layouts']
            theme_data = extraction_result.get('theme_data')
            
            print(f"\n✓ extracted {len(layouts)} rigid layout templates")
            
            # STRICT VALIDATION: Fail fast if critical design specs are missing
            self._validate_complete_extraction(prs, layouts, theme_data)
            
            from config import PREDEFINED_LAYOUT_CATEGORIES
            from services.ai_service import AIService
            
            ai_service = AIService()
            categorization_result = ai_service.categorize_layouts(
                layouts, 
                PREDEFINED_LAYOUT_CATEGORIES
            )
            
            all_categories = PREDEFINED_LAYOUT_CATEGORIES + categorization_result['new_categories']
            
            rules = {
                'slide_size': {
                    'width': prs.slide_width,
                    'height': prs.slide_height
                },
                'layouts': categorization_result['layouts'],
                'layoutCategories': all_categories,
                'theme_data': theme_data,  # Include complete theme data
                'extraction_method': 'rigid_slide_templates'
            }
            
            text_placeholder_count = sum(
                len([p for p in layout['placeholders'] if p['type'] == 'text'])
                for layout in layouts
            )
            image_placeholder_count = sum(
                len([p for p in layout['placeholders'] if p['type'] == 'image'])
                for layout in layouts
            )
            
            print(f"  total text placeholders: {text_placeholder_count}")
            print(f"  total image placeholders: {image_placeholder_count}")
            
            # Log theme data extraction
            if theme_data:
                if theme_data.get('color_scheme'):
                    print(f"  ✓ theme: {len(theme_data['color_scheme'])} colors extracted")
                if theme_data.get('format_scheme'):
                    print(f"  ✓ theme: format styles extracted")
                if theme_data.get('theme_raw'):
                    print(f"  ✓ theme: raw theme XML preserved")
            
            self.stored_rules = rules
            return rules
            
        except Exception as e:
            self.cleanup_template()
            raise
    
    def get_stored_rules(self):
        if self.stored_rules is None:
            raise ValueError('No rules stored. Please upload a PowerPoint file first.')
        return self.stored_rules
    
    def _validate_complete_extraction(self, prs, layouts, theme_data):
        """
        Strict validation: Ensure all critical design specifications were successfully extracted.
        Fails fast if any required styling information is missing.
        """
        errors = []
        
        # 1. Validate slide dimensions
        if not prs.slide_width or not prs.slide_height:
            errors.append("Failed to extract slide dimensions (width/height)")
        
        # 2. Validate theme data
        if not theme_data:
            errors.append("Failed to extract theme data from presentation")
        else:
            # Validate fonts
            if not theme_data.get('fonts'):
                errors.append("Failed to extract font information from theme")
            else:
                fonts = theme_data['fonts']
                if not fonts.get('title') or not fonts['title'].get('name'):
                    errors.append("Failed to extract title font name from theme")
                if not fonts.get('body') or not fonts['body'].get('name'):
                    errors.append("Failed to extract body font name from theme")
            
            # Validate color scheme
            if not theme_data.get('color_scheme'):
                errors.append("Failed to extract color scheme from theme")
        
        # 3. Validate layouts
        if not layouts or len(layouts) == 0:
            errors.append("No layouts were successfully extracted from presentation")
        
        for i, layout in enumerate(layouts):
            layout_name = layout.get('name', f'Layout {i}')
            
            # Validate layout has placeholders
            if 'placeholders' not in layout:
                errors.append(f"Layout '{layout_name}': Missing placeholders array")
                continue
            
            # Validate each placeholder has complete properties
            for ph in layout['placeholders']:
                ph_idx = ph.get('idx', '?')
                
                # Check for required fields
                if 'type' not in ph:
                    errors.append(f"Layout '{layout_name}', placeholder {ph_idx}: Missing type")
                if 'properties' not in ph:
                    errors.append(f"Layout '{layout_name}', placeholder {ph_idx}: Missing properties")
                    continue
                
                props = ph['properties']
                
                # Validate position data
                if 'position' not in props:
                    errors.append(f"Layout '{layout_name}', placeholder {ph_idx}: Missing position data")
                else:
                    pos = props['position']
                    required_pos_fields = ['left', 'top', 'width', 'height']
                    for field in required_pos_fields:
                        if field not in pos or pos[field] is None:
                            errors.append(f"Layout '{layout_name}', placeholder {ph_idx}: Missing position.{field}")
                
                # For text placeholders, validate font properties
                if ph.get('type') == 'text':
                    if 'font_props' not in props:
                        errors.append(f"Layout '{layout_name}', text placeholder {ph_idx}: Missing font properties")
                    else:
                        font_props = props['font_props']
                        if not font_props.get('name'):
                            errors.append(f"Layout '{layout_name}', text placeholder {ph_idx}: Missing font name")
                        if not font_props.get('size'):
                            errors.append(f"Layout '{layout_name}', text placeholder {ph_idx}: Missing font size")
        
        # If any errors found, fail fast
        if errors:
            error_message = "❌ TEMPLATE EXTRACTION FAILED - Incomplete design specifications:\n\n"
            error_message += "\n".join(f"  • {err}" for err in errors)
            error_message += "\n\nPlease upload a valid PowerPoint template with complete formatting information."
            error_message += "\nEnsure the template has:"
            error_message += "\n  - Defined theme with fonts and colors"
            error_message += "\n  - Properly formatted slide layouts"
            error_message += "\n  - Text placeholders with font specifications"
            raise ValueError(error_message)
        
        print("  ✅ All critical design specifications validated successfully")
    
    def update_stored_rules(self, rules):
        """update the stored rules (used for modifying layout properties like is_special)"""
        self.stored_rules = rules
    
    def generate_slide(self, layout_name, inputs):
        if not self.template_path or not os.path.exists(self.template_path):
            raise ValueError('No template presentation available')
        
        if self.stored_rules is None:
            raise ValueError('No rules stored')
        
        prs = Presentation(self.template_path)
        
        target_layout = None
        for master in prs.slide_masters:
            for layout in master.slide_layouts:
                if layout.name == layout_name:
                    target_layout = layout
                    break
            if target_layout:
                break
        
        if not target_layout:
            raise ValueError(f'Layout "{layout_name}" not found')
        
        slide = prs.slides.add_slide(target_layout)
        
        for placeholder in slide.placeholders:
            ph_idx = str(placeholder.placeholder_format.idx)
            
            if ph_idx in inputs:
                input_data = inputs[ph_idx]
                input_type = input_data.get('type')
                
                if input_type == 'text':
                    text_value = input_data.get('value', '')
                    if hasattr(placeholder, 'text_frame'):
                        placeholder.text = text_value
                
                elif input_type == 'image':
                    image_data = input_data.get('value')
                    if image_data:
                        if ',' in image_data:
                            image_data = image_data.split(',')[1]
                        
                        image_bytes = base64.b64decode(image_data)
                        image_stream = BytesIO(image_bytes)
                        
                        left = placeholder.left
                        top = placeholder.top
                        width = placeholder.width
                        height = placeholder.height
                        
                        sp = placeholder.element
                        sp.getparent().remove(sp)
                        slide.shapes.add_picture(image_stream, left, top, width, height)
        
        output = BytesIO()
        prs.save(output)
        output.seek(0)
        
        return base64.b64encode(output.getvalue()).decode('utf-8')
    
    def store_image(self, filename, image_data_base64):
        self.uploaded_images[filename] = image_data_base64
    
    def clear_images(self):
        self.uploaded_images = {}
    
    def _apply_theme_overrides(self, custom_theme):
        """
        Apply custom theme overrides to the stored rules.
        This modifies layout templates to use custom fonts and colors.
        """
        if not custom_theme or not self.stored_rules:
            return
        
        custom_fonts = custom_theme.get('fonts', {})
        custom_colors = custom_theme.get('colors', {})
        
        if custom_fonts:
            print(f"  ✓ overriding fonts:")
            if 'title' in custom_fonts:
                print(f"    - title: {custom_fonts['title'].get('name')} {custom_fonts['title'].get('size')}pt")
            if 'body' in custom_fonts:
                print(f"    - body: {custom_fonts['body'].get('name')} {custom_fonts['body'].get('size')}pt")
        
        if custom_colors:
            print(f"  ✓ overriding {len(custom_colors)} theme colors")
        
        # Update all layout templates with custom theme
        layouts = self.stored_rules.get('layouts', [])
        for layout in layouts:
            for placeholder in layout.get('placeholders', []):
                props = placeholder.get('properties', {})
                
                # Override font properties in text placeholders
                if placeholder.get('type') == 'text' and 'font_props' in props:
                    font_props = props['font_props']
                    
                    # Determine if this is a title or body based on name/position
                    is_title = 'title' in placeholder.get('name', '').lower()
                    
                    if is_title and 'title' in custom_fonts:
                        if 'name' in custom_fonts['title']:
                            font_props['name'] = custom_fonts['title']['name']
                        if 'size' in custom_fonts['title']:
                            font_props['size'] = custom_fonts['title']['size']
                    elif not is_title and 'body' in custom_fonts:
                        if 'name' in custom_fonts['body']:
                            font_props['name'] = custom_fonts['body']['name']
                        if 'size' in custom_fonts['body']:
                            font_props['size'] = custom_fonts['body']['size']
                    
                    # Override color if specified and matches theme color names
                    if 'color' in font_props and custom_colors:
                        # For now, apply primary text color (dk1) if available
                        if 'dk1' in custom_colors:
                            color_info = custom_colors['dk1']
                            if color_info.get('type') == 'rgb' and 'value' in color_info:
                                font_props['color'] = {
                                    'type': 'rgb',
                                    'rgb': color_info['value']
                                }
        
        print(f"  ✅ theme overrides applied to {len(layouts)} layouts")
    
    def generate_deck(self, slide_specs, custom_theme=None):
        if not self.template_path or not os.path.exists(self.template_path):
            raise ValueError('No template presentation available')
        
        if self.stored_rules is None:
            raise ValueError('No rules stored')
        
        if not isinstance(slide_specs, list):
            raise ValueError(f'slide_specs must be a list, got {type(slide_specs)}')
        
        # Load BOTH the source (for cloning) and target (for output)
        source_prs = Presentation(self.template_path)
        target_prs = Presentation(self.template_path)
        
        # Clear all slides from target
        for i in range(len(target_prs.slides) - 1, -1, -1):
            rId = target_prs.slides._sldIdLst[i].rId
            target_prs.part.drop_rel(rId)
            del target_prs.slides._sldIdLst[i]
        
        print(f"\n🔄 cloning {len(slide_specs)} slides from template")
        
        # Apply custom theme overrides if provided
        if custom_theme:
            print(f"\n🎨 applying custom theme overrides...")
            self._apply_theme_overrides(custom_theme)
        
        layouts = self.stored_rules.get('layouts', [])
        layout_map = {layout['name']: layout for layout in layouts}
        
        # Import the cloning utility
        from utils.slide_cloner import clone_slide_with_content
        
        for i, spec in enumerate(slide_specs):
            if not isinstance(spec, dict):
                raise ValueError(f'slide_spec {i} must be a dict, got {type(spec)}: {spec}')
            
            layout_name = spec.get('layout_name')
            placeholders_data = spec.get('placeholders', [])
            
            print(f"\ngenerating slide {i + 1}: {layout_name}")
            print(f"content items: {len(placeholders_data)}")
            
            # Debug: show what content we're passing
            for ph in placeholders_data:
                ph_idx = ph.get('idx', '?')
                ph_type = ph.get('type', '?')
                if ph_type == 'text':
                    content_preview = ph.get('content', '')[:50]
                    print(f"  placeholder idx={ph_idx}, type={ph_type}, content='{content_preview}...'")
                else:
                    print(f"  placeholder idx={ph_idx}, type={ph_type}")
            
            if layout_name not in layout_map:
                print(f"  error: layout '{layout_name}' not found, skipping")
                continue
            
            layout_template = layout_map[layout_name]
            
            # Get the source slide index (0-based) from the layout
            source_slide_index = layout_template.get('layout_index', layout_template.get('slide_number', 1) - 1)
            
            try:
                # Clone the slide from source template, filling placeholders with new content
                clone_slide_with_content(
                    source_prs,
                    source_slide_index,
                    target_prs,
                    placeholders_data,
                    self.uploaded_images
                )
                print(f"  ✓ slide cloned successfully from template slide {source_slide_index + 1}")
            except Exception as e:
                print(f"  ❌ error cloning slide: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        output = BytesIO()
        target_prs.save(output)
        output.seek(0)
        
        return base64.b64encode(output.getvalue()).decode('utf-8')
