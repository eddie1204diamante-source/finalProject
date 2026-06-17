from datetime import datetime
from app.database import db

class Atencion(db.Model):
    __tablename__ = 'atenciones'

    id = db.Column(db.Integer, primary_key=True)

    estado_caso = db.Column(db.String(50), nullable=False)
    categoria_desercion = db.Column(db.String(100), nullable=False)
    remitido_por = db.Column(db.String(100), nullable=False)
    atencion_familiar = db.Column(db.String(255), nullable=True)

    fecha_creacion_registro = db.Column(db.DateTime, default=datetime.now)
    activo = db.Column(db.Boolean, default=True)

    # Seguimientos
    fecha_consulta_1 = db.Column(db.Date, nullable=True)
    observaciones_1 = db.Column(db.Text, nullable=True)
    fecha_consulta_2 = db.Column(db.Date, nullable=True)
    observaciones_2 = db.Column(db.Text, nullable=True)
    fecha_consulta_3 = db.Column(db.Date, nullable=True)
    observaciones_3 = db.Column(db.Text, nullable=True)

    # FK unificadas en INTEGER
    aprendiz_id = db.Column(db.Integer, db.ForeignKey('aprendices.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Relaciones
    aprendiz = db.relationship('Aprendiz', backref='atenciones_lista')
    profesional = db.relationship('Usuario', backref='atenciones_asignadas')