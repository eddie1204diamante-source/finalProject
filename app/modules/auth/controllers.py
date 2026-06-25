import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from app.database import db
from app.modules.auth.models import Usuario, PasswordResetToken

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# --- CONSTANTE DE VALIDACIÓN ---
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
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        rol = request.form.get('rol')

        if not all([nombre, email, password, rol]):
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('auth/registro.html')

        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{3,50}$", nombre):
            flash('El nombre debe tener entre 3 y 50 letras (sin números).', 'error')
            return render_template('auth/registro.html')

        if not re.match(r"^[a-zA-Z0-9._%+-]{3,}@(sena\.edu\.co|misena\.edu\.co)$", email):
            flash('El formato del correo institucional es inválido (mín. 3 caracteres antes del @).', 'error')
            return render_template('auth/registro.html')

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('auth/registro.html')

        if not re.match(REGEX_PASSWORD, password):
            flash('Contraseña débil: Mín. 8 caracteres, una mayúscula, un número y un símbolo.', 'error')
            return render_template('auth/registro.html')

        if Usuario.query.filter_by(email=email).first():
            flash(f'El correo {email} ya está registrado.', 'error')
            return render_template('auth/registro.html')

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
        from app import mail  # Importamos tu clase espejo vinculada a Brevo
        email = request.form.get('email').strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            token_obj = PasswordResetToken(usuario_id=usuario.id)
            db.session.add(token_obj)
            db.session.commit()
            
            try:
                enlace = url_for('auth.restaurar_password', token=token_obj.token, _external=True)
                
                cuerpo_html = f"""
                <p>Hola <strong>{usuario.nombre}</strong>,</p>
                <p>Recibimos una solicitud para restablecer tu contraseña en NEXUS.</p>
                <p>Para restaurarla, haz clic en el siguiente enlace:</p>
                <p><a href="{enlace}" style="padding: 10px 20px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; display: inline-block;">Restablecer Contraseña</a></p>
                <br>
                <p><small>Este enlace expirará en 1 hora. Si no solicitaste esto, puedes ignorar este correo con seguridad.</small></p>
                """
                
                
                mail.send_message(
                subject="Recuperación de Contraseña | NEXUS",
                recipients=[email],
                html_body=cuerpo_html
            )
                
                flash('Se han enviado instrucciones a tu correo institucional.', 'success')
            except Exception as e:
                print(f"Error al enviar correo por API Brevo: {e}")
                flash('Hubo un problema al enviar el correo. Intenta de nuevo.', 'error')
            
            return redirect(url_for('auth.login'))
        else:
            flash('No encontramos ninguna cuenta con ese correo.', 'error')
            
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
