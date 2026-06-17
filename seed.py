from app import create_app
from app.database import db
from app.modules.auth.models import Usuario
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt()

def run_seed():
    with app.app_context():
        hashed_password = bcrypt.generate_password_hash("Nala123*").decode('utf-8')
        
        usuarios = [
            {
                "nombre": "Administrador Principal",
                "email": "v64149378@gmail.com",
                "password": hashed_password,
                "rol": "ADMIN"
            },
            {
                "nombre": "Laura Gomez",
                "email": "psico@sena.edu.co",
                "password": hashed_password,
                "rol": "PSICOLOGA"
            },
            {
                "nombre": "Maria Torres",
                "email": "social@sena.edu.co",
                "password": hashed_password,
                "rol": "T_SOCIAL"
            }
        ]

        for user_data in usuarios:
            usuario = Usuario.query.filter_by(email=user_data['email']).first()
            
            if usuario:
                # Si existe, solo actualizamos la contraseña y el estado
                usuario.password = user_data['password']
                usuario.nombre = user_data['nombre']
                usuario.enabled = 1
                print(f"Actualizado: {user_data['email']}")
            else:
                # Si no existe, lo creamos de cero
                nuevo_usuario = Usuario(
                    nombre=user_data['nombre'],
                    email=user_data['email'],
                    password=user_data['password'],
                    rol=user_data['rol'],
                    enabled=1
                )
                db.session.add(nuevo_usuario)
                print(f"Creado: {user_data['email']}")
        
        try:
            db.session.commit()
            print("Proceso finalizado con éxito.")
        except Exception as e:
            db.session.rollback()
            print(f"Error al confirmar cambios: {e}")

if __name__ == "__main__":
    run_seed()