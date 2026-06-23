from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.modules.aprendiz.models import Aprendiz
from app.modules.ficha.models import Ficha
from datetime import datetime, date, timedelta
import pandas as pd 

# Blueprint nombrado como 'aprendices' para coincidir con el Dashboard
aprendiz_bp = Blueprint('aprendices', __name__, url_prefix='/aprendices')

@aprendiz_bp.route('/')
@login_required
def listar():
    """Lista todos los aprendices registrados calculando su edad para la vista."""
    aprendices = Aprendiz.query.order_by(Aprendiz.id.asc()).all()
    hoy = date.today()
    
    for a in aprendices:
        if a.fecha_nacimiento:
            a.edad = hoy.year - a.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (a.fecha_nacimiento.month, a.fecha_nacimiento.day)
            )
        else:
            a.edad = "N/A"
            
    return render_template('aprendiz/lista.html', aprendices=aprendices)

@aprendiz_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_aprendiz():
    """Registro de nuevos aprendices con validación estricta en el servidor."""
    if current_user.rol != 'ADMIN':
        flash('Acceso denegado: Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('aprendices.listar'))

    fichas = Ficha.query.filter_by(activo=1).all()
    hoy = date.today()
    max_date_val = (hoy - timedelta(days=16*365.25)).isoformat()
    min_date_val = (hoy - timedelta(days=90*365.25)).isoformat()
    
    if request.method == 'POST':
        tdoc = request.form.get('tipo_documento')
        ndoc = request.form.get('numero_documento', '').strip()
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        f_nac_str = request.form.get('fecha_nacimiento')
        correo = request.form.get('correo', '').strip()
        celular = request.form.get('celular', '').strip()
        f_id = request.form.get('ficha_id')
        etapa = request.form.get('etapa_formacion')
        es_v = 1 if request.form.get('es_vocero') else 0

        if not all([tdoc, ndoc, nombres, apellidos, f_nac_str, correo, celular, f_id, etapa]):
            flash('Error Nexus: Todos los campos son obligatorios.', 'danger')
            return render_template('aprendiz/crear.html', fichas=fichas, max_date=max_date_val, min_date=min_date_val)

        try:
            f_nac = datetime.strptime(f_nac_str, '%Y-%m-%d').date()
            if Aprendiz.query.filter_by(numero_documento=ndoc).first():
                flash(f'Error: El documento {ndoc} ya está registrado.', 'danger')
                return redirect(request.url)

            nuevo = Aprendiz(
                tipo_documento=tdoc, numero_documento=ndoc, nombres=nombres,
                apellidos=apellidos, fecha_nacimiento=f_nac, correo=correo,
                celular=celular, ficha_id=f_id, etapa_formacion=etapa, es_vocero=es_v
            )
            db.session.add(nuevo)
            db.session.commit()
            flash('Aprendiz registrado exitosamente.', 'success')
            return redirect(url_for('aprendices.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error Crítico: {str(e)}', 'danger')

    return render_template('aprendiz/crear.html', fichas=fichas, max_date=max_date_val, min_date=min_date_val)

@aprendiz_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aprendiz(id):
    """Actualización de datos existentes con validación de integridad."""
    if current_user.rol != 'ADMIN':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('aprendices.listar'))

    a = Aprendiz.query.get_or_404(id)
    fichas = Ficha.query.filter_by(activo=1).all()
    hoy = date.today()
    max_date_val = (hoy - timedelta(days=16*365.25)).isoformat()
    min_date_val = (hoy - timedelta(days=90*365.25)).isoformat()

    if request.method == 'POST':
        try:
            a.nombres = request.form.get('nombres', '').strip()
            a.apellidos = request.form.get('apellidos', '').strip()
            a.correo = request.form.get('correo', '').strip()
            a.celular = request.form.get('celular', '').strip()
            a.ficha_id = request.form.get('ficha_id')
            a.etapa_formacion = request.form.get('etapa_formacion')
            a.es_vocero = 1 if request.form.get('es_vocero') else 0
            
            db.session.commit()
            flash('Datos actualizados con éxito.', 'success')
            return redirect(url_for('aprendices.listar'))
        except Exception:
            db.session.rollback()
            flash('Error al actualizar registro.', 'danger')

    return render_template('aprendiz/editar.html', a=a, fichas=fichas, max_date=max_date_val, min_date=min_date_val)

@aprendiz_bp.route('/cambiar-estado/<int:id>')
@login_required
def cambiar_estado(id):
    """Cambia el estado de activo/inactivo."""
    if current_user.rol != 'ADMIN':
        flash('No autorizado.', 'danger')
        return redirect(url_for('aprendices.listar'))
    
    a = Aprendiz.query.get_or_404(id)
    if a.activo == 1 and a.es_vocero == 1:
        flash(f'Error: {a.nombres} es VOCERO. No puede ser inactivado.', 'warning')
        return redirect(url_for('aprendices.listar'))
    
    a.activo = 0 if a.activo == 1 else 1
    db.session.commit()
    flash('Estado actualizado.', 'success')
    return redirect(url_for('aprendices.listar'))

@aprendiz_bp.route('/importar', methods=['GET', 'POST'])
@login_required
def importar_excel():
    """Importación masiva de aprendices usando Pandas."""
    if current_user.rol != 'ADMIN':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('aprendices.listar'))

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Por favor seleccione un archivo.', 'warning')
            return redirect(request.url)

        try:
            # Leer excel asegurando que todo sea string para evitar errores de formato
            df = pd.read_excel(file, dtype=str)
            df.columns = df.columns.str.strip() # Limpiar espacios en encabezados

            agregados = 0
            errores = 0

            for index, row in df.iterrows():
                try:
                    # Limpiamos Ficha y Documento por si traen .0
                    cod_ficha = str(row['Ficha']).strip().split('.')[0]
                    ndoc = str(row['Documento']).strip().split('.')[0]

                    # Buscamos la ficha
                    ficha_obj = Ficha.query.filter_by(codigo=cod_ficha).first()
                    if not ficha_obj:
                        errores += 1
                        continue

                    # Evitamos duplicados
                    if Aprendiz.query.filter_by(numero_documento=ndoc).first():
                        continue

                    # CREACIÓN DEL REGISTRO
                    nuevo = Aprendiz(
                        tipo_documento=row.get('Tipo', 'CC'),
                        numero_documento=ndoc,
                        nombres=str(row['Nombres']).strip().upper(),
                        apellidos=str(row['Apellidos']).strip().upper(),
                        # AQUÍ ESTÁ EL TRUCO: Tomamos solo los primeros 10 caracteres
                        fecha_nacimiento=datetime.strptime(str(row['Nacimiento'])[:10], '%Y-%m-%d').date(),
                        etapa_formacion=row.get('Etapa', 'LECTIVA'),
                        correo=str(row['Correo']).strip().lower(),
                        celular=str(row['Celular']).strip().split('.')[0],
                        ficha_id=ficha_obj.id,
                        activo=1,
                        es_vocero=0
                    )
                    db.session.add(nuevo)
                    agregados += 1
                except Exception as e:
                    print(f"Error en fila {index}: {str(e)}")
                    errores += 1

            db.session.commit()
            flash(f'Proceso terminado. Agregados: {agregados}, Errores/Fichas no encontradas: {errores}', 'success')
            return redirect(url_for('aprendices.listar'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el archivo: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('aprendiz/importar.html')