from app.database import db

class Ficha(db.Model):
    __tablename__ = 'fichas'

    # Identificador único (Sincronizado con Aprendiz e Instructor)
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    codigo = db.Column(db.String(20), unique=True, nullable=False)
    programa = db.Column(db.String(150), nullable=False)
    jornada = db.Column(db.String(50))
    modalidad = db.Column(db.String(50))

    # AJUSTE: Relación formal con la tabla coordinaciones
    # Se añade ForeignKey para integridad referencial en la base de datos
    coordinacion_id = db.Column(db.BigInteger, db.ForeignKey('coordinaciones.id'), nullable=True)
    
    # Helper para acceder a datos de la coordinación (ej: ficha.coordinacion.nombre)
    coordinacion = db.relationship('Coordinacion', backref='fichas')

    # Estado de la ficha: 1 para activo, 0 para inactivo
    activo = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<Ficha {self.codigo}>'