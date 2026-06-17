import threading
import base64
from io import BytesIO
from datetime import date, datetime

from flask import Blueprint, render_template, request, Response, current_app
from flask_login import login_required
from flask_mail import Message

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

# Modelos y extensiones
from app import mail
from app.database import db
from app.modules.comite.models import Comite
from app.modules.auth.models import Usuario
from app.modules.ficha.models import Ficha

reportes_bp = Blueprint('reportes', __name__)

# --- FUNCIONES DE APOYO ---

def enviar_correo_asincrono(app, msg):
    """Función para enviar correos en segundo plano sin bloquear el servidor."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error al enviar correos masivos: {e}")

def obtener_datos_reporte(fecha_inicio, fecha_fin, ficha_id=None, profesional_id=None):
    """Consulta la base de datos y organiza las estadísticas."""
    query = Comite.query.filter(
        Comite.fecha >= fecha_inicio,
        Comite.fecha <= fecha_fin
    )
    
    if ficha_id and ficha_id != 'None':
        query = query.filter(Comite.ficha_id == ficha_id)
    if profesional_id and profesional_id != 'None':
        query = query.filter(Comite.profesional_bienestar == profesional_id)

    comites = query.all()

    por_tipo = {}
    for c in comites:
        tipo = c.tipo_falta or 'Sin clasificar'
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    por_coordinacion = {}
    for c in comites:
        nombre = c.coordinacion.nombre if c.coordinacion else 'Sin coordinación'
        por_coordinacion[nombre] = por_coordinacion.get(nombre, 0) + 1

    profesionales = Usuario.query.filter(Usuario.rol.in_(['PSICOLOGA', 'T_SOCIAL'])).all()
    rendimiento = []
    
    for p in profesionales:
        casos = [c for c in comites if c.profesional_bienestar == p.id]
        rendimiento.append({
            'nombre': p.nombre,
            'total': len(casos),
            'abiertos': len([c for c in casos if c.activo and not c.paz_salvo]),
            'en_seguimiento': len([c for c in casos if c.activo and c.paz_salvo]),
            'cerrados': len([c for c in casos if not c.activo]),
        })

    return {
        'comites': comites,
        'total': len(comites),
        'por_tipo': por_tipo,
        'por_coordinacion': por_coordinacion,
        'rendimiento': rendimiento,
    }

# --- RUTAS ---

@reportes_bp.route('/')
@login_required
def ver_reportes():
    """Vista web con filtros y gráficos."""
    hoy = date.today()
    inicio_anio = date(hoy.year, 1, 1)

    f_inicio = request.args.get('fechaInicio', str(inicio_anio))
    f_fin = request.args.get('fechaFin', str(hoy))
    ficha_id = request.args.get('fichaId')
    profesional_id = request.args.get('profesionalId')

    try:
        fecha_inicio = datetime.strptime(f_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(f_fin, '%Y-%m-%d').date()
    except ValueError:
        fecha_inicio, fecha_fin = inicio_anio, hoy

    datos = obtener_datos_reporte(fecha_inicio, fecha_fin, ficha_id, profesional_id)
    profesionales = Usuario.query.filter(Usuario.rol.in_(['PSICOLOGA', 'T_SOCIAL'])).all()
    fichas = Ficha.query.order_by(Ficha.codigo).all()

    return render_template(
        'reportes/ver_reportes.html',
        datos=datos,
        profesionales=profesionales,
        fichas=fichas,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        ficha_id=ficha_id,
        profesional_id=profesional_id
    )

@reportes_bp.route('/exportar-pdf', methods=['GET', 'POST'])
@login_required
def exportar_pdf():
    """Genera el PDF con gráficas, lo envía por correo y permite la descarga."""
    hoy = date.today()
    inicio_anio = date(hoy.year, 1, 1)

    # Captura de datos dependiendo del método (POST para gráficas, GET para filtros directos)
    if request.method == 'POST':
        f_inicio = request.form.get('fechaInicio', str(inicio_anio))
        f_fin = request.form.get('fechaFin', str(hoy))
        ficha_id = request.form.get('fichaId')
        profesional_id = request.form.get('profesionalId')
        img_tipos_64 = request.form.get('chart_tipos_img')
        img_coord_64 = request.form.get('chart_coord_img')
    else:
        f_inicio = request.args.get('fechaInicio', str(inicio_anio))
        f_fin = request.args.get('fechaFin', str(hoy))
        ficha_id = request.args.get('fichaId')
        profesional_id = request.args.get('profesionalId')
        img_tipos_64 = None
        img_coord_64 = None

    try:
        fecha_inicio = datetime.strptime(f_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(f_fin, '%Y-%m-%d').date()
    except ValueError:
        fecha_inicio, fecha_fin = inicio_anio, hoy

    datos = obtener_datos_reporte(fecha_inicio, fecha_fin, ficha_id, profesional_id)

    # Configuración de ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # Título y Período
    elements.append(Paragraph("Reporte de Gestión - NEXUS SENA", styles['Title']))
    elements.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"Período de análisis: {fecha_inicio} hasta {fecha_fin}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # --- SECCIÓN DE GRÁFICAS (Solo si vienen por POST) ---
    if img_tipos_64 or img_coord_64:
        elements.append(Paragraph("Análisis Estadístico Visual", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        graficas_data = []
        fila_graficas = []

        if img_tipos_64:
            header, encoded = img_tipos_64.split(",", 1)
            decoded = base64.b64decode(encoded)
            img = Image(BytesIO(decoded), width=220, height=180)
            fila_graficas.append(img)
        
        if img_coord_64:
            header, encoded = img_coord_64.split(",", 1)
            decoded = base64.b64decode(encoded)
            img = Image(BytesIO(decoded), width=220, height=180)
            fila_graficas.append(img)

        if fila_graficas:
            t_img = Table([fila_graficas], colWidths=[250, 250])
            elements.append(t_img)
        
        elements.append(Spacer(1, 20))

    # Resumen numérico
    elements.append(Paragraph(f"Total de comités procesados en el período: <b>{datos['total']}</b>", styles['Normal']))
    elements.append(Spacer(1, 15))

    # Tabla 1: Tipo de Falta
    elements.append(Paragraph("Distribución por Tipo de Falta", styles['Heading3']))
    tipo_data = [['Tipo de Falta', 'Cantidad']]
    for tipo, cantidad in datos['por_tipo'].items():
        tipo_data.append([tipo, cantidad])

    tabla_tipo = Table(tipo_data, colWidths=[350, 100])
    tabla_tipo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6A11CB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
    ]))
    elements.append(tabla_tipo)
    elements.append(Spacer(1, 25))

    # Tabla 2: Rendimiento Equipo
    elements.append(Paragraph("Rendimiento Detallado del Equipo de Bienestar", styles['Heading3']))
    table_rend = [['Profesional', 'Total', 'Abiertos', 'Seguimiento', 'Cerrados']]
    for r in datos['rendimiento']:
        table_rend.append([r['nombre'], r['total'], r['abiertos'], r['en_seguimiento'], r['cerrados']])

    tabla_rend = Table(table_rend, colWidths=[160, 60, 70, 90, 70])
    tabla_rend.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2575FC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(tabla_rend)

    # Construir PDF
    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.seek(0)

    # --- ENVÍO DE CORREO ---
    try:
        usuarios = Usuario.query.filter(Usuario.email.isnot(None), Usuario.email != "").all()
        destinatarios = [u.email for u in usuarios]

        if destinatarios:
          cuerpo_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="background-color: #39A900; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">NEXUS - Sistema de Gestión</h1>
                    </div>
                    <div style="padding: 20px; border: 1px solid #eee;">
                        <p>Cordial saludo,</p>
                        <p>Se informa que se ha generado un <strong>Nuevo Reporte de Gestión Consolidado</strong> correspondiente al período:</p>
                        <p style="background: #f9f9f9; padding: 10px; border-left: 5px solid #39A900;">
                            <strong>Desde:</strong> {fecha_inicio}<br>
                            <strong>Hasta:</strong> {fecha_fin}
                        </p>
                        <p>El documento adjunto contiene las estadísticas detalladas por tipo de falta y el rendimiento del equipo de bienestar.</p>
                        <br>
                        <p style="font-size: 12px; color: #777;">Este es un correo automático generado por la plataforma NEXUS SENA. Por favor no responder.</p>
                    </div>
                </body>
            </html>
            """
        msg = Message(
                subject=f"📊 NEXUS: Reporte de Gestión {fecha_fin}",
                recipients=[],
                bcc=destinatarios,
                html=cuerpo_html # Usamos 'html' en vez de 'body'
            )
        msg.attach(f"Reporte_Nexus_{date.today()}.pdf", "application/pdf", pdf_value)

        thread = threading.Thread(
                target=enviar_correo_asincrono, 
                args=(current_app._get_current_object(), msg)
            )
        thread.start()
    except Exception as e:
        print(f"Error al preparar correo: {e}")

    nombre_archivo = f"Reporte_NEXUS_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        buffer, 
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={nombre_archivo}'}
    )