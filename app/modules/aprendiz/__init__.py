from flask import Flask
from config import Config
from app.database import db
from app.modules.aprendiz.controllers import aprendiz_bp

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Inicializar SQLAlchemy
    db.init_app(app)

    # Registrar blueprints
    app.register_blueprint(aprendiz_bp, url_prefix='/aprendices')

    return app