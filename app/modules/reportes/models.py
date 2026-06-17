from app.database import db
from datetime import datetime

class Comite(db.Model):
    __tablename__ = 'comites'

    id = db.Column(db.Integer, primary_key=True)

    aprendiz_id = db.Column(db.Integer, db.ForeignKey('aprendices.id'), nullable=False)
    ficha_id = db.Column(db.Integer, db.ForeignKey('fichas.id'), nullable=False)

    instructor_id = db.Column(db.Integer, db.ForeignKey('instructores.id'), nullable=True)
    coordinacion_id = db.Column(db.Integer, db.ForeignKey('coordinaciones.id'), nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    profesional_bienestar = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    representante_aprendices = db.Column(db.String(100), nullable=True)

    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=True)

    sede = db.Column(db.String(100), nullable=True)
    piso = db.Column(db.String(50), nullable=True)
    ambiente = db.Column(db.String(50), nullable=True)

    tipo_falta = db.Column(db.String(50), nullable=True)
    motivo = db.Column(db.Text, nullable=True)
    recomendacion = db.Column(db.Text, nullable=True)
    plan_mejoramiento = db.Column(db.Text, nullable=True)
    fecha_plazo = db.Column(db.Date, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    activo = db.Column(db.Boolean, default=True)
    paz_salvo = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones claras
    profesional = db.relationship(
        'Usuario',
        foreign_keys=[profesional_bienestar],
        backref='comites_como_psicologa'
    )

    registrador = db.relationship(
        'Usuario',
        foreign_keys=[usuario_id],
        backref='comites_registrados'
    )

    instructor = db.relationship(
        'Instructor',
        foreign_keys=[instructor_id],
        backref='comites'
    )

    aprendiz = db.relationship(
        'Aprendiz',
        backref='comites'
    )