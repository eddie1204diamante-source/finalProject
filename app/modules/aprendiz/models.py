from app.database import db

class Aprendiz(db.Model):
    __tablename__ = 'aprendices'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tipo_documento = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    etapa_formacion = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    celular = db.Column(db.String(15), nullable=False)

    ficha_id = db.Column(db.Integer, db.ForeignKey('fichas.id'), nullable=False)

    activo = db.Column(db.Integer, default=1)
    es_vocero = db.Column(db.Integer, default=0)

    ficha = db.relationship('Ficha', backref=db.backref('aprendices', lazy=True))