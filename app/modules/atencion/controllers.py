from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.modules.atencion.models import Atencion
from app.modules.aprendiz.models import Aprendiz
from app.modules.auth.models import Usuario
from datetime import datetime, date
from sqlalchemy.orm import joinedload

atencion_bp = Blueprint('atencion', __name__, url_prefix='/atencion')


def clean_int(value):
    if value and str(value).strip().isdigit():
        return int(value)
    return None


def preparar_datos_aprendiz(aprendiz):
    if not aprendiz:
        return None
    if hasattr(aprendiz, 'fecha_nacimiento') and aprendiz.fecha_nacimiento:
        hoy = date.today()
        aprendiz.edad = hoy.year - aprendiz.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (aprendiz.fecha_nacimiento.month, aprendiz.fecha_nacimiento.day)
        )
    else:
        aprendiz.edad = "N/A"
    aprendiz.email = getattr(aprendiz, 'correo', 'N/A')
    aprendiz.telefono = getattr(aprendiz, 'celular', 'N/A')
    return aprendiz


@atencion_bp.route('/')
@login_required
def listar():
    atenciones = Atencion.query.options(joinedload(Atencion.profesional)).order_by(Atencion.id.asc()).all()
    return render_template('atencion/lista.html', atenciones=atenciones)


@atencion_bp.route('/crear', methods=['GET'])
@login_required
def crear():
    if current_user.rol not in ['ADMIN', 'PSICOLOGA', 'T_SOCIAL']:
        flash('No tiene permisos para acceder al módulo.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    profesionales = Usuario.query.filter(
        Usuario.rol.in_(['PSICOLOGA', 'T_SOCIAL']),
        Usuario.enabled.is_(True)
    ).all()

    aprendices_activos = Aprendiz.query.filter_by(
        activo=1
    ).order_by(
        Aprendiz.nombres
    ).all()

    documento = request.args.get('documento', '').strip()
    aprendiz = None
    
    if documento:
        aprendiz = Aprendiz.query.filter_by(numero_documento=documento).first()
        if not aprendiz:
            flash(f'No se encontró aprendiz con documento: {documento}', 'danger')
        else:
            aprendiz = preparar_datos_aprendiz(aprendiz)
            
    return render_template(
        'atencion/crear.html',
        profesionales=profesionales,
        aprendices_activos=aprendices_activos,
        aprendiz=aprendiz,
        documento=documento,
        errors={}
    )


