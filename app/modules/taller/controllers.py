from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.modules.taller.models import Taller
from app.modules.instructor.models import Instructor
from app.database import db
from datetime import datetime, date

talleres_bp = Blueprint('talleres', __name__, template_folder='templates')

# ========== FUNCIONES DE VALIDACIÓN ==========
def validar_instructor(nombre_completo):
    """Verifica que el instructor exista y esté activo."""
    instructor = Instructor.query.filter(
        Instructor.nombres + ' ' + Instructor.apellidos == nombre_completo,
        Instructor.activo == True
    ).first()
    return instructor is not None

def validar_nombre_taller(nombre):
    if not nombre or len(nombre.strip()) < 3:
        return False, "El nombre debe tener al menos 3 caracteres."
    if nombre.isdigit():
        return False, "El nombre no puede ser solo números."
    return True, ""

def validar_descripcion(descripcion):
    if descripcion and len(descripcion) > 5000:
        return False, "La descripción no puede exceder los 5000 caracteres."
    return True, ""

def validar_fecha(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    except ValueError:
        return None, False, "Formato de fecha inválido. Use YYYY-MM-DD."
    hoy = date.today()
    if fecha.date() < hoy:
        return None, False, "La fecha no puede ser anterior a hoy."
    if fecha.date() > hoy.replace(year=hoy.year + 2):
        return None, False, "No se pueden programar talleres con más de 2 años de anticipación."
    return fecha, True, ""

def evitar_duplicado(instructor, fecha, id_excluir=None):
    query = Taller.query.filter(
        Taller.instructor == instructor,
        Taller.fecha_programada == fecha,
        Taller.estado != 'Cancelado'
    )
    if id_excluir:
        query = query.filter(Taller.id != id_excluir)
    return query.first() is not None

# ========== RUTAS ==========
@talleres_bp.route('/')
@login_required
def index():
    # Actualizar talleres pasados a 'Realizado'
    hoy = date.today()
    talleres_programados = Taller.query.filter(
        Taller.estado == 'Programado',
        Taller.fecha_programada < hoy
    ).all()
    for t in talleres_programados:
        t.estado = 'Realizado'
    db.session.commit()

    todos = Taller.query.order_by(Taller.id.desc()).all()
    return render_template('taller/lista.html', talleres=todos)

@talleres_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        instructor = request.form.get('instructor', '').strip()
        fecha_str = request.form.get('fecha_programada', '').strip()

        # Validaciones
        if not nombre or not instructor or not fecha_str:
            flash('Todos los campos son obligatorios.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

        valido, msg = validar_nombre_taller(nombre)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

        valido, msg = validar_descripcion(descripcion)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

        fecha, valido, msg = validar_fecha(fecha_str)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

        if not validar_instructor(instructor):
            flash('El instructor seleccionado no es válido o no está activo.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

        if evitar_duplicado(instructor, fecha):
            flash('El instructor ya tiene un taller programado (no cancelado) en esta fecha.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

        try:
            nuevo = Taller(
                nombre=nombre,
                descripcion=descripcion,
                instructor=instructor,
                fecha_programada=fecha,
                estado='Programado'
            )
            db.session.add(nuevo)
            db.session.commit()
            flash('¡Taller programado con éxito!', 'success')
            return redirect(url_for('talleres.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

    instructores = Instructor.query.filter_by(activo=True).all()
    return render_template('taller/crear.html', instructores=instructores, hoy=date.today().isoformat())

@talleres_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    taller = Taller.query.get_or_404(id)
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        instructor = request.form.get('instructor', '').strip()
        fecha_str = request.form.get('fecha_programada', '').strip()
        nuevo_estado = request.form.get('estado', taller.estado)

        # Validaciones
        if not nombre or not instructor or not fecha_str:
            flash('Todos los campos son obligatorios.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

        valido, msg = validar_nombre_taller(nombre)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

        valido, msg = validar_descripcion(descripcion)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

        fecha, valido, msg = validar_fecha(fecha_str)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

        if not validar_instructor(instructor):
            flash('El instructor seleccionado no es válido o no está activo.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

        if evitar_duplicado(instructor, fecha, id_excluir=id):
            flash('El instructor ya tiene otro taller programado (no cancelado) en esta fecha.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

        hoy = date.today()
        if nuevo_estado == 'Realizado' and fecha.date() > hoy:
            flash('No se puede marcar como Realizado un taller con fecha futura.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())
        if nuevo_estado == 'Programado' and fecha.date() < hoy:
            flash('No se puede programar un taller con fecha pasada.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

        # Actualizar
        taller.nombre = nombre
        taller.descripcion = descripcion
        taller.instructor = instructor
        taller.fecha_programada = fecha
        taller.estado = nuevo_estado

        try:
            db.session.commit()
            flash('Taller actualizado correctamente.', 'success')
            return redirect(url_for('talleres.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

    instructores = Instructor.query.filter_by(activo=True).all()
    return render_template('taller/editar.html', taller=taller, instructores=instructores, hoy=date.today().isoformat())

@talleres_bp.route('/cambiar-estado/<int:id>', methods=['POST'])
@login_required
def cambiar_estado(id):
    taller = Taller.query.get_or_404(id)
    hoy = date.today()

    if taller.estado != 'Cancelado':
        taller.estado = 'Cancelado'
        flash(f'Taller "{taller.nombre}" cancelado.', 'warning')
    else:
        if taller.fecha_programada.date() < hoy:
            flash('No se puede reactivar un taller con fecha pasada.', 'danger')
            return redirect(url_for('talleres.index'))
        if evitar_duplicado(taller.instructor, taller.fecha_programada, id_excluir=id):
            flash('No se puede reactivar porque el instructor ya tiene otro taller en esa fecha.', 'danger')
            return redirect(url_for('talleres.index'))
        taller.estado = 'Programado'
        flash(f'Taller "{taller.nombre}" reactivado.', 'success')

    db.session.commit()
    return redirect(url_for('talleres.index'))