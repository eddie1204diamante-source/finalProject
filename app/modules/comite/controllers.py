from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.modules.comite.models import Comite
from app.modules.aprendiz.models import Aprendiz
from app.modules.instructor.models import Instructor
from app.modules.auth.models import Usuario  
from datetime import datetime, date

comite_bp = Blueprint('comite', __name__)

def clean_int(value):
    """Convierte entrada de formulario a entero o None"""
    if value and str(value).strip().isdigit():
        return int(value)
    return None

def preparar_datos_aprendiz(aprendiz):
    """Calcula edad y normaliza atributos para el banner de información"""
    if not aprendiz:
        return None
    
    # 1. Cálculo de edad
    if hasattr(aprendiz, 'fecha_nacimiento') and aprendiz.fecha_nacimiento:
        hoy = date.today()
        aprendiz.edad = hoy.year - aprendiz.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (aprendiz.fecha_nacimiento.month, aprendiz.fecha_nacimiento.day)
        )
    else:
        aprendiz.edad = "N/A"
    
    # 2. Mapeo de atributos (Base de datos -> Vista)
    # Se usa getattr por si el campo no existe en el modelo legacy
    aprendiz.email = getattr(aprendiz, 'correo', 'N/A')
    aprendiz.telefono = getattr(aprendiz, 'celular', 'N/A')
    return aprendiz

@comite_bp.route('/')
@login_required
def listar():
    comites = Comite.query.order_by(Comite.id.asc()).all()
    return render_template('comite/lista.html', comites=comites)

