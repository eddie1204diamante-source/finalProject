from app.database import db
from datetime import date
# Importamos la clase real del único sitio donde quedó definida
from app.modules.auth.models import Usuario 

class Comite(db.Model):
    __tablename__ = 'comites'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Llaves Foráneas
    aprendiz_id = db.Column(db.BigInteger, db.ForeignKey('aprendices.id'), nullable=True)
    ficha_id = db.Column(db.BigInteger, db.ForeignKey('fichas.id'), nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructores.id'), nullable=True)
    coordinacion_id = db.Column(db.Integer, db.ForeignKey('coordinaciones.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True) # Quien registra
    
    # Campos Obligatorios
    profesional_bienestar = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False) # Psicóloga
    representante_aprendices = db.Column(db.String(100), nullable=False)
    
    # Tiempos y Ubicación
    fecha = db.Column(db.Date, nullable=True)
    hora = db.Column(db.Time, nullable=True)
    sede = db.Column(db.String(50), nullable=False)
    piso = db.Column(db.String(50), nullable=False)
    ambiente = db.Column(db.String(50), nullable=False)
    
    # Proceso
    tipo_falta = db.Column(db.String(50), nullable=True)
    motivo = db.Column(db.Text, nullable=False)
    recomendacion = db.Column(db.Text, nullable=False)
    plan_mejoramiento = db.Column(db.Text, nullable=False)
    fecha_plazo = db.Column(db.Date, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    
    # Estados
    activo = db.Column(db.Boolean, default=True)
    paz_salvo = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.Date, default=date.today)

    # --- RELACIONES CORREGIDAS ---
    
    aprendiz = db.relationship('Aprendiz', backref='comites_asignados')
    
    # Relación con la Psicóloga (Profesional)
    profesional = db.relationship(
        Usuario, 
        foreign_keys=[profesional_bienestar], 
        backref='comites_como_psicologa' # Nombre único para el backref
    )
    
    # Relación con quien digita (Registrador)
    registrador = db.relationship(
        Usuario, 
        foreign_keys=[usuario_id], 
        backref='actas_digitadas' # Nombre único para el backref
    )
    
    instructor = db.relationship('Instructor', backref='comites_instructor')
    coordinacion = db.relationship('Coordinacion', backref='comites_coord')

    def __repr__(self):
        return f'<Comite {self.id} - {self.fecha}>'