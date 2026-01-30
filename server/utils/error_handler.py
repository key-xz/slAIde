"""centralized error handling utilities"""
import logging
import traceback
from functools import wraps
from flask import jsonify
from .validation import ValidationError


logger = logging.getLogger(__name__)


class APIError(Exception):
    """base exception for API errors"""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def handle_api_errors(f):
    """
    decorator to handle API errors consistently
    catches exceptions and returns appropriate JSON responses
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except ValidationError as e:
            logger.warning(f'validation error in {f.__name__}: {e}')
            return jsonify({'error': str(e)}), 400
        
        except FileNotFoundError as e:
            logger.warning(f'file not found in {f.__name__}: {e}')
            return jsonify({'error': 'resource not found'}), 404
        
        except ValueError as e:
            logger.warning(f'value error in {f.__name__}: {e}')
            return jsonify({'error': str(e)}), 400
        
        except APIError as e:
            logger.error(f'api error in {f.__name__}: {e}')
            return jsonify({'error': e.message}), e.status_code
        
        except Exception as e:
            # log full traceback but return generic error message
            logger.error(f'unexpected error in {f.__name__}: {e}', exc_info=True)
            return jsonify({'error': 'an unexpected error occurred'}), 500
    
    return wrapper


def safe_error_message(e: Exception) -> str:
    """
    return a safe error message for user display
    prevents information disclosure
    """
    if isinstance(e, (ValidationError, ValueError)):
        return str(e)
    
    # for other exceptions, return generic message
    return 'an error occurred while processing your request'
