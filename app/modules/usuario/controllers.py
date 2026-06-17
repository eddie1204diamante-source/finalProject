import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_bcrypt import Bcrypt
from app.database import db

# Importación del modelo
from app.modules.auth.models import Usuario

usuario_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')
bcrypt = Bcrypt()

@usuario_bp.route('/')
@login_required
def listar():
    # Solo el ADMIN puede ver la gestión de usuarios
    if current_user.rol != 'ADMIN':
        flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Listamos todos los usuarios ordenados por ID
    usuarios = Usuario.query.order_by(Usuario.id.asc()).all()
    return render_template('usuario/lista.html', usuarios=usuarios)

@usuario_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if current_user.rol != 'ADMIN':
        return redirect(url_for('usuarios.listar'))

    errors = {}
    usuarioDTO = {}
    roles = ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        rol = request.form.get('rolId')

        usuarioDTO = {
            'nombre': nombre,
            'email': email,
            'rolId': rol
        }

        if not nombre:
            errors['nombre'] = "El nombre completo es obligatorio."
        
        if not email:
            errors['email'] = "El correo institucional es obligatorio."
        elif Usuario.query.filter_by(email=email).first():
            errors['email'] = f'El correo {email} ya está registrado.'

        regex_password = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not password:
            errors['password'] = "La contraseña es obligatoria."
        elif not re.match(regex_password, password):
            errors['password'] = "Mín. 8 caracteres, una Mayúscula, un Número y un Símbolo."

        if not confirm_password:
            errors['confirmPassword'] = "Debes confirmar la contraseña."
        elif password != confirm_password:
            errors['confirmPassword'] = "Las contraseñas no coinciden."

        if not rol:
            errors['rolId'] = "Seleccione un rol institucional."

        if errors:
            return render_template('usuario/crear.html', 
                                 errors=errors, 
                                 usuarioDTO=usuarioDTO, 
                                 roles=roles)

        try:
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                password=bcrypt.generate_password_hash(password).decode('utf-8'),
                rol=rol,
                enabled=True
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('usuarios.listar'))
        except Exception as e:
            db.session.rollback()
            flash('Error al procesar el registro.', 'error')

    return render_template('usuario/crear.html', roles=roles, errors={}, usuarioDTO={})

@usuario_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if current_user.rol != 'ADMIN':
        return redirect(url_for('usuarios.listar'))

    usuario = Usuario.query.get_or_404(id)
    errors = {}
    roles = ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']

    if request.method == 'POST':
        nuevo_email = request.form.get('email')
        nombre = request.form.get('nombre')
        rol = request.form.get('rolId')
        nueva_pass = request.form.get('password')
        confirm_pass = request.form.get('confirmPassword') # Captura de confirmación añadida

        if not nombre:
            errors['nombre'] = "El nombre es obligatorio."
        
        if not nuevo_email:
            errors['email'] = "El correo es obligatorio."
        
        existente = Usuario.query.filter_by(email=nuevo_email).first()
        if existente and existente.id != usuario.id:
            errors['email'] = 'El email ya está en uso por otro usuario.'

        # Ajuste de validación de contraseña opcional
        if nueva_pass:
            regex_password = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
            if not re.match(regex_password, nueva_pass):
                errors['password'] = "Mín. 8 caracteres, una Mayúscula, un Número y un Símbolo."
            
            # Validación de coincidencia añadida
            if nueva_pass != confirm_pass:
                errors['confirmPassword'] = "Las contraseñas no coinciden."

        if errors:
            return render_template('usuario/editar.html', u=usuario, errors=errors, roles=roles)

        usuario.nombre = nombre
        usuario.email = nuevo_email
        usuario.rol = rol
        if nueva_pass:
            usuario.password = bcrypt.generate_password_hash(nueva_pass).decode('utf-8')

        db.session.commit()
        flash('Usuario actualizado correctamente.', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuario/editar.html', u=usuario, roles=roles, errors={})

@usuario_bp.route('/cambiar-estado/<int:id>')
@login_required
def cambiar_estado(id):
    if current_user.rol != 'ADMIN':
        return redirect(url_for('usuarios.listar'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.email == current_user.email:
        flash('No puedes desactivar tu propia cuenta.', 'warning')
        return redirect(url_for('usuarios.listar'))

    usuario.enabled = not usuario.enabled
    db.session.commit()
    
    estado = "activado" if usuario.enabled else "desactivado"
    flash(f'Usuario {usuario.nombre} {estado} correctamente.', 'success')
    return redirect(url_for('usuarios.listar'))