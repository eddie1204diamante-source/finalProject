from flask import Flask, redirect, url_for
from app.database import db
from flask_login import LoginManager
from flask_mail import Mail

mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Configuración de base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/NexusPython'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'tu_clave_secreta'

    # Configuración de correo
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'v64149378@gmail.com'
    app.config['MAIL_PASSWORD'] = 'hxilscvjkfqozxis' 
    app.config['MAIL_DEFAULT_SENDER'] = 'v64149378@gmail.com'

    # Inicialización de extensiones
    db.init_app(app)
    mail.init_app(app)

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
    # NUEVO: Importación del controlador de atención
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
    # NUEVO: Registro del blueprint de atención
    app.register_blueprint(atencion_bp, url_prefix='/atencion')
    app.register_blueprint(talleres_bp, url_prefix='/taller')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    with app.app_context():
        # IMPORTANTE: Cargamos los modelos para que SQLAlchemy reconozca las relaciones
        from app.modules.auth.models import Usuario
        from app.modules.comite.models import Comite
        from app.modules.aprendiz.models import Aprendiz
        # NUEVO: Carga del modelo de Atención para las relaciones de BD
        from app.modules.atencion.models import Atencion
        from app.modules.taller.models import Taller
        db.create_all()
        @login_manager.user_loader
        def load_user(user_id):
            return Usuario.query.get(int(user_id))

    return app