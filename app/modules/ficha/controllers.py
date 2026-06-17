from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.modules.ficha.models import Ficha
from app.modules.coordinacion.models import Coordinacion # Importante para el SELECT

# Definimos el prefijo para que las URLs sean coherentes
ficha_bp = Blueprint('ficha', __name__, url_prefix='/fichas')

@ficha_bp.route('/')
@login_required
def listar_fichas():
    if current_user.rol not in ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']:
        return redirect(url_for('main.dashboard'))
    
    # AJUSTE: Cambiamos Ficha.codigo.asc() por Ficha.id.asc() para arreglar el desorden
    fichas = Ficha.query.order_by(Ficha.id.asc()).all()
    return render_template('ficha/lista.html', fichas=fichas)

@ficha_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_ficha():
    if current_user.rol != 'ADMIN':
        flash('No tienes permiso para realizar esta acción.', 'error')
        return redirect(url_for('ficha.listar_fichas'))

    # Obtenemos coordinaciones activas para el formulario
    coordinaciones = Coordinacion.query.filter_by(activo=1).all()

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        programa = request.form.get('programa', '').strip()
        jornada = request.form.get('jornada', '').strip()
        modalidad = request.form.get('modalidad', '').strip()
        coord_id = request.form.get('coordinacion_id')

        # VALIDACIÓN: Campos vacíos (incluyendo coordinación)
        if not all([codigo, programa, jornada, modalidad, coord_id]):
            flash('Error: Todos los campos son obligatorios.', 'error')
            return render_template('ficha/crear.html', coordinaciones=coordinaciones)

        # VALIDACIÓN: Duplicados
        if Ficha.query.filter_by(codigo=codigo).first():
            flash(f'El código {codigo} ya existe. Intenta con otro.', 'error')
            return render_template('ficha/crear.html', coordinaciones=coordinaciones)

        try:
            nueva_ficha = Ficha(
                codigo=codigo,
                programa=programa,
                jornada=jornada,
                modalidad=modalidad,
                coordinacion_id=coord_id,
                activo=1 # 1 para Activo según tu modelo
            )
            db.session.add(nueva_ficha)
            db.session.commit()
            flash('Ficha guardada correctamente.', 'success')
            return redirect(url_for('ficha.listar_fichas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar la solicitud: {str(e)}', 'error')

    return render_template('ficha/crear.html', coordinaciones=coordinaciones)

@ficha_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_ficha(id):
    if current_user.rol != 'ADMIN':
        flash('Acceso denegado.', 'error')
        return redirect(url_for('ficha.listar_fichas'))

    f = Ficha.query.get_or_404(id)
    coordinaciones = Coordinacion.query.filter_by(activo=1).all()

    if request.method == 'POST':
        codigo_n = request.form.get('codigo', '').strip()
        programa_n = request.form.get('programa', '').strip()
        jornada_n = request.form.get('jornada', '').strip()
        modalidad_n = request.form.get('modalidad', '').strip()
        coord_id_n = request.form.get('coordinacion_id')

        if not all([codigo_n, programa_n, jornada_n, modalidad_n, coord_id_n]):
            flash('Error: Los campos no pueden quedar vacíos.', 'error')
            return render_template('ficha/editar.html', f=f, coordinaciones=coordinaciones)

        # Validación de duplicidad inteligente
        if codigo_n != f.codigo:
            if Ficha.query.filter_by(codigo=codigo_n).first():
                flash(f'Error: El código {codigo_n} ya pertenece a otra ficha.', 'error')
                return render_template('ficha/editar.html', f=f, coordinaciones=coordinaciones)

        try:
            f.codigo = codigo_n
            f.programa = programa_n
            f.jornada = jornada_n
            f.modalidad = modalidad_n
            f.coordinacion_id = coord_id_n
            
            db.session.commit()
            flash('Ficha actualizada correctamente.', 'success')
            return redirect(url_for('ficha.listar_fichas'))
        except Exception:
            db.session.rollback()
            flash('Error interno al actualizar la ficha.', 'error')

    return render_template('ficha/editar.html', f=f, coordinaciones=coordinaciones)

@ficha_bp.route('/cambiar-estado/<int:id>')
@login_required
def cambiar_estado(id):
    if current_user.rol != 'ADMIN':
        flash('No tienes permiso.', 'error')
        return redirect(url_for('ficha.listar_fichas'))

    ficha = Ficha.query.get_or_404(id)
    
    # Lógica de switch para Integer (1/0)
    ficha.activo = 0 if ficha.activo == 1 else 1
    
    try:
        db.session.commit()
        estado = "activada" if ficha.activo == 1 else "inactivada"
        flash(f'Ficha {estado} correctamente.', 'success')
    except Exception:
        db.session.rollback()
        flash('No se pudo cambiar el estado.', 'error')
        
    return redirect(url_for('ficha.listar_fichas'))