from flask import Flask, redirect, url_for
from app.database import db
from flask_login import LoginManager
from flask_mail import Mail
import os

mail = Mail()


def create_app():
    app = Flask(__name__)

    # =========================
    # CONFIGURACIÓN BASE
    # =========================
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # =========================
    # BASE DE DATOS (FIX MYSQL)
    # =========================
    mysql_url = os.getenv('MYSQL_URL')

    if mysql_url:
        mysql_url = mysql_url.replace("mysql://", "mysql+pymysql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    print("MYSQL_URL =", mysql_url)
    print("SQLALCHEMY_DATABASE_URI =", app.config['SQLALCHEMY_DATABASE_URI'])

    db.init_app(app)

    # =========================
    # LOGIN MANAGER
    # =========================
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # =========================
    # MAIL CONFIG (BREVO / SMTP)
    # =========================
    app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

    mail.init_app(app)

    # =========================
    # BLUEPRINTS
    # =========================
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
    app.register_blueprint(main_bp)
    app.register_blueprint(aprendiz_bp, url_prefix='/aprendices')
    app.register_blueprint(ficha_bp, url_prefix='/fichas')
    app.register_blueprint(coordinacion_bp, url_prefix='/coordinaciones')
    app.register_blueprint(instructor_bp, url_prefix='/instructores')
    app.register_blueprint(comite_bp, url_prefix='/comites')
    app.register_blueprint(usuario_bp, url_prefix='/usuarios')
    app.register_blueprint(atencion_bp, url_prefix='/atencion')
    app.register_blueprint(talleres_bp, url_prefix='/taller')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')

    # =========================
    # RUTA PRINCIPAL
    # =========================
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # =========================
    # DB INIT (SOLO CREATE ALL)
    # =========================
    with app.app_context():
        db.create_all()

    # =========================
    # USER LOADER
    # =========================
    from app.modules.auth.models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    return app