import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from flask_mail import Message
from app.database import db
from app.modules.auth.models import Usuario, PasswordResetToken

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# --- CONSTANTE DE VALIDACIÓN (Para no repetir código) ---
REGEX_PASSWORD = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
DOMINIOS_SENA = ("sena.edu.co", "misena.edu.co")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and bcrypt.check_password_hash(usuario.password, password):
            if usuario.enabled:
                login_user(usuario)
                flash(f"¡Bienvenido {usuario.nombre}! Has ingresado como {usuario.rol.upper()}", "success")
                return redirect(url_for('main.dashboard'))
            else:
                flash('Tu cuenta está deshabilitada.', 'error')
        else:
            flash('Correo o contraseña incorrectos.', 'error')
            
    return render_template('auth/login.html')
@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # 1. Obtener y limpiar datos primero
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        rol = request.form.get('rol')

        # 2. Validación de campos vacíos
        if not all([nombre, email, password, rol]):
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('auth/registro.html')

        # 3. Validación de Nombre (3-50 caracteres, sin números)
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{3,50}$", nombre):
            flash('El nombre debe tener entre 3 y 50 letras (sin números).', 'error')
            return render_template('auth/registro.html')

        # 4. Validación de Email Institucional Estricta (Mínimo 3 caracteres antes del @)
        if not re.match(r"^[a-zA-Z0-9._%+-]{3,}@(sena\.edu\.co|misena\.edu\.co)$", email):
            flash('El formato del correo institucional es inválido (mín. 3 caracteres antes del @).', 'error')
            return render_template('auth/registro.html')

        # 5. Validación de coincidencia de contraseñas
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('auth/registro.html')

        # 6. Validación de complejidad de contraseña (REGEX)
        if not re.match(REGEX_PASSWORD, password):
            flash('Contraseña débil: Mín. 8 caracteres, una mayúscula, un número y un símbolo.', 'error')
            return render_template('auth/registro.html')

        # 7. Verificación de existencia en DB
        if Usuario.query.filter_by(email=email).first():
            flash(f'El correo {email} ya está registrado.', 'error')
            return render_template('auth/registro.html')

        # 8. Intento de guardado
        try:
            nuevo_usuario = Usuario(
                nombre=nombre.title(), 
                email=email,
                password=bcrypt.generate_password_hash(password).decode('utf-8'),
                rol=rol,
                enabled=True
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error en DB: {e}")
            flash('Error al procesar el registro en el servidor.', 'error')

    return render_template('auth/registro.html')

@auth_bp.route('/recuperar-password', methods=['GET', 'POST'])
def recuperar_password():
    if request.method == 'POST':
        from app import mail

        email = request.form.get('email', '').strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            flash('No encontramos ninguna cuenta con ese correo.', 'error')
            return render_template('auth/recuperar_password.html')

        token_obj = PasswordResetToken(usuario_id=usuario.id)

        try:
            db.session.add(token_obj)
            db.session.commit()

            enlace = url_for(
                'auth.restaurar_password',
                token=token_obj.token,
                _external=True
            )

            msg = Message(
                subject='Recuperación de Contraseña | NEXUS',
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[email]
            )

            msg.body = f"""
Hola {usuario.nombre}

Recibimos una solicitud para restablecer tu contraseña.

Haz clic en el siguiente enlace:

{enlace}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.
"""

            print("===================================")
            print("Intentando enviar correo a:", email)
            print("SMTP:", current_app.config['MAIL_SERVER'])
            print("Puerto:", current_app.config['MAIL_PORT'])
            print("Usuario SMTP:", current_app.config['MAIL_USERNAME'])
            print("===================================")

            mail.send(msg)

            print("CORREO ENVIADO CORRECTAMENTE")

            flash(
                'Se han enviado instrucciones a tu correo institucional.',
                'success'
            )

            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()

            print("ERROR SMTP:")
            print(repr(e))

            flash(
                f'Error al enviar correo: {str(e)}',
                'error'
            )

    return render_template('auth/recuperar_password.html')

@auth_bp.route('/restaurar-password', methods=['GET', 'POST'])
def restaurar_password():
    token = request.args.get('token')
    token_obj = PasswordResetToken.query.filter_by(token=token).first()

    if not token_obj:
        flash('Enlace inválido o expirado.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        # Aplicamos las mismas reglas de seguridad que en el registro
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('auth/restaurar_password.html', token=token)

        if not re.match(REGEX_PASSWORD, password):
            flash('La nueva contraseña no cumple con los requisitos de seguridad.', 'error')
            return render_template('auth/restaurar_password.html', token=token)

        usuario = Usuario.query.get(token_obj.usuario_id)
        if usuario:
            usuario.password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.delete(token_obj)
            db.session.commit()
            
            flash('Contraseña actualizada correctamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/restaurar_password.html', token=token)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('auth.login'))