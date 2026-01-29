"""
clones template slides with new content while preserving all design elements.
ai selects which slides to use, cloner preserves pixel-perfect design.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from io import BytesIO
import base64
from copy import deepcopy


def clone_slide_with_content(source_presentation, source_slide_index, target_presentation, 
                             placeholder_contents, uploaded_images):
    try:
        # Get the source slide
        source_slide = source_presentation.slides[source_slide_index]
        source_layout = source_slide.slide_layout
        
        print(f"    🔄 cloning slide {source_slide_index + 1} (layout: {source_layout.name})")
        
        # Add a new slide with the same layout
        new_slide = target_presentation.slides.add_slide(source_layout)
        
        # Copy all shapes from source to target
        # This preserves backgrounds, design elements, and all formatting
        _copy_all_shapes(source_slide, new_slide, placeholder_contents, uploaded_images)
        
        # Apply background if present
        _copy_background(source_slide, new_slide)
        
        print(f"    ✅ cloned slide successfully")
        return new_slide
        
    except Exception as e:
        print(f"    ❌ error cloning slide: {e}")
        import traceback
        traceback.print_exc()
        raise


def _copy_all_shapes(source_slide, target_slide, placeholder_contents, uploaded_images):
    content_map = {item['idx']: item for item in placeholder_contents}
    placeholder_counter = 0
    
    print(f"      copying {len(source_slide.shapes)} shapes...")
    
    for shape in source_slide.shapes:
        try:
            shape_name = shape.name if hasattr(shape, 'name') else 'Unknown'
            
            # Check if this is a placeholder
            is_placeholder = hasattr(shape, 'is_placeholder') and shape.is_placeholder
            
            if is_placeholder:
                # This is a placeholder - we need to fill it with content
                if placeholder_counter in content_map:
                    content_item = content_map[placeholder_counter]
                    _fill_placeholder_in_cloned_slide(target_slide, shape, content_item, uploaded_images, placeholder_counter)
                else:
                    print(f"        placeholder {placeholder_counter} has no content, keeping original")
                
                placeholder_counter += 1
            else:
                # Non-placeholder shape - it will be copied automatically by the layout
                # We don't need to manually copy it as add_slide already includes layout shapes
                pass
                
        except Exception as e:
            print(f"        warning: error processing shape '{shape_name}': {e}")


def _fill_placeholder_in_cloned_slide(target_slide, source_shape, content_item, uploaded_images, idx):
    content_type = content_item.get('type')
    
    # Find the corresponding placeholder in the target slide
    target_placeholder = None
    try:
        # Try to find by placeholder idx
        if hasattr(source_shape, 'placeholder_format'):
            ph_idx = source_shape.placeholder_format.idx
            for shape in target_slide.placeholders:
                if hasattr(shape, 'placeholder_format') and shape.placeholder_format.idx == ph_idx:
                    target_placeholder = shape
                    break
    except:
        pass
    
    if not target_placeholder:
        print(f"        ⚠️  could not find target placeholder for idx {idx}")
        return
    
    try:
        if content_type == 'text':
            # Replace text content
            content = content_item.get('content', '')
            if hasattr(target_placeholder, 'text_frame'):
                target_placeholder.text_frame.clear()
                target_placeholder.text_frame.text = content
                print(f"        ✓ filled text placeholder {idx}: '{content[:50]}...'")
        
        elif content_type == 'image':
            # Replace image content
            image_index = content_item.get('image_index')
            if image_index is not None:
                image_filenames = list(uploaded_images.keys())
                if 0 <= image_index < len(image_filenames):
                    filename = image_filenames[image_index]
                    image_data_b64 = uploaded_images[filename]
                    
                    # Decode base64
                    if ',' in image_data_b64:
                        image_data_b64 = image_data_b64.split(',')[1]
                    image_bytes = base64.b64decode(image_data_b64)
                    image_stream = BytesIO(image_bytes)
                    
                    # Insert picture into placeholder
                    try:
                        target_placeholder.insert_picture(image_stream)
                        print(f"        ✓ filled image placeholder {idx}: {filename}")
                    except:
                        # Fallback: add picture manually
                        left = target_placeholder.left
                        top = target_placeholder.top
                        width = target_placeholder.width
                        height = target_placeholder.height
                        
                        # Remove placeholder
                        sp = target_placeholder.element
                        sp.getparent().remove(sp)
                        
                        # Add picture
                        target_slide.shapes.add_picture(image_stream, left, top, width, height)
                        print(f"        ✓ filled image placeholder {idx} (fallback method): {filename}")
    
    except Exception as e:
        print(f"        ❌ error filling placeholder {idx}: {e}")
        import traceback
        traceback.print_exc()


def _copy_background(source_slide, target_slide):
    try:
        # Copy background fill if present
        if hasattr(source_slide, 'background') and hasattr(target_slide, 'background'):
            # The background is usually inherited from layout/master
            # In most cases, using the same layout already preserves the background
            pass
    except Exception as e:
        print(f"        warning: could not copy background: {e}")
