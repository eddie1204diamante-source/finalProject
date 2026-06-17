from app.database import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    enabled = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Usuario {self.email}>'

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    expiracion = db.Column(db.DateTime, nullable=False)

    def __init__(self, usuario_id):
        self.usuario_id = usuario_id
        self.token = secrets.token_urlsafe(32)
        # Expira en 1 hora, igual que en tu EmailService.java
        self.expiracion = datetime.utcnow() + timedelta(hours=1)