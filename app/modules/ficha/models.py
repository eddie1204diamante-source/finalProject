from app.database import db

class Ficha(db.Model):
    __tablename__ = 'fichas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    codigo = db.Column(db.String(20), unique=True, nullable=False)
    programa = db.Column(db.String(150), nullable=False)
    jornada = db.Column(db.String(50))
    modalidad = db.Column(db.String(50))

    coordinacion_id = db.Column(
        db.Integer,
        db.ForeignKey('coordinaciones.id'),
        nullable=True
    )

    coordinacion = db.relationship('Coordinacion', backref='fichas')

    activo = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<Ficha {self.codigo}>'