import os
import base64
import requests
from flask import Flask, redirect, url_for
from app.database import db
from flask_login import LoginManager


class BrevoMail:
    def __init__(self):
        self.api_key = None

    def init_app(self, app):
        # Captura la variable de entorno desde Railway
        self.api_key = os.getenv("BREVO_API_KEY")

    def _build_headers(self):
        return {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json",
        }

    def _build_recipients(self, recipients):
        if isinstance(recipients, list):
            return [{"email": email} for email in recipients]
        return [{"email": recipients}]

    def send_message(self, subject, recipients, html_body, sender=None):
        """
        Método para correos simples.
        """
        if not self.api_key:
            print("Error: BREVO_API_KEY no está configurada.")
            return None

        from_email = sender or "eddie1204diamante@gmail.com"
        url = "https://api.brevo.com/v3/smtp/email"

        payload = {
            "sender": {
                "name": "NEXUS SENA",
                "email": from_email
            },
            "to": self._build_recipients(recipients),
            "subject": subject,
            "htmlContent": html_body
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=30
            )

            if response.status_code in (200, 201):
                data = response.json()
                print(f"Correo enviado exitosamente vía Brevo. Respuesta: {data}")
                return data
            else:
                print(f"Error API Brevo: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            print(f"Error de conexión con Brevo: {e}")
            return None

    def send_message_with_attachment(
        self,
        subject,
        recipients,
        html_body,
        filename,
        file_bytes,
        sender=None
    ):
        """
        Método para correos con adjunto PDF.
        """
        if not self.api_key:
            print("Error: BREVO_API_KEY no está configurada.")
            return None

        from_email = sender or "eddie1204diamante@gmail.com"
        url = "https://api.brevo.com/v3/smtp/email"
        pdf_base64 = base64.b64encode(file_bytes).decode("utf-8")

        payload = {
            "sender": {
                "name": "NEXUS SENA",
                "email": from_email
            },
            "to": self._build_recipients(recipients),
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
            response = requests.post(
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=30
            )

            if response.status_code in (200, 201):
                data = response.json()
                print(f"Correo con adjunto enviado correctamente vía Brevo. Respuesta: {data}")
                return data
            else:
                print(f"Error API Brevo con adjunto: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            print(f"Error de conexión al enviar correo con adjunto: {e}")
            return None


# Mantienes el mismo nombre de objeto
mail = BrevoMail()


def create_app():
    app = Flask(__name__)

    # Configuración desde variables de entorno
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Configuración de base de datos
    mysql_url = os.getenv("MYSQL_URL")
    if mysql_url:
        mysql_url = mysql_url.replace("mysql://", "mysql+pymysql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    print("MYSQL_URL =", os.getenv("MYSQL_URL"))
    print("SQLALCHEMY_DATABASE_URI =", app.config["SQLALCHEMY_DATABASE_URI"])
    print("BREVO_API_KEY exists =", bool(os.getenv("BREVO_API_KEY")))

    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    # Registro de blueprints
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
    app.register_blueprint(aprendiz_bp, url_prefix="/aprendices")
    app.register_blueprint(main_bp)
    app.register_blueprint(ficha_bp, url_prefix="/fichas")
    app.register_blueprint(coordinacion_bp, url_prefix="/coordinaciones")
    app.register_blueprint(instructor_bp, url_prefix="/instructores")
    app.register_blueprint(comite_bp, url_prefix="/comites")
    app.register_blueprint(usuario_bp, url_prefix="/usuarios")
    app.register_blueprint(atencion_bp, url_prefix="/atencion")
    app.register_blueprint(talleres_bp, url_prefix="/taller")
    app.register_blueprint(reportes_bp, url_prefix="/reportes")

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

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