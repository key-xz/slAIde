import os
from dotenv import load_dotenv

_BASE_DIR = os.path.dirname(__file__)

# load env files from the server directory (not the process cwd)
_env_path = os.path.join(_BASE_DIR, '.env')
_env_dev_path = os.path.join(_BASE_DIR, '.env.development')
_env_prod_path = os.path.join(_BASE_DIR, '.env.production')

if os.path.exists(_env_path):
    load_dotenv(_env_path)
elif os.path.exists(_env_dev_path):
    load_dotenv(_env_dev_path)
elif os.path.exists(_env_prod_path):
    load_dotenv(_env_prod_path)
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
    # openrouter (openai-compatible) configuration
    # prefer OPENROUTER_API_KEY; fall back to OPENAI_API_KEY for convenience during migration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    OPENROUTER_SITE_URL = os.getenv('OPENROUTER_SITE_URL')
    OPENROUTER_APP_NAME = os.getenv('OPENROUTER_APP_NAME', 'slAIde')

    # default to kimi via openrouter
    AI_MODEL = os.getenv('AI_MODEL', 'moonshotai/kimi-k2.5')

    # optional: use a separate model for multimodal (image) analysis
    AI_VISION_MODEL = os.getenv('AI_VISION_MODEL', 'openai/gpt-4o-mini')
    
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
