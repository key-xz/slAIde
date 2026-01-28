from flask import Flask
from flask_cors import CORS
from config import get_config
from routes import api_blueprint


def create_app(config_name=None):
    app = Flask(__name__)
    
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    CORS(app, origins=app.config['CORS_ORIGINS'])
    app.register_blueprint(api_blueprint)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
