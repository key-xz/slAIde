import base64
from io import BytesIO
from pptx.util import Pt, Inches
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.dml.color import RGBColor


def apply_text_frame_properties(text_frame, props):
    if not props:
        return
    
    try:
        if 'margin_left' in props and props['margin_left'] is not None:
            text_frame.margin_left = props['margin_left']
        if 'margin_right' in props and props['margin_right'] is not None:
            text_frame.margin_right = props['margin_right']
        if 'margin_top' in props and props['margin_top'] is not None:
            text_frame.margin_top = props['margin_top']
        if 'margin_bottom' in props and props['margin_bottom'] is not None:
            text_frame.margin_bottom = props['margin_bottom']
        if 'word_wrap' in props and props['word_wrap'] is not None:
            text_frame.word_wrap = props['word_wrap']
        if 'vertical_anchor' in props and props['vertical_anchor']:
            anchor_str = props['vertical_anchor']
            if 'TOP' in anchor_str:
                text_frame.vertical_anchor = MSO_ANCHOR.TOP
            elif 'MIDDLE' in anchor_str:
                text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            elif 'BOTTOM' in anchor_str:
                text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
    except Exception as e:
        print(f"    warning: failed to apply text frame props: {e}")


def apply_paragraph_properties(paragraph, props):
    if not props:
        return
    
    try:
        if 'alignment' in props and props['alignment']:
            align_str = props['alignment']
            if 'LEFT' in align_str:
                paragraph.alignment = PP_ALIGN.LEFT
            elif 'CENTER' in align_str:
                paragraph.alignment = PP_ALIGN.CENTER
            elif 'RIGHT' in align_str:
                paragraph.alignment = PP_ALIGN.RIGHT
            elif 'JUSTIFY' in align_str:
                paragraph.alignment = PP_ALIGN.JUSTIFY
        
        if 'line_spacing' in props and props['line_spacing']:
            paragraph.line_spacing = props['line_spacing']
        
        if 'space_before' in props and props['space_before']:
            paragraph.space_before = Pt(props['space_before'])
        
        if 'space_after' in props and props['space_after']:
            paragraph.space_after = Pt(props['space_after'])
        
        if 'level' in props:
            paragraph.level = props['level']
    except Exception as e:
        print(f"    warning: failed to apply paragraph props: {e}")


def apply_font_properties(font, props):
    if not props:
        return
    
    try:
        if 'name' in props:
            font.name = props['name']
        
        if 'size' in props:
            font.size = Pt(props['size'])
        
        if 'bold' in props:
            font.bold = props['bold']
        
        if 'italic' in props:
            font.italic = props['italic']
        
        if 'underline' in props:
            font.underline = props['underline']
        
        if 'color' in props:
            color_info = props['color']
            if 'rgb' in color_info:
                rgb_str = color_info['rgb']
                if rgb_str and len(rgb_str) >= 6:
                    r = int(rgb_str[0:2], 16)
                    g = int(rgb_str[2:4], 16)
                    b = int(rgb_str[4:6], 16)
                    font.color.rgb = RGBColor(r, g, b)
    except Exception as e:
        print(f"    warning: failed to apply font props: {e}")


def apply_fill_properties(shape, props):
    if not props:
        return
    
    try:
        if 'type' in props and 'SOLID' in props['type']:
            shape.fill.solid()
            
            if 'fore_color' in props:
                fore_color = props['fore_color']
                if 'rgb' in fore_color:
                    rgb_str = fore_color['rgb']
                    if rgb_str and len(rgb_str) >= 6:
                        r = int(rgb_str[0:2], 16)
                        g = int(rgb_str[2:4], 16)
                        b = int(rgb_str[4:6], 16)
                        shape.fill.fore_color.rgb = RGBColor(r, g, b)
    except Exception as e:
        print(f"    warning: failed to apply fill props: {e}")


def apply_line_properties(shape, props):
    if not props:
        return
    
    try:
        if 'width' in props:
            shape.line.width = props['width']
        
        if 'color' in props:
            line_color = props['color']
            if 'rgb' in line_color:
                rgb_str = line_color['rgb']
                if rgb_str and len(rgb_str) >= 6:
                    r = int(rgb_str[0:2], 16)
                    g = int(rgb_str[2:4], 16)
                    b = int(rgb_str[4:6], 16)
                    shape.line.color.rgb = RGBColor(r, g, b)
    except Exception as e:
        print(f"    warning: failed to apply line props: {e}")


