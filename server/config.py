import os
from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('.env.development'):
    load_dotenv('.env.development')
else:
    load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '5000'))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))
    ALLOWED_EXTENSIONS = {'.pptx'}
    TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4o')
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.TEMP_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])


PREDEFINED_LAYOUT_CATEGORIES = [
    {
        'id': 'title_slide',
        'name': 'Title Slide',
        'description': 'presentation opening with title and subtitle',
        'isPredefined': True
    },
    {
        'id': 'section_divider',
        'name': 'Section Divider',
        'description': 'separates major sections, typically minimal text',
        'isPredefined': True
    },
    {
        'id': 'table_of_contents',
        'name': 'Table of Contents',
        'description': 'lists presentation sections or agenda',
        'isPredefined': True
    },
    {
        'id': 'content_standard',
        'name': 'Standard Content',
        'description': 'title + body text, 1-2 text areas',
        'isPredefined': True
    },
    {
        'id': 'content_with_image',
        'name': 'Content with Image',
        'description': 'text and single image side-by-side or stacked',
        'isPredefined': True
    },
    {
        'id': 'image_focused',
        'name': 'Image Focused',
        'description': 'large image with minimal text',
        'isPredefined': True
    },
    {
        'id': 'multi_image_grid',
        'name': 'Multi-Image Grid',
        'description': '2+ images in grid layout',
        'isPredefined': True
    },
    {
        'id': 'two_column',
        'name': 'Two Column',
        'description': 'side-by-side text columns',
        'isPredefined': True
    },
    {
        'id': 'comparison',
        'name': 'Comparison',
        'description': 'compare two concepts side-by-side',
        'isPredefined': True
    },
    {
        'id': 'closing_slide',
        'name': 'Closing Slide',
        'description': 'thank you, contact info, or conclusion',
        'isPredefined': True
    }
]
