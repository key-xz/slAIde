def extract_color(color):
    if color is None:
        return None
    
    try:
        if hasattr(color, 'rgb') and color.rgb:
            return {
                'type': 'rgb',
                'value': str(color.rgb)
            }
        elif hasattr(color, 'theme_color') and color.theme_color:
            return {
                'type': 'theme',
                'value': str(color.theme_color)
            }
    except:
        pass
    return None


def extract_font_properties(font):
    if font is None:
        return {}
    
    props = {}
    try:
        if font.name:
            props['name'] = font.name
        if font.size:
            props['size'] = font.size.pt
        if font.bold is not None:
            props['bold'] = font.bold
        if font.italic is not None:
            props['italic'] = font.italic
        if font.underline is not None:
            props['underline'] = bool(font.underline)
        if hasattr(font, 'color') and font.color:
            props['color'] = extract_color(font.color)
    except:
        pass
    return props


def extract_fill_properties(fill):
    if fill is None:
        return {}
    
    props = {}
    try:
        if hasattr(fill, 'type'):
            props['type'] = str(fill.type)
        
        if hasattr(fill, 'fore_color') and fill.fore_color:
            props['fore_color'] = extract_color(fill.fore_color)
        
        if hasattr(fill, 'back_color') and fill.back_color:
            props['back_color'] = extract_color(fill.back_color)
    except:
        pass
    return props


def extract_shape_properties(shape):
    props = {
        'type': str(shape.shape_type),
        'name': shape.name,
        'position': {
            'left': shape.left,
            'top': shape.top,
            'width': shape.width,
            'height': shape.height
        }
    }
    
    if hasattr(shape, 'fill'):
        props['fill'] = extract_fill_properties(shape.fill)
    
    if hasattr(shape, 'line'):
        try:
            line_props = {}
            if shape.line.color:
                line_props['color'] = extract_color(shape.line.color)
            if hasattr(shape.line, 'width') and shape.line.width:
                line_props['width'] = shape.line.width
            if line_props:
                props['line'] = line_props
        except:
            pass
    
    if hasattr(shape, 'text_frame') and shape.has_text_frame:
        text_props = {
            'text': shape.text,
            'paragraphs': []
        }
        
        for paragraph in shape.text_frame.paragraphs:
            para_props = {
                'alignment': str(paragraph.alignment) if paragraph.alignment else None,
                'level': paragraph.level,
                'runs': []
            }
            
            for run in paragraph.runs:
                run_props = {
                    'text': run.text,
                    'font': extract_font_properties(run.font)
                }
                para_props['runs'].append(run_props)
            
            text_props['paragraphs'].append(para_props)
        
        props['text_frame'] = text_props
    
    return props


def extract_slide_layout_properties(slide_layout):
    return {
        'name': slide_layout.name,
        'placeholders': [
            {
                'type': str(ph.placeholder_format.type),
                'idx': ph.placeholder_format.idx,
                'position': {
                    'left': ph.left,
                    'top': ph.top,
                    'width': ph.width,
                    'height': ph.height
                }
            }
            for ph in slide_layout.placeholders
        ]
    }


def extract_master_properties(slide_master):
    return {
        'name': slide_master.name if hasattr(slide_master, 'name') else 'Master',
        'layouts': [
            extract_slide_layout_properties(layout)
            for layout in slide_master.slide_layouts
        ]
    }
