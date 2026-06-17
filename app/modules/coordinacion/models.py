from app.database import db

class Coordinacion(db.Model):
    __tablename__ = 'coordinaciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    nombre = db.Column(db.String(100), unique=True, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Coordinacion {self.nombre}>'