def create_text_shape(slide, shape_props, content):
    pos = shape_props['position']
    left = pos['left']
    top = pos['top']
    width = pos['width']
    height = pos['height']
    
    # Check if this was originally a placeholder
    real_idx = shape_props.get('placeholder_idx', -1)
    
    # If it's a placeholder, we should try to add it as one if possible
    # but add_textbox is more reliable for exact positioning
    textbox = slide.shapes.add_textbox(left, top, width, height)
    text_frame = textbox.text_frame
    
    # Strictly enforce word wrap and margins from template
    if 'text_frame_props' in shape_props:
        apply_text_frame_properties(text_frame, shape_props['text_frame_props'])
    
    text_frame.clear()
    p = text_frame.paragraphs[0]
    
    # Strictly enforce paragraph alignment and spacing
    if 'paragraph_props' in shape_props:
        apply_paragraph_properties(p, shape_props['paragraph_props'])
    
    run = p.add_run()
    run.text = content
    
    # Strictly enforce font name, size, color, bold, italic
    if 'font_props' in shape_props:
        apply_font_properties(run.font, shape_props['font_props'])
    
    # Strictly enforce fill and line (border)
    if 'fill_props' in shape_props:
        apply_fill_properties(textbox, shape_props['fill_props'])
    
    if 'line_props' in shape_props:
        apply_line_properties(textbox, shape_props['line_props'])
    
    if 'rotation' in shape_props:
        textbox.rotation = shape_props['rotation']
    
    return textbox


def create_image_shape(slide, shape_props, image_data):
    pos = shape_props['position']
    left = pos['left']
    top = pos['top']
    width = pos['width']
    height = pos['height']
    
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    image_bytes = base64.b64decode(image_data)
    image_stream = BytesIO(image_bytes)
    
    picture = slide.shapes.add_picture(image_stream, left, top, width, height)
    
    if 'rotation' in shape_props:
        picture.rotation = shape_props['rotation']
    
    return picture


def create_static_shape(slide, shape_props):
    shape_type_str = shape_props.get('shape_type', '')
    pos = shape_props['position']
    left = pos['left']
    top = pos['top']
    width = pos['width']
    height = pos['height']
    
    # Map string shape type to MSO_SHAPE_TYPE if possible
    # This is a bit tricky as shape_type is stored as a string like 'PICTURE (13)'
    
    if 'PICTURE' in shape_type_str:
        # We don't have the original image data for static pictures easily
        # but we can try to add a placeholder or skip
        return None
        
    # Default to a rectangle for unknown shapes, or specific ones if we can identify them
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, left, top, width, height)
    
    if 'fill_props' in shape_props:
        apply_fill_properties(shape, shape_props['fill_props'])
    if 'line_props' in shape_props:
        apply_line_properties(shape, shape_props['line_props'])
    if 'rotation' in shape_props:
        shape.rotation = shape_props['rotation']
        
    # If it has text, add it
    if shape_props.get('content_type') == 'text' and 'text_frame_props' in shape_props:
        # Static text
        pass # To be implemented if needed
        
    return shape


def generate_slide_from_template(presentation, layout_template, placeholder_contents, uploaded_images):
    # Use the layout index to get the actual layout from the template
    layout_idx = layout_template.get('layout_index', 0)
    
    # Try to find the corresponding slide layout in the presentation
    if layout_idx < len(presentation.slide_layouts):
        slide_layout = presentation.slide_layouts[layout_idx]
    else:
        slide_layout = presentation.slide_layouts[0]
        
    slide = presentation.slides.add_slide(slide_layout)
    
    # Map of real PPTX idx to placeholder shape on the new slide
    placeholder_map = {}
    for shape in slide.placeholders:
        placeholder_map[shape.placeholder_format.idx] = shape
    
    # Remove all default shapes from the new slide to start with a clean slate
    # but keep the background from the layout
    for shape in list(slide.shapes):
        sp = shape.element
        sp.getparent().remove(sp)
    
    content_map = {item['idx']: item for item in placeholder_contents}
    
    # 1. Create all placeholders (text and image)
    for placeholder_def in layout_template['placeholders']:
        idx = placeholder_def['idx']
        real_pptx_idx = placeholder_def.get('real_pptx_idx')
        ph_type = placeholder_def['type']
        shape_props = placeholder_def['properties']
        
        if idx not in content_map:
            print(f"    warning: no content for placeholder idx={idx}")
            continue
        
        content_item = content_map[idx]
        
        # Deterministically use the position and sizing from shape_props
        if ph_type == 'text' and content_item.get('type') == 'text':
            content = content_item.get('content', '')
            print(f"    creating text placeholder idx={idx} (real_idx={real_pptx_idx}): {content[:50]}...")
            create_text_shape(slide, shape_props, content)
        
        elif ph_type == 'image' and content_item.get('type') == 'image':
            image_index = content_item.get('image_index')
            if image_index is not None:
                image_filenames = list(uploaded_images.keys())
                if 0 <= image_index < len(image_filenames):
                    filename = image_filenames[image_index]
                    image_data = uploaded_images[filename]
                    print(f"    creating image placeholder idx={idx} (real_idx={real_pptx_idx}): {filename}")
                    create_image_shape(slide, shape_props, image_data)
                else:
                    print(f"    error: image_index {image_index} out of range")
            else:
                print(f"    error: no image_index for image placeholder")
    
    # 2. Create all static shapes from the template slide
    for static_shape_props in layout_template.get('shapes', []):
        create_static_shape(slide, static_shape_props)
    
    return slide
