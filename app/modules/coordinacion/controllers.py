from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
# CAMBIO CLAVE: Rutas absolutas para que Python no lance ModuleNotFoundError
from app.modules.coordinacion.models import Coordinacion 
from app.database import db
import re

coordinacion_bp = Blueprint('coordinacion', __name__)

@coordinacion_bp.before_request
@login_required
def verificar_permisos():
    roles_permitidos = ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']
    if current_user.rol not in roles_permitidos:
        flash('No tiene permisos para acceder a este módulo.', 'danger')
        return redirect(url_for('main.dashboard'))

# AJUSTE: Se cambió '/coordinaciones' por '/'
@coordinacion_bp.route('/')
def listar_coordinaciones(): 
    coordinaciones = Coordinacion.query.order_by(Coordinacion.id.asc()).all()
    # Ajustado a tu nombre de carpeta: coordinacion
    return render_template('coordinacion/lista.html', coordinaciones=coordinaciones)

# AJUSTE: Se quitó el prefijo repetido
@coordinacion_bp.route('/crear', methods=['GET', 'POST'])
def crear_coordinacion():
    if current_user.rol != 'ADMIN':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('coordinacion.listar_coordinaciones'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        
        if len(nombre) < 5 or not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$", nombre):
            flash('Nombre inválido: Mínimo 5 caracteres, solo letras y espacios.', 'danger')
            return render_template('coordinacion/crear.html')

        if Coordinacion.query.filter_by(nombre=nombre).first():
            flash(f'La coordinación "{nombre}" ya existe.', 'danger')
            return render_template('coordinacion/crear.html')

        try:
            nueva_coord = Coordinacion(nombre=nombre)
            db.session.add(nueva_coord)
            db.session.commit()
            flash('Coordinación guardada correctamente.', 'success')
            return redirect(url_for('coordinacion.listar_coordinaciones'))
        except Exception:
            db.session.rollback()
            flash('Error al guardar en la base de datos.', 'danger')
            return render_template('coordinacion/crear.html')

    return render_template('coordinacion/crear.html')

# AJUSTE: Se quitó el prefijo repetido
@coordinacion_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_coordinacion(id):
    if current_user.rol != 'ADMIN':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('coordinacion.listar_coordinaciones'))

    coordinacion = Coordinacion.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        
        if len(nombre) < 5 or not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$", nombre):
            flash('Validación fallida: Verifique el nombre.', 'danger')
            return render_template('coordinacion/editar.html', coordinacion=coordinacion)

        try:
            coordinacion.nombre = nombre
            db.session.commit()
            flash('Coordinación actualizada.', 'success')
            return redirect(url_for('coordinacion.listar_coordinaciones'))
        except Exception:
            db.session.rollback()
            flash('Error al actualizar.', 'danger')

    return render_template('coordinacion/editar.html', coordinacion=coordinacion)

# AJUSTE: Se quitó el prefijo repetido
@coordinacion_bp.route('/cambiar-estado/<int:id>')
def cambiar_estado(id):
    if current_user.rol != 'ADMIN':
        flash('No autorizado.', 'danger')
        return redirect(url_for('coordinacion.listar_coordinaciones'))
    
    coord = Coordinacion.query.get_or_404(id)
    coord.activo = not coord.activo 
    db.session.commit()
    flash('Estado de la coordinación actualizado.', 'success')
    return redirect(url_for('coordinacion.listar_coordinaciones'))