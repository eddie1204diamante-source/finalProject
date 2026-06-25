from app.database import db

class Taller(db.Model):
    __tablename__ = 'talleres'

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(150), nullable=False)

    descripcion = db.Column(db.Text)

    fecha_programada = db.Column(db.DateTime, nullable=False)

    # Relación con Instructor
    instructor_id = db.Column(
        db.Integer,
        db.ForeignKey('instructores.id'),
        nullable=False
    )

    instructor = db.relationship(
        'Instructor',
        backref='talleres'
    )

    aforo = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default='Programado'
    )
    asistentes = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    def __repr__(self):
        return f'<Taller {self.nombre}>'