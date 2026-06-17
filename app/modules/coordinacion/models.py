from datetime import datetime
from app.database import db # Se ajustó para apuntar a la base de datos central

class Coordinacion(db.Model):
    __tablename__ = 'coordinaciones'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    nombre = db.Column(db.String(100), unique=True, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    # Relación 1:N preparada para el siguiente módulo (Instructores)
    #instructores = db.relationship('Instructor', backref='coordinacion', lazy=True)

    def __repr__(self):
        return f'<Coordinacion {self.nombre}>'