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
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp:
            file_storage.save(tmp.name)
            self.template_path = tmp.name
        
        try:
            prs = Presentation(self.template_path)
            
            if len(prs.slides) == 0:
                raise ValueError('The uploaded presentation has no slides. Please upload a presentation with at least one example slide.')
            
            layouts = extract_all_slides_as_layouts(prs)
            
            rules = {
                'slide_size': {
                    'width': prs.slide_width,
                    'height': prs.slide_height
                },
                'layouts': layouts,
                'extraction_method': 'rigid_slide_templates'
            }
            
            print(f"\n✓ extracted {len(layouts)} rigid layout templates")
            
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
            
            self.stored_rules = rules
            return rules
            
        except Exception as e:
            self.cleanup_template()
            raise
    
    def get_stored_rules(self):
        if self.stored_rules is None:
            raise ValueError('No rules stored. Please upload a PowerPoint file first.')
        return self.stored_rules
    
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
    
    def generate_deck(self, slide_specs):
        if not self.template_path or not os.path.exists(self.template_path):
            raise ValueError('No template presentation available')
        
        if self.stored_rules is None:
            raise ValueError('No rules stored')
        
        if not isinstance(slide_specs, list):
            raise ValueError(f'slide_specs must be a list, got {type(slide_specs)}')
        
        prs = Presentation(self.template_path)
        
        for i in range(len(prs.slides) - 1, -1, -1):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
        
        layouts = self.stored_rules.get('layouts', [])
        layout_map = {layout['name']: layout for layout in layouts}
        
        for i, spec in enumerate(slide_specs):
            if not isinstance(spec, dict):
                raise ValueError(f'slide_spec {i} must be a dict, got {type(spec)}: {spec}')
            
            layout_name = spec.get('layout_name')
            placeholders_data = spec.get('placeholders', [])
            
            print(f"\ngenerating slide {i + 1}: {layout_name}")
            print(f"content items: {len(placeholders_data)}")
            
            if layout_name not in layout_map:
                print(f"  error: layout '{layout_name}' not found, skipping")
                continue
            
            layout_template = layout_map[layout_name]
            
            try:
                generate_slide_from_template(
                    prs,
                    layout_template,
                    placeholders_data,
                    self.uploaded_images
                )
                print(f"  ✓ slide generated successfully")
            except Exception as e:
                print(f"  error generating slide: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        output = BytesIO()
        prs.save(output)
        output.seek(0)
        
        return base64.b64encode(output.getvalue()).decode('utf-8')
