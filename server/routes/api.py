from flask import Blueprint, request, jsonify
from services import PPTXService

api_blueprint = Blueprint('api', __name__, url_prefix='/api')
pptx_service = PPTXService()


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


@api_blueprint.route('/generate-slide', methods=['POST'])
def generate_slide():
    try:
        data = request.get_json()
        layout_name = data.get('layout_name')
        inputs = data.get('inputs', {})
        
        if not layout_name:
            return jsonify({'error': 'Layout name is required'}), 400
        
        file_b64 = pptx_service.generate_slide(layout_name, inputs)
        
        return jsonify({
            'success': True,
            'message': 'Slide generated successfully',
            'file': file_b64
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
