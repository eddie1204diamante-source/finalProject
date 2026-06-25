from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.modules.taller.models import Taller
from app.modules.instructor.models import Instructor
from app.database import db
from datetime import datetime, date

talleres_bp = Blueprint('talleres', __name__, template_folder='templates')


# ========== FUNCIONES DE VALIDACIÓN ==========
def obtener_instructor_activo(instructor_id):
    """Obtiene un instructor por ID y verifica que esté activo."""
    try:
        instructor_id = int(instructor_id)
    except (TypeError, ValueError):
        return None

    return Instructor.query.filter_by(id=instructor_id, activo=True).first()


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


def validar_aforo(aforo_str):
    try:
        aforo = int(aforo_str)
        if aforo <= 0:
            return None, False, "El aforo debe ser mayor a 0."
        if aforo > 1000:
            return None, False, "El aforo no puede ser mayor a 1000."
        return aforo, True, ""
    except (TypeError, ValueError):
        return None, False, "El aforo debe ser un número entero."


def validar_asistentes(asistentes_str, aforo):
    try:
        asistentes = int(asistentes_str)
        if asistentes < 0:
            return None, False, "Los asistentes no pueden ser negativos."
        if asistentes > aforo:
            return None, False, "Los asistentes no pueden superar el aforo."
        return asistentes, True, ""
    except (TypeError, ValueError):
        return None, False, "Los asistentes deben ser un número entero."


def evitar_duplicado(instructor_id, fecha, id_excluir=None):
    try:
        instructor_id = int(instructor_id)
    except (TypeError, ValueError):
        return False

    query = Taller.query.filter(
        Taller.instructor_id == instructor_id,
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
    ahora = datetime.now()

    talleres_programados = Taller.query.filter(
        Taller.estado == 'Programado',
        Taller.fecha_programada < ahora
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
        instructor_id = request.form.get('instructor_id', '').strip()
        aforo_str = request.form.get('aforo', '').strip()
        fecha_str = request.form.get('fecha_programada', '').strip()

        if not nombre or not instructor_id or not aforo_str or not fecha_str:
            flash('Todos los campos son obligatorios.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        valido, msg = validar_nombre_taller(nombre)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        valido, msg = validar_descripcion(descripcion)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        fecha, valido, msg = validar_fecha(fecha_str)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        aforo, valido, msg = validar_aforo(aforo_str)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        instructor = obtener_instructor_activo(instructor_id)
        if not instructor:
            flash('El instructor seleccionado no es válido o no está activo.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        if evitar_duplicado(instructor.id, fecha):
            flash('El instructor ya tiene un taller programado (no cancelado) en esta fecha.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        try:
            nuevo = Taller(
                nombre=nombre,
                descripcion=descripcion,
                fecha_programada=fecha,
                instructor_id=instructor.id,
                aforo=aforo,
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
            return render_template(
                'taller/crear.html',
                instructores=instructores,
                hoy=date.today().isoformat()
            )

    instructores = Instructor.query.filter_by(activo=True).all()
    return render_template(
        'taller/crear.html',
        instructores=instructores,
        hoy=date.today().isoformat()
    )


@talleres_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    taller = Taller.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        instructor_id = request.form.get('instructor_id', '').strip()
        aforo_str = request.form.get('aforo', '').strip()
        fecha_str = request.form.get('fecha_programada', '').strip()
        nuevo_estado = request.form.get('estado', taller.estado)
        asistentes_str = request.form.get('asistentes', '0').strip()

        if not nombre or not instructor_id or not aforo_str or not fecha_str:
            flash('Todos los campos son obligatorios.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        valido, msg = validar_nombre_taller(nombre)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        valido, msg = validar_descripcion(descripcion)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        fecha, valido, msg = validar_fecha(fecha_str)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        aforo, valido, msg = validar_aforo(aforo_str)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        asistentes, valido, msg = validar_asistentes(asistentes_str, aforo)
        if not valido:
            flash(msg, 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        instructor = obtener_instructor_activo(instructor_id)
        if not instructor:
            flash('El instructor seleccionado no es válido o no está activo.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        if evitar_duplicado(instructor.id, fecha, id_excluir=id):
            flash('El instructor ya tiene otro taller programado (no cancelado) en esta fecha.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        ahora = datetime.now()

        if nuevo_estado == 'Realizado' and fecha > ahora:
            flash('No se puede marcar como Realizado un taller con fecha futura.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        if nuevo_estado == 'Programado' and fecha < ahora.replace(hour=0, minute=0, second=0, microsecond=0):
            flash('No se puede programar un taller con fecha pasada.', 'danger')
            instructores = Instructor.query.filter_by(activo=True).all()
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

        taller.nombre = nombre
        taller.descripcion = descripcion
        taller.instructor_id = instructor.id
        taller.aforo = aforo
        taller.asistentes = asistentes
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
            return render_template(
                'taller/editar.html',
                taller=taller,
                instructores=instructores,
                hoy=date.today().isoformat()
            )

    instructores = Instructor.query.filter_by(activo=True).all()
    return render_template(
        'taller/editar.html',
        taller=taller,
        instructores=instructores,
        hoy=date.today().isoformat()
    )


@talleres_bp.route('/cambiar-estado/<int:id>', methods=['POST'])
@login_required
def cambiar_estado(id):
    taller = Taller.query.get_or_404(id)
    hoy = date.today()

    if taller.estado != 'Cancelado':
        taller.estado = 'Cancelado'
        flash(f'El taller "{taller.nombre}" fue cancelado correctamente.', 'warning')
    else:
        if taller.fecha_programada.date() < hoy:
            flash('No se puede reactivar un taller con fecha pasada.', 'danger')
            return redirect(url_for('talleres.index'))

        if evitar_duplicado(taller.instructor_id, taller.fecha_programada, id_excluir=id):
            flash('No se puede reactivar porque el instructor ya tiene otro taller en esa fecha.', 'danger')
            return redirect(url_for('talleres.index'))

        taller.estado = 'Programado'
        flash(f'El taller "{taller.nombre}" fue reactivado correctamente.', 'success')

    db.session.commit()
    return redirect(url_for('talleres.index'))