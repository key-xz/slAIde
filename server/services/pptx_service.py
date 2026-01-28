import os
import tempfile
import base64
from io import BytesIO
from pptx import Presentation
from utils.pptx_extractors import (
    extract_master_properties,
    extract_shape_properties
)


class PPTXService:
    def __init__(self):
        self.stored_rules = None
        self.template_path = None
    
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
            
            rules = {
                'slide_size': {
                    'width': prs.slide_width,
                    'height': prs.slide_height
                },
                'masters': [],
                'slides': [],
                'layouts': []
            }
            
            layout_map = {}
            for master in prs.slide_masters:
                master_props = extract_master_properties(master)
                rules['masters'].append(master_props)
                
                for layout_idx, layout in enumerate(master.slide_layouts):
                    layout_key = f"{master.name}_{layout.name}"
                    if layout_key not in layout_map:
                        layout_map[layout_key] = {
                            'name': layout.name,
                            'master_name': master.name if hasattr(master, 'name') else 'Master',
                            'layout_idx': layout_idx,
                            'placeholders': []
                        }
                        
                        for ph in layout.placeholders:
                            ph_type = str(ph.placeholder_format.type)
                            layout_map[layout_key]['placeholders'].append({
                                'idx': ph.placeholder_format.idx,
                                'type': ph_type,
                                'name': ph.name,
                                'position': {
                                    'left': ph.left,
                                    'top': ph.top,
                                    'width': ph.width,
                                    'height': ph.height
                                }
                            })
            
            rules['layouts'] = list(layout_map.values())
            
            for idx, slide in enumerate(prs.slides):
                slide_props = {
                    'index': idx,
                    'layout_name': slide.slide_layout.name,
                    'shapes': []
                }
                
                for shape in slide.shapes:
                    try:
                        shape_props = extract_shape_properties(shape)
                        slide_props['shapes'].append(shape_props)
                    except Exception as e:
                        print(f"error processing shape: {e}")
                        continue
                
                rules['slides'].append(slide_props)
            
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
