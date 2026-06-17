from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.modules.instructor.models import Instructor
from app.modules.coordinacion.models import Coordinacion
from app import db
import re

# Definición del Blueprint con prefijo para rutas limpias
instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructores')

@instructor_bp.route('/')
@login_required
def listar_instructores():
    # Restricción de acceso según roles definidos en la migración Nexus
    if current_user.rol not in ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']:
        return redirect(url_for('main.dashboard'))
    
    instructores = Instructor.query.order_by(Instructor.id.asc()).all()
    return render_template('instructor/lista.html', instructores=instructores)

@instructor_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_instructor():
    if current_user.rol != 'ADMIN':
        flash('No tienes permisos para registrar instructores.', 'danger')
        return redirect(url_for('instructor.listar_instructores'))
    
    coordinaciones = Coordinacion.query.filter_by(activo=True).all()
    
    if request.method == 'POST':
        # 1. Captura y limpieza
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        tipo_doc = request.form.get('tipo_documento')
        num_doc = request.form.get('numero_documento', '').strip()
        profesion = request.form.get('profesion', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        coord_id = request.form.get('coordinacion_id')

        # 2. Validaciones de Servidor (Obligatorias)
        if not all([nombres, apellidos, tipo_doc, num_doc, profesion, correo, telefono, coord_id]):
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('instructor.crear_instructor'))

        if len(num_doc) > 15:
            flash('El documento no puede exceder los 15 caracteres.', 'danger')
            return redirect(url_for('instructor.crear_instructor'))

        if len(telefono) != 10 or not telefono.isdigit():
            flash('El teléfono debe tener exactamente 10 dígitos numéricos.', 'danger')
            return redirect(url_for('instructor.crear_instructor'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
            flash('El formato del correo electrónico es inválido.', 'danger')
            return redirect(url_for('instructor.crear_instructor'))

        # 3. Verificación de Duplicados
        if Instructor.query.filter_by(numero_documento=num_doc).first():
            flash(f'El documento {num_doc} ya está registrado.', 'danger')
        elif Instructor.query.filter_by(correo=correo).first():
            flash(f'El correo {correo} ya está registrado.', 'danger')
        else:
            try:
                nuevo = Instructor(
                    tipo_documento=tipo_doc, numero_documento=num_doc,
                    nombres=nombres, apellidos=apellidos, profesion=profesion,
                    correo=correo, telefono=telefono, coordinacion_id=coord_id
                )
                db.session.add(nuevo)
                db.session.commit()
                flash('Instructor guardado correctamente.', 'success')
                return redirect(url_for('instructor.listar_instructores'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error en base de datos: {str(e)}', 'danger')
                
    return render_template('instructor/crear.html', coordinaciones=coordinaciones)

@instructor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_instructor(id):
    if current_user.rol != 'ADMIN':
        flash('No tienes permiso para editar.', 'danger')
        return redirect(url_for('instructor.listar_instructores'))
    
    instructor = Instructor.query.get_or_404(id)
    coordinaciones = Coordinacion.query.filter_by(activo=True).all()
    
    if request.method == 'POST':
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        tipo_doc = request.form.get('tipo_documento')
        num_doc = request.form.get('numero_documento', '').strip()
        profesion = request.form.get('profesion', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        coord_id = request.form.get('coordinacion_id')

        # Validaciones de integridad
        if not all([nombres, apellidos, tipo_doc, num_doc, profesion, correo, telefono, coord_id]):
            flash('Faltan campos obligatorios.', 'danger')
            return render_template('instructor/editar.html', instructor=instructor, coordinaciones=coordinaciones)

        # Validación de duplicados excluyendo al actual (Lógica de Actualización)
        doc_existe = Instructor.query.filter(Instructor.numero_documento == num_doc, Instructor.id != id).first()
        email_existe = Instructor.query.filter(Instructor.correo == correo, Instructor.id != id).first()

        if doc_existe:
            flash(f'El documento {num_doc} ya lo tiene otro instructor.', 'danger')
        elif email_existe:
            flash(f'El correo {correo} ya está en uso.', 'danger')
        else:
            try:
                instructor.tipo_documento = tipo_doc
                instructor.numero_documento = num_doc
                instructor.nombres = nombres
                instructor.apellidos = apellidos
                instructor.profesion = profesion
                instructor.correo = correo
                instructor.telefono = telefono
                instructor.coordinacion_id = coord_id

                db.session.commit()
                flash('Instructor actualizado correctamente.', 'success')
                return redirect(url_for('instructor.listar_instructores'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('instructor/editar.html', instructor=instructor, coordinaciones=coordinaciones)

@instructor_bp.route('/cambiar-estado/<int:id>')
@login_required
def cambiar_estado(id):
    if current_user.rol != 'ADMIN':
        flash('Acción no permitida.', 'danger')
        return redirect(url_for('instructor.listar_instructores'))
    
    instructor = Instructor.query.get_or_404(id)
    instructor.activo = not instructor.activo
    db.session.commit()
    flash('Estado actualizado correctamente.', 'success')
    return redirect(url_for('instructor.listar_instructores'))