from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.modules.coordinacion.models import Coordinacion
from app.database import db
import re
import pandas as pd

coordinacion_bp = Blueprint('coordinacion', __name__)

@coordinacion_bp.before_request
@login_required
def verificar_permisos():
    roles_permitidos = ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']
    if current_user.rol not in roles_permitidos:
        flash('No tiene permisos para acceder a este módulo.', 'danger')
        return redirect(url_for('main.dashboard'))


@coordinacion_bp.route('/')
def listar_coordinaciones():
    coordinaciones = Coordinacion.query.order_by(Coordinacion.id.asc()).all()
    return render_template('coordinacion/lista.html', coordinaciones=coordinaciones)


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
        except Exception as e:
            db.session.rollback()
            print(f"Error al guardar coordinación: {e}")
            flash('Error al guardar en la base de datos.', 'danger')
            return render_template('coordinacion/crear.html')

    return render_template('coordinacion/crear.html')


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
            existente = Coordinacion.query.filter_by(nombre=nombre).first()
            if existente and existente.id != coordinacion.id:
                flash(f'Ya existe otra coordinación con el nombre "{nombre}".', 'danger')
                return render_template('coordinacion/editar.html', coordinacion=coordinacion)

            coordinacion.nombre = nombre
            db.session.commit()
            flash('Coordinación actualizada.', 'success')
            return redirect(url_for('coordinacion.listar_coordinaciones'))
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar coordinación: {e}")
            flash('Error al actualizar.', 'danger')

    return render_template('coordinacion/editar.html', coordinacion=coordinacion)


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


@coordinacion_bp.route('/importar', methods=['GET', 'POST'])
@login_required
def importar_excel():
    if current_user.rol != 'ADMIN':
        flash('No tienes permisos para importar coordinaciones.', 'danger')
        return redirect(url_for('coordinacion.listar_coordinaciones'))

    if request.method == 'POST':
        file = request.files.get('file')

        if not file or file.filename == '':
            flash('Por favor seleccione un archivo Excel.', 'warning')
            return redirect(request.url)

        try:
            df = pd.read_excel(file, dtype=str).fillna('')
            df.columns = df.columns.str.strip()

            columnas_requeridas = {'Nombre'}
            if not columnas_requeridas.issubset(set(df.columns)):
                flash('El Excel debe contener la columna "Nombre".', 'danger')
                return redirect(request.url)

            agregadas = 0
            duplicadas = 0
            errores = 0

            for index, row in df.iterrows():
                try:
                    nombre = str(row['Nombre']).strip()

                    if not nombre:
                        errores += 1
                        continue

                    if len(nombre) < 5 or not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$", nombre):
                        errores += 1
                        continue

                    if Coordinacion.query.filter_by(nombre=nombre).first():
                        duplicadas += 1
                        continue

                    nueva = Coordinacion(nombre=nombre)
                    db.session.add(nueva)
                    agregadas += 1

                except Exception as e:
                    print(f"Error en fila {index}: {e}")
                    errores += 1

            db.session.commit()
            flash(
                f'Importación terminada. Agregadas: {agregadas}, Duplicadas: {duplicadas}, Errores: {errores}.',
                'success'
            )
            return redirect(url_for('coordinacion.listar_coordinaciones'))

        except Exception as e:
            db.session.rollback()
            print(f"Error general importando coordinaciones: {e}")
            flash(f'Error al procesar el archivo: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('coordinacion/importar.html')