@atencion_bp.route('/guardar', methods=['POST'])
@login_required
def guardar():
    errors = {}
    aprendiz_id = clean_int(request.form.get('aprendiz_id'))
    usuario_id = clean_int(request.form.get('usuario_id'))  # ID del profesional
    categoria = request.form.get('categoria_desercion')
    remitido = (request.form.get('remitido_por') or "").strip()
    estado = request.form.get('estado_caso')
    atencion_fam = (request.form.get('atencion_familiar') or "").strip()
    
    if not usuario_id:
        errors['usuario_id'] = "Debe seleccionar un profesional responsable."
    if not categoria:
        errors['categoria_desercion'] = "La categoría de deserción es obligatoria."
    if len(remitido) < 3:
        errors['remitido_por'] = "Indique quién remite (mínimo 3 caracteres)."
    if not estado:
        errors['estado_caso'] = "El estado del caso es obligatorio."

    aprendiz = Aprendiz.query.get(aprendiz_id) if aprendiz_id else None
    if aprendiz:
        aprendiz = preparar_datos_aprendiz(aprendiz)
        if isinstance(aprendiz.edad, int) and aprendiz.edad < 18:
            if not atencion_fam:
                atencion_fam = "No aplica (Menor de edad)"

    for i in range(1, 4):
        f_val = request.form.get(f'fecha_consulta_{i}')
        o_val = (request.form.get(f'observaciones_{i}') or "").strip()
        
        if i == 1:
            if not f_val:
                errors['fecha_consulta_1'] = "La fecha 1 es obligatoria."
            if len(o_val) < 3:
                errors['observaciones_1'] = "La observación 1 es obligatoria (mínimo 3 caracteres)."
        else:
            if f_val and len(o_val) < 3:
                errors[f'observaciones_{i}'] = f"Si hay fecha {i}, la observación no puede ser opcional."
            if len(o_val) >= 3 and not f_val:
                errors[f'fecha_consulta_{i}'] = f"Si registra observación {i}, la fecha es obligatoria."

    if errors:
        profesionales = Usuario.query.filter(
            Usuario.rol.in_(['PSICOLOGA', 'T_SOCIAL']),
            Usuario.enabled.is_(True)
        ).all()

        aprendices_activos = Aprendiz.query.filter_by(
            activo=1
        ).order_by(
            Aprendiz.nombres
        ).all()

        return render_template(
            'atencion/crear.html',
            profesionales=profesionales,
            aprendices_activos=aprendices_activos,
            aprendiz=aprendiz,
            documento=request.form.get('doc_temp'),
            errors=errors
        )

    try:
        def get_date(field):
            val = request.form.get(field)
            return datetime.strptime(val, '%Y-%m-%d').date() if val else None

        nueva_atencion = Atencion(
            aprendiz_id=aprendiz_id,
            usuario_id=usuario_id,
            estado_caso=estado,
            categoria_desercion=categoria,
            remitido_por=remitido,
            atencion_familiar=atencion_fam,
            fecha_consulta_1=get_date('fecha_consulta_1'),
            observaciones_1=request.form.get('observaciones_1'),
            fecha_consulta_2=get_date('fecha_consulta_2'),
            observaciones_2=request.form.get('observaciones_2'),
            fecha_consulta_3=get_date('fecha_consulta_3'),
            observaciones_3=request.form.get('observaciones_3'),
            activo=True
        )
        db.session.add(nueva_atencion)
        db.session.commit()
        flash('Atención registrada exitosamente.', 'success')
        return redirect(url_for('atencion.listar'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error de base de datos: {str(e)}', 'danger')
        return redirect(url_for('atencion.listar'))


@atencion_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    atencion = Atencion.query.get_or_404(id)
    profesionales = Usuario.query.filter(
        Usuario.rol.in_(['PSICOLOGA', 'T_SOCIAL']),
        Usuario.enabled.is_(True)
    ).all()
    aprendiz = preparar_datos_aprendiz(atencion.aprendiz)
    errors = {}

    if request.method == 'POST':
        usuario_id = clean_int(request.form.get('usuario_id'))
        remitido = (request.form.get('remitido_por') or "").strip()
        atencion_fam = (request.form.get('atencion_familiar') or "").strip()
        
        if not usuario_id:
            errors['usuario_id'] = "Debe asignar un profesional."
        if len(remitido) < 3:
            errors['remitido_por'] = "El campo Remitido Por es obligatorio (mínimo 3 caracteres)."
        
        if isinstance(aprendiz.edad, int) and aprendiz.edad < 18:
            if not atencion_fam:
                atencion_fam = "No aplica (Menor de edad)"

        for i in range(1, 4):
            f_val = request.form.get(f'fecha_consulta_{i}')
            o_val = (request.form.get(f'observaciones_{i}') or "").strip()
            if i == 1:
                if not f_val:
                    errors['fecha_consulta_1'] = "Fecha 1 requerida."
                if len(o_val) < 3:
                    errors['observaciones_1'] = "Observación 1 requerida (mínimo 3 caracteres)."
            else:
                if f_val and len(o_val) < 3:
                    errors[f'observaciones_{i}'] = f"La observación {i} es obligatoria si hay fecha."
                if len(o_val) >= 3 and not f_val:
                    errors[f'fecha_consulta_{i}'] = f"La fecha {i} es obligatoria si hay observación."

        if not errors:
            try:
                atencion.estado_caso = request.form.get('estado_caso')
                atencion.categoria_desercion = request.form.get('categoria_desercion')
                atencion.usuario_id = usuario_id
                atencion.remitido_por = remitido
                atencion.atencion_familiar = atencion_fam
                
                for i in range(1, 4):
                    f_val = request.form.get(f'fecha_consulta_{i}')
                    obs_val = request.form.get(f'observaciones_{i}')
                    setattr(atencion, f'fecha_consulta_{i}', datetime.strptime(f_val, '%Y-%m-%d').date() if f_val else None)
                    setattr(atencion, f'observaciones_{i}', obs_val if obs_val else None)
                
                db.session.commit()
                flash('Seguimiento actualizado correctamente.', 'success')
                return redirect(url_for('atencion.listar'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar: {str(e)}', 'danger')
        
    return render_template(
        'atencion/editar.html',
        atencion=atencion,
        profesionales=profesionales,
        aprendiz=aprendiz,
        errors=errors
    )


@atencion_bp.route('/cambiar_estado/<int:id>', methods=['POST'])
@login_required
def cambiar_estado(id):
    atencion = Atencion.query.get_or_404(id)
    atencion.activo = not atencion.activo
    try:
        db.session.commit()
        mensaje = "Atención inactivada correctamente." if not atencion.activo else "Atención activada correctamente."
        flash(mensaje, 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')
        
    return redirect(url_for('atencion.listar'))