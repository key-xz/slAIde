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