@comite_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if current_user.rol not in ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']:
        flash('No tiene permisos para acceder al módulo de comités.', 'danger')
        return redirect(url_for('main.dashboard'))

    profesionales = Usuario.query.filter(Usuario.rol.in_(['PSICOLOGA', 'T_SOCIAL']), Usuario.enabled.is_(True)).all()
    instructores = Instructor.query.filter_by(activo=1).all()

    aprendiz = None
    vocero = None
    documento = request.args.get('documento', '').strip()
    
    if documento:
        aprendiz = Aprendiz.query.filter_by(numero_documento=documento).first()
        
        if not aprendiz:
            flash(f'No se encontró ningún aprendiz con el documento: {documento}', 'danger')
            return render_template('comite/crear.html', instructores=instructores, profesionales=profesionales, documento=documento)
        
        if aprendiz.es_vocero:
            flash(f'Atención: {aprendiz.nombres} es vocero activo. No se puede citar a comité a un vocero.', 'warning')
            return render_template('comite/crear.html', instructores=instructores, profesionales=profesionales, documento=documento)
        
        # Preparar datos para el banner
        aprendiz = preparar_datos_aprendiz(aprendiz)
        
        vocero = Aprendiz.query.filter_by(
            ficha_id=aprendiz.ficha_id, 
            es_vocero=True, 
            activo=True
        ).first()

    if request.method == 'POST':
        try:
            f_str = request.form.get('fecha')
            fecha_comite = datetime.strptime(f_str, '%Y-%m-%d').date() if f_str else None
            hoy = date.today()
            
            # Validación de Regla del Día 20
            if fecha_comite:
                if hoy.day > 20:
                    # Debe ser el mes siguiente
                    proximo_mes = hoy.month + 1 if hoy.month < 12 else 1
                    if fecha_comite.month != proximo_mes:
                        flash("Error: Después del día 20, la citación debe ser para el próximo mes.", "danger")
                        return redirect(url_for('comite.crear', documento=documento))
                else:
                    # Debe ser el mes actual
                    if fecha_comite.month != hoy.month:
                        flash("Error: Solo puede programar comités para el mes en curso.", "danger")
                        return redirect(url_for('comite.crear', documento=documento))

            nuevo_comite = Comite(
                fecha=fecha_comite,
                hora=datetime.strptime(request.form.get('hora'), '%H:%M').time() if request.form.get('hora') else None,
                sede=request.form.get('sede', '').strip() or 'Sede Principal',
                piso=request.form.get('piso', '').strip() or 'N/A',
                ambiente=request.form.get('ambiente', '').strip() or 'N/A',
                tipo_falta=request.form.get('tipo_falta'),
                motivo=request.form.get('motivo', '').strip(),
                recomendacion=request.form.get('recomendacion', '').strip(),
                plan_mejoramiento=request.form.get('plan_mejoramiento', '').strip(),
                representante_aprendices=request.form.get('representante_aprendices', '').strip(),
                profesional_bienestar=clean_int(request.form.get('profesional_bienestar')),
                aprendiz_id=clean_int(request.form.get('aprendiz_id')),
                ficha_id=clean_int(request.form.get('ficha_id')),
                instructor_id=clean_int(request.form.get('instructor_id')),
                coordinacion_id=clean_int(request.form.get('coordinacion_id')),
                usuario_id=current_user.id,
                fecha_plazo=datetime.strptime(request.form.get('fecha_plazo'), '%Y-%m-%d').date() if request.form.get('fecha_plazo') else None,
                observaciones=request.form.get('observaciones', '').strip(),
                paz_salvo=True if request.form.get('paz_salvo') == 'on' else False,
                activo=True
            )
            
            db.session.add(nuevo_comite)
            db.session.commit()
            flash('Comité registrado exitosamente.', 'success')
            return redirect(url_for('comite.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el comité: {str(e)}', 'danger')

    return render_template('comite/crear.html', 
                           aprendiz=aprendiz, 
                           vocero=vocero, 
                           instructores=instructores, 
                           profesionales=profesionales, 
                           documento=documento)

@comite_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if current_user.rol not in ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']:
        flash('No tiene permisos para editar comités.', 'danger')
        return redirect(url_for('comite.listar'))

    comite = Comite.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            f_str = request.form.get('fecha')
            nueva_fecha = datetime.strptime(f_str, '%Y-%m-%d').date() if f_str else None
            hoy = date.today()
            
            # Validación de Regla del Día 20 (Servidor)
            if nueva_fecha:
                if hoy.day > 20:
                    proximo_mes = hoy.month + 1 if hoy.month < 12 else 1
                    if nueva_fecha.month != proximo_mes:
                        flash("Error: El plazo para este mes venció (día 20). Elija el próximo mes.", "danger")
                        return redirect(url_for('comite.editar', id=id))
                else:
                    if nueva_fecha.month != hoy.month:
                        flash("Error: La fecha debe pertenecer al mes actual.", "danger")
                        return redirect(url_for('comite.editar', id=id))

            # Actualización de campos
            comite.fecha = nueva_fecha
            comite.hora = datetime.strptime(request.form.get('hora'), '%H:%M').time() if request.form.get('hora') else comite.hora
            comite.sede = request.form.get('sede', '').strip()
            comite.piso = request.form.get('piso', '').strip()
            comite.ambiente = request.form.get('ambiente', '').strip()
            comite.tipo_falta = request.form.get('tipo_falta')
            comite.motivo = request.form.get('motivo', '').strip()
            comite.recomendacion = request.form.get('recomendacion', '').strip()
            comite.plan_mejoramiento = request.form.get('plan_mejoramiento', '').strip()
            comite.profesional_bienestar = clean_int(request.form.get('profesional_bienestar'))
            comite.instructor_id = clean_int(request.form.get('instructor_id'))
            
            fp_str = request.form.get('fecha_plazo')
            comite.fecha_plazo = datetime.strptime(fp_str, '%Y-%m-%d').date() if fp_str else None
            
            comite.observaciones = request.form.get('observaciones', '').strip()
            comite.paz_salvo = True if request.form.get('paz_salvo') == 'on' else False
            
            db.session.commit()
            flash('Comité actualizado correctamente.', 'success')
            return redirect(url_for('comite.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
            return redirect(url_for('comite.editar', id=id))

    # Carga de datos para el banner y selects
    profesionales = Usuario.query.filter(Usuario.rol.in_(['PSICOLOGA', 'T_SOCIAL']), Usuario.enabled.is_(True)).all()
    instructores = Instructor.query.filter_by(activo=1).all()
    
    # Normalizamos el aprendiz del comité para el banner
    aprendiz = preparar_datos_aprendiz(comite.aprendiz)
    
    return render_template('comite/editar.html', 
                           comite=comite, 
                           aprendiz=aprendiz, 
                           profesionales=profesionales, 
                           instructores=instructores)

@comite_bp.route('/cambiar_estado/<int:id>')
@login_required
def cambiar_estado(id):
    if current_user.rol not in ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']:
        flash('No tiene permisos.', 'danger')
        return redirect(url_for('comite.listar'))
        
    comite = Comite.query.get_or_404(id)
    try:
        comite.activo = not getattr(comite, 'activo', True)
        db.session.commit()
        flash(f'Estado actualizado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        
    return redirect(url_for('comite.listar'))