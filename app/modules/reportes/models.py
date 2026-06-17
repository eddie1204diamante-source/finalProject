from app.database import db
from datetime import datetime

class Comite(db.Model):
    __tablename__ = 'comites'

    # Identificadores (IDs)
    id = db.Column(db.Integer, primary_key=True)
    aprendiz_id = db.Column(db.Integer, db.ForeignKey('aprendices.id'), nullable=False)
    ficha_id = db.Column(db.Integer, db.ForeignKey('fichas.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    coordinacion_id = db.Column(db.Integer, db.ForeignKey('coordinaciones.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    profesional_bienestar = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    # Detalles del comité
    representante_aprendices = db.Column(db.String(100))
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time)
    sede = db.Column(db.String(100))
    piso = db.Column(db.String(50))
    ambiente = db.Column(db.String(50))
    
    # Información académica/disciplinaria
    tipo_falta = db.Column(db.String(50)) 
    motivo = db.Column(db.Text)
    recomendacion = db.Column(db.Text)
    plan_mejoramiento = db.Column(db.Text)
    fecha_plazo = db.Column(db.Date)
    observaciones = db.Column(db.Text)


    activo = db.Column(db.Boolean, default=True)   
    paz_salvo = db.Column(db.Boolean, default=False)  
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


    profesional = db.relationship('Usuario', foreign_keys=[profesional_bienestar])
