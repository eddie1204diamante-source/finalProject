from app.database import db
from datetime import date
from app.modules.auth.models import Usuario

class Comite(db.Model):
    __tablename__ = 'comites'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # FK (TODAS EN INTEGER para evitar errores 3780)
    aprendiz_id = db.Column(db.Integer, db.ForeignKey('aprendices.id'), nullable=True)
    ficha_id = db.Column(db.Integer, db.ForeignKey('fichas.id'), nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructores.id'), nullable=True)
    coordinacion_id = db.Column(db.Integer, db.ForeignKey('coordinaciones.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    profesional_bienestar = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    representante_aprendices = db.Column(db.String(100), nullable=False)

    fecha = db.Column(db.Date, nullable=True)
    hora = db.Column(db.Time, nullable=True)
    sede = db.Column(db.String(50), nullable=False)
    piso = db.Column(db.String(50), nullable=False)
    ambiente = db.Column(db.String(50), nullable=False)

    tipo_falta = db.Column(db.String(50), nullable=True)
    motivo = db.Column(db.Text, nullable=False)
    recomendacion = db.Column(db.Text, nullable=False)
    plan_mejoramiento = db.Column(db.Text, nullable=False)
    fecha_plazo = db.Column(db.Date, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    activo = db.Column(db.Boolean, default=True)
    paz_salvo = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.Date, default=date.today)

    # RELACIONES

    aprendiz = db.relationship('Aprendiz', backref='comites_asignados')

    profesional = db.relationship(
        Usuario,
        foreign_keys=[profesional_bienestar],
        backref='comites_como_psicologa'
    )

    registrador = db.relationship(
        Usuario,
        foreign_keys=[usuario_id],
        backref='actas_digitadas'
    )

    instructor = db.relationship('Instructor', backref='comites_instructor')
    coordinacion = db.relationship('Coordinacion', backref='comites_coord')

    def __repr__(self):
        return f'<Comite {self.id} - {self.fecha}>'