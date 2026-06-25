from app.database import db

class Instructor(db.Model):
    __tablename__ = 'instructores'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_documento = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    profesion = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    coordinacion_id = db.Column(
        db.Integer,
        db.ForeignKey('coordinaciones.id'),
        nullable=False
    )

    coordinacion = db.relationship(
        'Coordinacion',
        backref=db.backref('instructores', lazy=True)
    )

    def __repr__(self):
        return f'<Instructor {self.nombres} {self.apellidos}>'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"