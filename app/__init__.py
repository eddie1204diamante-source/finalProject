import os
import base64
import requests  # <-- Necesario para conectar con Brevo por HTTPS
from flask import Flask, redirect, url_for
from app.database import db
from flask_login import LoginManager

# --- NUEVA CLASE PARA ENVIAR POR BREVO HTTPS ---
class BrevoMail:
    def __init__(self):
        self.api_key = None

    def init_app(self, app):
        # Captura la variable BREVO_API_KEY desde Railway
        self.api_key = os.getenv('BREVO_API_KEY')

    def send_message(self, subject, recipients, html_body, sender=None):
        """Método para correos simples (ej: Recuperación de contraseña)"""
        from_email = sender or "eddie1204diamante@gmail.com"
        
        url = "https://brevo.com"
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json"
        }
        
        to_list = [{"email": email} for email in (recipients if isinstance(recipients, list) else [recipients])]
        
        payload = {
            "sender": {"name": "NEXUS SENA", "email": from_email},
            "to": to_list,
            "subject": subject,
            "htmlContent": html_body
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                print(f"Correo enviado exitosamente vía Brevo HTTPS. ID: {response.json().get('messageId')}")
                return response.json()
            else:
                print(f"Error API Brevo: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error crítico de conexión HTTPS con Brevo: {e}")
            return None

    def send_message_with_attachment(self, subject, recipients, html_body, filename, file_bytes, sender=None):
        """Método para correos con el PDF adjunto (ej: Módulo de reportes)"""
        from_email = sender or "eddie1204diamante@gmail.com"
        
        url = "https://brevo.com"
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json"
        }
        
        to_list = [{"email": email} for email in (recipients if isinstance(recipients, list) else [recipients])]
        pdf_base64 = base64.b64encode(file_bytes).decode("utf-8")
        
        payload = {
            "sender": {"name": "NEXUS SENA", "email": from_email},
            "to": to_list,
            "subject": subject,
            "htmlContent": html_body,
            "attachments": [
                {
                    "name": filename,
                    "content": pdf_base64
                }
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                print(f"Correo con adjunto enviado correctamente mediante Brevo HTTPS. ID: {response.json().get('messageId')}")
                return response.json()
            else:
                print(f"Error API Brevo con adjunto: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error crítico al enviar correo con adjunto por Brevo HTTPS: {e}")
            return None


# Mantienes exactamente el mismo nombre de objeto para no romper tus controladores
mail = BrevoMail()

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
    db.init_app(app)
    mail.init_app(app)  # Inicializa la configuración de Brevo

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # --- REGISTRO DE BLUEPRINTS ---
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
