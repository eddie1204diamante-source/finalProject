from app.database import db

class Instructor(db.Model):
    __tablename__ = 'instructores'
    
    # Se ajustó a Integer para mantener consistencia con el módulo de Coordinación
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_documento = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    profesion = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relación con Coordinación: DEBE ser Integer para que la Foreign Key funcione
    coordinacion_id = db.Column(db.Integer, db.ForeignKey('coordinaciones.id'), nullable=False)
    
    # Relación para acceder fácilmente al objeto coordinacion desde instructor
    coordinacion = db.relationship('Coordinacion', backref=db.backref('instructores', lazy=True))

    def __repr__(self):
        return f'<Instructor {self.nombres} {self.apellidos}>'