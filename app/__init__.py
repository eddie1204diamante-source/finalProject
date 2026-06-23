from flask import Flask, redirect, url_for
from app.database import db
from flask_login import LoginManager
import os
import resend  # <--- 1. Importamos la nueva librería

# 2. Creamos una clase espejo para no romper el resto de tus archivos/controladores
class ResendMail:
    def __init__(self):
        self.api_key = None

    def init_app(self, app):
        # Leemos la variable que ya configuraste en Railway
        self.api_key = os.getenv('RESEND_API_KEY')
        resend.api_key = self.api_key

    def send_message(self, subject, recipients, html_body, sender=None):
        """Método rápido para enviar correos usando la API HTTPS de Resend"""
        # Si estás en modo prueba de una sola noche, usa el remitente por defecto de Resend
        from_email = sender or "Tu App <onboarding@resend.dev>"
        
        try:
            params = {
                "from": from_email,
                "to": recipients if isinstance(recipients, list) else [recipients],
                "subject": subject,
                "html": html_body,
            }
            response = resend.Emails.send(params)
            print(f"Correo enviado exitosamente mediante Resend. ID: {response.get('id')}")
            return response
        except Exception as e:
            print(f"Error crítico al enviar correo por Resend HTTPS: {e}")
            return None

# Mantienes exactamente el mismo nombre de objeto para que tus controladores no fallen
mail = ResendMail()

def create_app():
    app = Flask(__name__)

    # Configuración desde variables de entorno
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Configuración desde variables de entorno de Base de Datos
    mysql_url = os.getenv('MYSQL_URL')
    if mysql_url:
        mysql_url = mysql_url.replace("mysql://", "mysql+pymysql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_url

    print("MYSQL_URL =", os.getenv('MYSQL_URL'))
    print("SQLALCHEMY_DATABASE_URI =", app.config['SQLALCHEMY_DATABASE_URI'])

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializaciones de extensiones
    db.init_app(app)
    mail.init_app(app)  # <--- Inicializa la configuración de Resend

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # --- REGISTRO DE BLUEPRINTS (Se mantiene exactamente igual) ---
    from app.modules.auth.controllers import auth_bp
    from app.modules.aprendiz.controllers import aprendiz_bp
    from app.modules.main.controllers import main_bp
    from app.modules.ficha.controllers import ficha_bp
    from app.modules.coordinacion.controllers import coordinacion_bp
    from app.modules.instructor.controllers import instructor_bp
    from app.modules.comite.controllers import comite_bp
    from app.modules.usuario.controllers import usuario_bp
    from app.modules.atencion.controllers import atencion_bp
    from app.modules.taller.controllers import talleres_bp
    from app.modules.reportes.controllers import reportes_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(aprendiz_bp, url_prefix='/aprendices')
    app.register_blueprint(main_bp)
    app.register_blueprint(ficha_bp, url_prefix='/fichas')
    app.register_blueprint(coordinacion_bp, url_prefix='/coordinaciones')
    app.register_blueprint(instructor_bp, url_prefix='/instructores')
    app.register_blueprint(comite_bp, url_prefix='/comites')
    app.register_blueprint(usuario_bp, url_prefix='/usuarios')
    app.register_blueprint(atencion_bp, url_prefix='/atencion')
    app.register_blueprint(talleres_bp, url_prefix='/taller')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    with app.app_context():
        from app.modules.auth.models import Usuario
        from app.modules.comite.models import Comite
        from app.modules.aprendiz.models import Aprendiz
        from app.modules.atencion.models import Atencion
        from app.modules.taller.models import Taller
        db.create_all()
        
        @login_manager.user_loader
        def load_user(user_id):
            return Usuario.query.get(int(user_id))

    return app
