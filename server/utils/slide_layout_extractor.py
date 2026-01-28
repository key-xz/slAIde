from pptx.enum.shapes import MSO_SHAPE_TYPE
from utils.style_extractor import extract_placeholder_complete_styling


def extract_shape_complete_properties(shape, placeholder_idx):
    
    shape_type = shape.shape_type
    
    base_props = {
        'placeholder_idx': placeholder_idx,
        'shape_type': str(shape_type),
        'name': shape.name,
        'position': {
            'left': shape.left,
            'top': shape.top,
            'width': shape.width,
            'height': shape.height
        },
        'rotation': shape.rotation if hasattr(shape, 'rotation') else 0
    }
    
    if shape_type == MSO_SHAPE_TYPE.PICTURE:
        base_props['content_type'] = 'image'
        base_props['is_placeholder'] = True
        return base_props
    
    if hasattr(shape, 'text_frame') and shape.has_text_frame:
        text_frame = shape.text_frame
        
        base_props['content_type'] = 'text'
        base_props['is_placeholder'] = True
        
        base_props['text_frame_props'] = {
            'margin_left': text_frame.margin_left if hasattr(text_frame, 'margin_left') else None,
            'margin_right': text_frame.margin_right if hasattr(text_frame, 'margin_right') else None,
            'margin_top': text_frame.margin_top if hasattr(text_frame, 'margin_top') else None,
            'margin_bottom': text_frame.margin_bottom if hasattr(text_frame, 'margin_bottom') else None,
            'word_wrap': text_frame.word_wrap if hasattr(text_frame, 'word_wrap') else None,
            'vertical_anchor': str(text_frame.vertical_anchor) if hasattr(text_frame, 'vertical_anchor') else None,
            'auto_size': str(text_frame.auto_size) if hasattr(text_frame, 'auto_size') else None
        }
        
        if text_frame.paragraphs:
            para = text_frame.paragraphs[0]
            
            base_props['paragraph_props'] = {
                'alignment': str(para.alignment) if hasattr(para, 'alignment') and para.alignment else None,
                'line_spacing': float(para.line_spacing) if hasattr(para, 'line_spacing') and para.line_spacing else None,
                'space_before': para.space_before.pt if hasattr(para, 'space_before') and para.space_before else None,
                'space_after': para.space_after.pt if hasattr(para, 'space_after') and para.space_after else None,
                'level': para.level if hasattr(para, 'level') else 0
            }
            
            if para.runs:
                run = para.runs[0]
                font = run.font
                
                font_props = {}
                if font.name:
                    font_props['name'] = font.name
                if font.size:
                    font_props['size'] = font.size.pt
                if font.bold is not None:
                    font_props['bold'] = font.bold
                if font.italic is not None:
                    font_props['italic'] = font.italic
                if font.underline is not None:
                    font_props['underline'] = bool(font.underline)
                
                if hasattr(font, 'color') and font.color:
                    try:
                        color_info = {}
                        if hasattr(font.color, 'type'):
                            color_info['type'] = str(font.color.type)
                        if hasattr(font.color, 'rgb') and font.color.rgb:
                            color_info['rgb'] = str(font.color.rgb)
                        if hasattr(font.color, 'theme_color') and font.color.theme_color:
                            color_info['theme_color'] = str(font.color.theme_color)
                        if hasattr(font.color, 'brightness'):
                            color_info['brightness'] = font.color.brightness
                        if color_info:
                            font_props['color'] = color_info
                    except:
                        pass
                
                if font_props:
                    base_props['font_props'] = font_props
    else:
        base_props['content_type'] = 'static'
        base_props['is_placeholder'] = False
    
    if hasattr(shape, 'fill'):
        try:
            fill_props = {}
            fill = shape.fill
            
            if hasattr(fill, 'type'):
                fill_props['type'] = str(fill.type)
            
            if hasattr(fill, 'fore_color') and fill.fore_color:
                fore_color = {}
                try:
                    if hasattr(fill.fore_color, 'rgb') and fill.fore_color.rgb:
                        fore_color['rgb'] = str(fill.fore_color.rgb)
                    if hasattr(fill.fore_color, 'theme_color') and fill.fore_color.theme_color:
                        fore_color['theme_color'] = str(fill.fore_color.theme_color)
                    if hasattr(fill.fore_color, 'brightness'):
                        fore_color['brightness'] = fill.fore_color.brightness
                except:
                    pass
                if fore_color:
                    fill_props['fore_color'] = fore_color
            
            if fill_props:
                base_props['fill_props'] = fill_props
        except:
            pass
    
    if hasattr(shape, 'line'):
        try:
            line_props = {}
            line = shape.line
            
            if hasattr(line, 'width') and line.width:
                line_props['width'] = line.width
            
            if hasattr(line, 'color') and line.color:
                line_color = {}
                try:
                    if hasattr(line.color, 'rgb') and line.color.rgb:
                        line_color['rgb'] = str(line.color.rgb)
                    if hasattr(line.color, 'theme_color') and line.color.theme_color:
                        line_color['theme_color'] = str(line.color.theme_color)
                except:
                    pass
                if line_color:
                    line_props['color'] = line_color
            
            if line_props:
                base_props['line_props'] = line_props
        except:
            pass
    
    if hasattr(shape, 'shadow'):
        try:
            shadow_props = {}
            shadow = shape.shadow
            
            if hasattr(shadow, 'inherit') and shadow.inherit is not None:
                shadow_props['inherit'] = shadow.inherit
            
            if shadow_props:
                base_props['shadow_props'] = shadow_props
        except:
            pass
    
    return base_props


def extract_slide_as_layout(slide, layout_index):
    layout_def = {
        'name': f"slide {layout_index + 1}",
        'original_layout_name': slide.slide_layout.name,
        'layout_index': layout_index,
        'placeholders': [],
        'shapes': []
    }
    
    placeholder_idx = 0
    
    for shape in slide.shapes:
        try:
            shape_props = extract_shape_complete_properties(shape, placeholder_idx)
            
            if shape_props.get('is_placeholder', False):
                layout_def['placeholders'].append({
                    'idx': placeholder_idx,
                    'type': shape_props['content_type'],
                    'name': shape.name,
                    'position': shape_props['position'],
                    'properties': shape_props
                })
                placeholder_idx += 1
            else:
                layout_def['shapes'].append(shape_props)
        
        except Exception as e:
            print(f"  warning: failed to extract shape '{shape.name}': {e}")
            continue
    
    return layout_def


def extract_all_slides_as_layouts(presentation):
    layouts = []
    
    print(f"\nextracting {len(presentation.slides)} slides as layout templates...")
    
    for idx, slide in enumerate(presentation.slides):
        print(f"  extracting slide {idx + 1} ({slide.slide_layout.name})...")
        layout = extract_slide_as_layout(slide, idx)
        
        print(f"    found {len(layout['placeholders'])} content placeholders")
        print(f"    found {len(layout['shapes'])} static shapes")
        
        layouts.append(layout)
    
    return layouts
