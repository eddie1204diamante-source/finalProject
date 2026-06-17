from app.database import db
from datetime import datetime

class Taller(db.Model):
    __tablename__ = 'talleres'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_programada = db.Column(db.DateTime, nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='Programado')

    def __repr__(self):
        return f'<Taller {self.nombre}>'