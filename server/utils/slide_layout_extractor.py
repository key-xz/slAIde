import base64
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER


def extract_shape_complete_properties(shape, default_font=None):
    """
    extracts all relevant properties from a shape.
    treats all text boxes and images as content areas for google slides compatibility.
    """
    if default_font is None:
        default_font = {'name': 'Calibri', 'size': 18}
    
    shape_type = shape.shape_type
    
    # check if it's a placeholder
    is_placeholder = False
    real_idx = -1
    
    try:
        if hasattr(shape, 'is_placeholder') and shape.is_placeholder:
            is_placeholder = True
            if hasattr(shape, 'placeholder_format'):
                real_idx = shape.placeholder_format.idx
    except:
        pass
    
    base_props = {
        'placeholder_idx': real_idx,
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
    
    # determine content type
    if shape_type == MSO_SHAPE_TYPE.PICTURE:
        base_props['content_type'] = 'image'
        base_props['is_placeholder'] = True
        try:
            base_props['image_data'] = base64.b64encode(shape.image.blob).decode('utf-8')
        except:
            pass
        return base_props
    
    if hasattr(shape, 'text_frame'):
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
            print(f"      shape '{shape.name}' has {len(text_frame.paragraphs)} paragraph(s)")
            
            base_props['paragraph_props'] = {
                'alignment': str(para.alignment) if hasattr(para, 'alignment') and para.alignment else None,
                'line_spacing': float(para.line_spacing) if hasattr(para, 'line_spacing') and para.line_spacing else None,
                'space_before': para.space_before.pt if hasattr(para, 'space_before') and para.space_before else None,
                'space_after': para.space_after.pt if hasattr(para, 'space_after') and para.space_after else None,
                'level': para.level if hasattr(para, 'level') else 0
            }
            
            had_runs = len(para.runs) > 0
            if para.runs:
                print(f"      paragraph has {len(para.runs)} run(s)")
            else:
                print(f"      ✗ paragraph has NO runs - will try to add dummy text")
                try:
                    dummy_run = para.add_run()
                    dummy_run.text = "X"
                    print(f"      ✓ added dummy run to extract font properties")
                except Exception as e:
                    print(f"      ✗ failed to add dummy run: {e}")
            
            if para.runs:
                run = para.runs[0]
                font = run.font
                
                font_props = {}
                
                try:
                    name = font.name
                    print(f"        font.name value: {repr(name)} (type: {type(name).__name__})")
                    if name:
                        font_props['name'] = name
                        print(f"        ✓ extracted font.name: {name}")
                    else:
                        font_props['name'] = default_font['name']
                        print(f"        → using default font.name from master: {default_font['name']}")
                except Exception as e:
                    print(f"        ✗ error getting font.name: {e}")
                    font_props['name'] = default_font['name']
                
                try:
                    size = font.size
                    print(f"        font.size value: {repr(size)} (type: {type(size).__name__ if size else 'NoneType'})")
                    if size:
                        size_pt = size.pt
                        font_props['size'] = size_pt
                        print(f"        ✓ extracted font.size: {size_pt}pt")
                    else:
                        font_props['size'] = default_font['size']
                        print(f"        → using default font.size from master: {default_font['size']}pt")
                except Exception as e:
                    print(f"        ✗ error getting font.size: {e}")
                    font_props['size'] = default_font['size']
                
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
                            rgb_obj = font.color.rgb
                            rgb_hex = format(rgb_obj[0], '02X') + format(rgb_obj[1], '02X') + format(rgb_obj[2], '02X')
                            color_info['rgb'] = rgb_hex
                        if hasattr(font.color, 'theme_color') and font.color.theme_color:
                            color_info['theme_color'] = str(font.color.theme_color)
                        if hasattr(font.color, 'brightness') and font.color.brightness is not None:
                            color_info['brightness'] = font.color.brightness
                        if color_info:
                            font_props['color'] = color_info
                    except Exception as e:
                        print(f"    warning: failed to extract font color: {e}")
                        pass
                
                if font_props:
                    base_props['font_props'] = font_props
                    font_summary = []
                    if 'name' in font_props:
                        font_summary.append(f"font={font_props['name']}")
                    if 'size' in font_props:
                        font_summary.append(f"size={font_props['size']}pt")
                    if 'color' in font_props and 'rgb' in font_props['color']:
                        font_summary.append(f"color=#{font_props['color']['rgb']}")
                    if font_summary:
                        print(f"      ✓ extracted font: {', '.join(font_summary)}")
                
                if not had_runs and para.runs:
                    try:
                        para.clear()
                        print(f"      ✓ cleaned up dummy run")
                    except:
                        pass
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


def get_default_fonts_from_master(slide):
    """
    extracts default font properties from the slide master/theme.
    returns both title and body fonts.
    """
    result = {
        'title': {'name': 'Calibri', 'size': 44},
        'body': {'name': 'Calibri', 'size': 18}
    }
    
    try:
        slide_layout = slide.slide_layout
        slide_master = slide_layout.slide_master
        
        print(f"      attempting to extract fonts from master slide...")
        
        # try method 1: theme font scheme
        if hasattr(slide_master, 'theme') and slide_master.theme:
            theme = slide_master.theme
            print(f"      found theme: {theme}")
            if hasattr(theme, 'font_scheme') and theme.font_scheme:
                font_scheme = theme.font_scheme
                print(f"      found font_scheme: {font_scheme}")
                
                # get major (heading/title) font
                if hasattr(font_scheme, 'major_font') and font_scheme.major_font:
                    major_font = font_scheme.major_font
                    print(f"      major_font attributes: {dir(major_font)}")
                    if hasattr(major_font, 'latin') and major_font.latin:
                        result['title']['name'] = major_font.latin
                        print(f"      ✓ extracted theme title font: {major_font.latin}")
                
                # get minor (body) font
                if hasattr(font_scheme, 'minor_font') and font_scheme.minor_font:
                    minor_font = font_scheme.minor_font
                    print(f"      minor_font attributes: {dir(minor_font)}")
                    if hasattr(minor_font, 'latin') and minor_font.latin:
                        result['body']['name'] = minor_font.latin
                        print(f"      ✓ extracted theme body font: {minor_font.latin}")
        
        # try method 2: extract from actual text in master slide placeholders
        if result['title']['name'] == 'Calibri' or result['body']['name'] == 'Calibri':
            print(f"      theme fonts not found, trying to extract from master slide shapes...")
            for shape in slide_master.shapes:
                if hasattr(shape, 'text_frame') and shape.text_frame:
                    if shape.text_frame.paragraphs:
                        para = shape.text_frame.paragraphs[0]
                        if not para.runs:
                            para.add_run().text = "X"
                        if para.runs:
                            font = para.runs[0].font
                            font_name = font.name
                            font_size = font.size.pt if font.size else None
                            
                            if font_name:
                                # assume top shapes are title, bottom are body
                                if shape.top < (5143500 * 0.2):
                                    result['title']['name'] = font_name
                                    if font_size:
                                        result['title']['size'] = font_size
                                    print(f"      ✓ extracted title font from master shape: {font_name} {font_size}pt")
                                else:
                                    result['body']['name'] = font_name
                                    if font_size:
                                        result['body']['size'] = font_size
                                    print(f"      ✓ extracted body font from master shape: {font_name} {font_size}pt")
                                break
        
    except Exception as e:
        print(f"      warning: failed to extract theme fonts: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def extract_slide_as_layout(slide, layout_index):
    """
    extracts layout from a slide, treating all text boxes and images as content areas.
    """
    slide_layout = slide.slide_layout
    layout_name = slide_layout.name
    
    default_fonts = get_default_fonts_from_master(slide)
    print(f"  default fonts from master - title: {default_fonts['title']}, body: {default_fonts['body']}")
    
    # try to find better name if it's just "blank"
    if layout_name.lower() == 'blank':
        for shape in slide.shapes:
            try:
                if hasattr(shape, 'text_frame') and shape.text_frame.text.strip():
                    layout_name = shape.text_frame.text.strip()[:30]
                    break
            except:
                pass
    
    layout_def = {
        'name': f"{layout_name} (slide {layout_index + 1})",
        'original_layout_name': layout_name,
        'layout_index': layout_index,
        'placeholders': [],
        'shapes': []
    }
    
    internal_counter = 0
    
    for shape in slide.shapes:
        try:
            # determine if this is likely a title based on position
            # typical slide height is around 5143500 EMUs
            # use top 20% as title area (about 1028700 EMUs)
            try:
                slide_height = 5143500  # standard 16:9 slide height in EMUs
                is_likely_title = shape.top < (slide_height * 0.2)
            except:
                is_likely_title = False
            
            default_font = default_fonts['title'] if is_likely_title else default_fonts['body']
            print(f"      shape '{shape.name}' at y={shape.top}, using {'title' if is_likely_title else 'body'} font defaults")
            shape_props = extract_shape_complete_properties(shape, default_font)
            
            # all text frames and images are content areas
            if shape_props.get('is_placeholder', False):
                layout_def['placeholders'].append({
                    'idx': internal_counter,
                    'real_pptx_idx': shape_props['placeholder_idx'],
                    'type': shape_props['content_type'],
                    'name': shape.name,
                    'position': shape_props['position'],
                    'properties': shape_props
                })
                internal_counter += 1
            else:
                layout_def['shapes'].append(shape_props)
        
        except Exception as e:
            print(f"  warning: failed to extract shape '{shape.name}': {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return layout_def


def extract_all_slides_as_layouts(presentation):
    """
    extracts layouts from all slides in presentation.
    """
    layouts = []
    print(f"\nextracting {len(presentation.slides)} slides as layout templates...")
    
    for idx, slide in enumerate(presentation.slides):
        print(f"  extracting slide {idx + 1} ({slide.slide_layout.name})...")
        layout = extract_slide_as_layout(slide, idx)
        
        print(f"    found {len(layout['placeholders'])} content areas")
        print(f"    found {len(layout['shapes'])} static shapes")
        
        layouts.append(layout)
    
    return layouts
