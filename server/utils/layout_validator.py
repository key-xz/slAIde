def analyze_layouts(layouts):
    """analyze available layouts and their capabilities"""
    
    text_only_layouts = []
    image_layouts = []
    mixed_layouts = []
    
    total_text_placeholders = 0
    total_image_placeholders = 0
    
    for layout in layouts:
        placeholders = layout.get('placeholders', [])
        
        has_text = any(ph['type'] == 'text' for ph in placeholders)
        has_image = any(ph['type'] == 'image' for ph in placeholders)
        
        text_count = sum(1 for ph in placeholders if ph['type'] == 'text')
        image_count = sum(1 for ph in placeholders if ph['type'] == 'image')
        
        total_text_placeholders += text_count
        total_image_placeholders += image_count
        
        if has_text and has_image:
            mixed_layouts.append({
                'name': layout['name'],
                'text_slots': text_count,
                'image_slots': image_count
            })
        elif has_text:
            text_only_layouts.append({
                'name': layout['name'],
                'text_slots': text_count
            })
        elif has_image:
            image_layouts.append({
                'name': layout['name'],
                'image_slots': image_count
            })
    
    return {
        'text_only_layouts': text_only_layouts,
        'image_layouts': image_layouts,
        'mixed_layouts': mixed_layouts,
        'total_text_placeholders': total_text_placeholders,
        'total_image_placeholders': total_image_placeholders,
        'total_layouts': len(layouts)
    }


def validate_content_feasibility(layouts, num_images, has_text_content):
    """
    validate that the provided content can be generated using available layouts.
    returns (is_valid, error_message)
    """
    
    if not layouts:
        return False, "no layouts available. please upload a template presentation first."
    
    analysis = analyze_layouts(layouts)
    
    if num_images > 0:
        if analysis['total_image_placeholders'] == 0:
            return False, (
                f"cannot generate presentation: {num_images} image(s) uploaded, "
                f"but the template has no layouts with image placeholders. "
                f"please use a template that includes slides with images."
            )
        
        if num_images > analysis['total_image_placeholders']:
            return False, (
                f"cannot generate presentation: {num_images} image(s) uploaded, "
                f"but template only has {analysis['total_image_placeholders']} image placeholder(s) total. "
                f"please either upload fewer images or use a template with more image placeholders."
            )
        
        if not has_text_content:
            if len(analysis['image_layouts']) == 0 and len(analysis['mixed_layouts']) == 0:
                return False, (
                    f"cannot generate presentation: images uploaded but no text content provided, "
                    f"and template has no image-only or mixed layouts available."
                )
    
    else:
        if analysis['total_text_placeholders'] == 0:
            return False, (
                f"cannot generate presentation: no images uploaded, "
                f"but template has no text-only layouts. "
                f"please either upload images or use a template with text placeholders."
            )
        
        if len(analysis['text_only_layouts']) == 0 and len(analysis['mixed_layouts']) == 0:
            if has_text_content:
                return False, (
                    f"cannot generate presentation: text content provided but no images uploaded, "
                    f"and template has no text-only or mixed layouts. "
                    f"please upload images to match the template's requirements."
                )
    
    if has_text_content and analysis['total_text_placeholders'] == 0:
        return False, (
            f"cannot generate presentation: text content provided, "
            f"but template has no text placeholders available."
        )
    
    return True, None


def get_feasibility_summary(layouts, num_images):
    """get a human-readable summary of what can be generated"""
    
    analysis = analyze_layouts(layouts)
    
    summary = []
    summary.append(f"template analysis:")
    summary.append(f"  - {analysis['total_layouts']} layout(s) available")
    summary.append(f"  - {len(analysis['text_only_layouts'])} text-only layout(s)")
    summary.append(f"  - {len(analysis['image_layouts'])} image-only layout(s)")
    summary.append(f"  - {len(analysis['mixed_layouts'])} mixed (text+image) layout(s)")
    summary.append(f"  - {analysis['total_text_placeholders']} total text placeholder(s)")
    summary.append(f"  - {analysis['total_image_placeholders']} total image placeholder(s)")
    summary.append(f"\ninput provided:")
    summary.append(f"  - {num_images} image(s) uploaded")
    
    if num_images > 0:
        summary.append(f"\nrequirements:")
        summary.append(f"  - must use all {num_images} image(s)")
        summary.append(f"  - need layouts with at least {num_images} image placeholder(s)")
        summary.append(f"  - text content will be generated to accompany images")
    else:
        summary.append(f"\nrequirements:")
        summary.append(f"  - no images to place")
        summary.append(f"  - can only use text-only layouts")
        summary.append(f"  - all slides will be text-based")
    
    return '\n'.join(summary)
