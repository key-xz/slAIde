"""input validation and security utilities"""
import os
from pathlib import Path
from flask import Request
from werkzeug.datastructures import FileStorage


class ValidationError(ValueError):
    """raised when validation fails"""
    pass


def validate_pptx_file(request_files) -> FileStorage:
    """
    validate that a PPTX file was uploaded
    raises ValidationError if validation fails
    """
    if 'file' not in request_files:
        raise ValidationError('no file provided')
    
    file = request_files['file']
    
    if not file or file.filename == '':
        raise ValidationError('no file selected')
    
    if not file.filename.endswith('.pptx'):
        raise ValidationError('file must be a .pptx file')
    
    return file


def validate_file_size(file: FileStorage, max_size_mb: int = 50) -> None:
    """
    validate file size
    raises ValidationError if file is too large
    """
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if size > max_size_bytes:
        raise ValidationError(f'file size exceeds {max_size_mb}MB limit')


def validate_image_files(request_files) -> dict:
    """
    validate uploaded image files
    returns dict mapping image_id to FileStorage
    raises ValidationError if validation fails
    """
    images = {}
    
    for key, file in request_files.items():
        if key.startswith('image_'):
            if not file or file.filename == '':
                continue
            
            # validate image type
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
            ext = Path(file.filename).suffix.lower()
            
            if ext not in allowed_extensions:
                raise ValidationError(f'invalid image type: {ext}. allowed: {", ".join(allowed_extensions)}')
            
            images[key] = file
    
    return images


def validate_path_is_safe(path: str, allowed_parent: str) -> str:
    """
    validate that a file path is within an allowed directory
    prevents path traversal attacks
    raises ValidationError if path is unsafe
    returns absolute path
    """
    abs_path = os.path.abspath(path)
    abs_parent = os.path.abspath(allowed_parent)
    
    if not abs_path.startswith(abs_parent):
        raise ValidationError('invalid file path')
    
    return abs_path


def validate_ai_model(model: str) -> str:
    """
    validate AI model selection
    raises ValidationError if model is invalid
    """
    allowed_models = {'fast', 'openai', 'kimi'}
    
    if model not in allowed_models:
        raise ValidationError(f'invalid model: {model}. allowed: {", ".join(allowed_models)}')
    
    return model


def validate_boolean_param(value, param_name: str, default: bool = False) -> bool:
    """
    validate and parse boolean parameter
    returns boolean value or default if not provided
    """
    if value is None:
        return default
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    
    return bool(value)
