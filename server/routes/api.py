from flask import Blueprint, request, jsonify
from services import PPTXService, AIService
from utils.layout_validator import validate_content_feasibility, get_feasibility_summary

api_blueprint = Blueprint('api', __name__, url_prefix='/api')
pptx_service = PPTXService()
ai_service = None

def get_ai_service():
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service


@api_blueprint.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@api_blueprint.route('/extract-rules', methods=['POST'])
def extract_rules():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pptx'):
        return jsonify({'error': 'File must be a .pptx file'}), 400
    
    try:
        rules = pptx_service.extract_rules_from_file(file)
        return jsonify(rules)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/rules', methods=['GET'])
def get_rules():
    try:
        rules = pptx_service.get_stored_rules()
        return jsonify(rules)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/toggle-layout-special', methods=['POST'])
def toggle_layout_special():
    """toggle whether a layout is marked as special"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        layout_name = request_data.get('layout_name')
        is_special = request_data.get('is_special', False)
        
        if not layout_name:
            return jsonify({'error': 'layout_name is required'}), 400
        
        rules = pptx_service.get_stored_rules()
        layouts = rules.get('layouts', [])
        
        found = False
        for layout in layouts:
            if layout['name'] == layout_name:
                layout['is_special'] = is_special
                found = True
                break
        
        if not found:
            return jsonify({'error': f'Layout "{layout_name}" not found'}), 404
        
        rules['layouts'] = layouts
        pptx_service.update_stored_rules(rules)
        
        return jsonify({
            'success': True,
            'message': f'Layout marked as {"special" if is_special else "general"}'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/intelligent-chunk', methods=['POST'])
def intelligent_chunk():
    """ai-driven intelligent chunking: creates slide-ready chunks from raw text + images + layouts"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        raw_text = request_data.get('raw_text', '')
        images = request_data.get('images', [])
        
        if not raw_text or not raw_text.strip():
            return jsonify({'error': 'Raw text is required'}), 400
        
        rules = pptx_service.get_stored_rules()
        layouts = rules.get('layouts', [])
        
        if not layouts:
            return jsonify({'error': 'No layouts available. Please upload a template first.'}), 400
        
        result = get_ai_service().intelligent_chunk_with_layouts(
            raw_text=raw_text,
            images=images,
            layouts=layouts,
            slide_size=rules.get('slide_size')
        )
        
        return jsonify({
            'success': True,
            'structure': result.get('structure', []),
            'deck_summary': result.get('deck_summary', {})
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/preprocess-content', methods=['POST'])
def preprocess_content():
    """Preprocess raw content into structured slide outlines with comprehensive information organization"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        content_chunks = request_data.get('content_chunks', None)
        images = request_data.get('images', [])
        provided_layouts = request_data.get('layouts', None)
        
        rules = pptx_service.get_stored_rules()
        layouts = provided_layouts if provided_layouts is not None else rules.get('layouts', [])
        
        if not layouts:
            return jsonify({'error': 'No layouts available. Please upload a template first.'}), 400
        
        if content_chunks is not None:
            if not isinstance(content_chunks, list) or len(content_chunks) == 0:
                return jsonify({'error': 'Content chunks must be a non-empty array'}), 400
            
            if not isinstance(images, list):
                return jsonify({'error': 'Images must be an array'}), 400
            
            for i, chunk in enumerate(content_chunks):
                if not isinstance(chunk, dict):
                    return jsonify({'error': f'Chunk {i} must be an object'}), 400
                if 'id' not in chunk or 'text' not in chunk or 'linked_image_ids' not in chunk:
                    return jsonify({'error': f'Chunk {i} missing required fields (id, text, linked_image_ids)'}), 400
                
                for img_id in chunk['linked_image_ids']:
                    if not any(img.get('id') == img_id for img in images):
                        return jsonify({'error': f'Chunk {i} references non-existent image ID: {img_id}'}), 400
            
            for i, img in enumerate(images):
                if not isinstance(img, dict):
                    return jsonify({'error': f'Image {i} must be an object'}), 400
                if 'id' not in img or 'filename' not in img or 'tags' not in img:
                    return jsonify({'error': f'Image {i} missing required fields (id, filename, tags)'}), 400
            
            structure = get_ai_service().preprocess_with_chunks_and_links(
                content_chunks=content_chunks,
                images=images,
                layouts=layouts,
                slide_size=rules.get('slide_size')
            )
        else:
            content_text = request_data.get('content_text', '')
            num_images = request_data.get('num_images', 0)
            
            if not content_text or not content_text.strip():
                return jsonify({'error': 'Content text is required'}), 400
            
            structure = get_ai_service().preprocess_content_structure(
                content_text=content_text,
                layouts=layouts,
                num_images=num_images,
                slide_size=rules.get('slide_size')
            )
        
        return jsonify({
            'success': True,
            'structure': structure
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/preview-slides', methods=['POST'])
def preview_slides():
    """Generate slide specifications from structured content"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        structured_content = request_data.get('structured_content', None)
        images = request_data.get('images', [])
        
        if not structured_content:
            return jsonify({'error': 'Structured content is required'}), 400
        
        if not isinstance(images, list):
            return jsonify({'error': 'Images must be an array'}), 400
        
        rules = pptx_service.get_stored_rules()
        layouts = rules.get('layouts', [])
        
        if not layouts:
            return jsonify({'error': 'No layouts available. Please upload a template first.'}), 400
        
        # Validate structured content
        if 'structure' not in structured_content:
            return jsonify({'error': 'Invalid structured content format'}), 400
        
        slides = structured_content['structure']
        
        pptx_service.clear_images()
        image_id_to_index = {}
        for i, img in enumerate(images):
            if not isinstance(img, dict):
                return jsonify({'error': f'Image {i} must be an object with filename and data'}), 400
            
            img_id = img.get('id')
            filename = img.get('filename')
            image_data = img.get('data')
            
            if not filename or not image_data:
                return jsonify({'error': f'Image {i} missing filename or data'}), 400
            
            pptx_service.store_image(filename, image_data)
            
            if img_id:
                image_id_to_index[img_id] = i
        
        for i, slide in enumerate(slides):
            if 'layout_name' not in slide:
                return jsonify({'error': f'Slide {i+1} missing layout_name'}), 400
            
            if 'placeholders' not in slide or not slide['placeholders']:
                return jsonify({'error': f'Slide {i+1} missing placeholders'}), 400
            
            # Find matching layout
            layout = next((l for l in layouts if l['name'] == slide['layout_name']), None)
            if not layout:
                return jsonify({'error': f'Slide {i+1}: Layout "{slide["layout_name"]}" not found'}), 400
            
            # Verify all placeholder indices are valid
            layout_placeholder_indices = {ph['idx'] for ph in layout['placeholders']}
            slide_placeholder_indices = {ph['idx'] for ph in slide['placeholders']}
            
            if slide_placeholder_indices != layout_placeholder_indices:
                missing = layout_placeholder_indices - slide_placeholder_indices
                extra = slide_placeholder_indices - layout_placeholder_indices
                
                print(f"\n❌ PLACEHOLDER MISMATCH - Slide {i+1}")
                print(f"   Layout: {slide['layout_name']}")
                print(f"   Expected indices: {sorted(layout_placeholder_indices)}")
                print(f"   Got indices: {sorted(slide_placeholder_indices)}")
                print(f"   Layout placeholders:")
                for ph in layout['placeholders']:
                    print(f"     - idx={ph['idx']}, type={ph['type']}, name={ph['name']}")
                print(f"   Slide placeholders:")
                for ph in slide['placeholders']:
                    print(f"     - idx={ph['idx']}, type={ph['type']}")
                
                error_msg = f'Slide {i+1} placeholder mismatch.'
                if missing:
                    error_msg += f' Missing indices: {sorted(missing)}.'
                if extra:
                    error_msg += f' Extra indices: {sorted(extra)}.'
                return jsonify({'error': error_msg}), 400
        
        # Return slides directly from structured content (1:1 mapping)
        return jsonify({
            'slides': slides
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/generate-deck', methods=['POST'])
def generate_deck():
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        content_text = request_data.get('content_text', '')
        images = request_data.get('images', [])
        slides_spec = request_data.get('slides', [])
        custom_theme = request_data.get('customTheme', None)
        
        if not content_text and not slides_spec:
            return jsonify({'error': 'Either content_text or slides specification is required'}), 400
        
        if content_text and not isinstance(content_text, str):
            return jsonify({'error': 'Content text must be a string'}), 400
        
        if not isinstance(images, list):
            return jsonify({'error': 'Images must be an array'}), 400
        
        if not isinstance(slides_spec, list):
            return jsonify({'error': 'Slides must be an array'}), 400
        
        rules = pptx_service.get_stored_rules()
        layouts = rules.get('layouts', [])
        
        if not layouts:
            return jsonify({'error': 'No layouts available. Please upload a template first.'}), 400
        
        # If slides_spec is provided, use it directly and extract images from it
        if slides_spec:
            # Extract unique image indices from slides_spec
            image_indices = set()
            for slide in slides_spec:
                for placeholder in slide.get('placeholders', []):
                    if placeholder.get('type') == 'image' and 'image_index' in placeholder:
                        image_indices.add(placeholder['image_index'])
            
            # Validate we have all needed images
            if image_indices and images:
                max_image_index = max(image_indices) if image_indices else -1
                if max_image_index >= len(images):
                    return jsonify({'error': f'Image index {max_image_index} referenced but only {len(images)} images provided'}), 400
            
            # Store images
            pptx_service.clear_images()
            for i, img in enumerate(images):
                if not isinstance(img, dict):
                    return jsonify({'error': f'Image {i} must be an object with filename and data'}), 400
                
                filename = img.get('filename')
                image_data = img.get('data')
                
                if not filename or not image_data:
                    return jsonify({'error': f'Image {i} missing filename or data'}), 400
                
                pptx_service.store_image(filename, image_data)
            
            slide_specs = slides_spec
        else:
            num_images = len(images)
            has_text_content = bool(content_text and content_text.strip())
            
            is_valid, error_message = validate_content_feasibility(layouts, num_images, has_text_content)
            
            if not is_valid:
                summary = get_feasibility_summary(layouts, num_images)
                return jsonify({
                    'error': error_message,
                    'template_analysis': summary
                }), 400
            
            pptx_service.clear_images()
            image_filenames = []
            image_data_list = []
            
            for i, img in enumerate(images):
                if not isinstance(img, dict):
                    return jsonify({'error': f'Image {i} must be an object with filename and data'}), 400
                
                filename = img.get('filename')
                image_data = img.get('data')
                
                if not filename or not image_data:
                    return jsonify({'error': f'Image {i} missing filename or data'}), 400
                
                pptx_service.store_image(filename, image_data)
                image_filenames.append(filename)
                image_data_list.append(image_data)
            
            slide_specs = get_ai_service().organize_content_into_slides(
                content_text=content_text,
                image_filenames=image_filenames,
                layouts=layouts,
                image_data_list=image_data_list,
                slides_specification=[]
            )
        
        file_b64 = pptx_service.generate_deck(slide_specs, custom_theme=custom_theme)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(slide_specs)} slides successfully',
            'file': file_b64,
            'slides_count': len(slide_specs)
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/regenerate-slide', methods=['POST'])
def regenerate_slide():
    """regenerate a single slide using AI with access to all layouts"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        slide = request_data.get('slide')
        images = request_data.get('images', [])
        provided_layouts = request_data.get('layouts', None)
        context_slides = request_data.get('context_slides', [])
        
        if not slide:
            return jsonify({'error': 'Slide is required'}), 400
        
        rules = pptx_service.get_stored_rules()
        layouts = provided_layouts if provided_layouts is not None else rules.get('layouts', [])
        
        if not layouts:
            return jsonify({'error': 'No layouts available'}), 400
        
        regenerated_slide = get_ai_service().regenerate_single_slide(
            slide=slide,
            images=images,
            layouts=layouts,
            context_slides=context_slides
        )
        
        return jsonify({
            'success': True,
            'slide': regenerated_slide
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/analyze-image', methods=['POST'])
def analyze_image():
    """analyze image content with vision AI"""
    try:
        request_data = request.get_json()
        image_data = request_data.get('image_data')
        
        if not image_data:
            return jsonify({'error': 'image_data required'}), 400
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        analysis = get_ai_service().analyze_image_content(image_data)
        
        return jsonify({
            'success': True,
            **analysis
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


