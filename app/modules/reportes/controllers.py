import os
import json
import threading
import base64
from io import BytesIO
from datetime import date, datetime
from urllib import request as urllib_request
from urllib import error as urllib_error

from flask import Blueprint, render_template, request, send_file
from flask_login import login_required

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

from app import mail
from app.database import db
from app.modules.comite.models import Comite
from app.modules.auth.models import Usuario
from app.modules.ficha.models import Ficha

reportes_bp = Blueprint("reportes", __name__)

RESEND_API_URL = "https://api.resend.com/emails"


def _normalizar_destinatarios(correo_destino=None):
    """
    Si llega un correo específico, lo usa.
    Si no, toma todos los correos válidos de usuarios en la base de datos.
    """
    destinatarios = set()

    if correo_destino:
        correo_destino = correo_destino.strip().lower()
        if "@" in correo_destino and "." in correo_destino:
            destinatarios.add(correo_destino)
            return sorted(destinatarios)

    usuarios = Usuario.query.filter(
        Usuario.email.isnot(None),
        Usuario.email != ""
    ).all()

    for usuario in usuarios:
        email = (usuario.email or "").strip().lower()
        if "@" in email and "." in email:
            destinatarios.add(email)

    return sorted(destinatarios)


def _construir_html_correo(fecha_inicio, fecha_fin):
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="background-color: #39A900; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">NEXUS - Sistema de Gestión</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #eee; border-top: none; border-radius: 0 0 8px 8px;">
                <p>Cordial saludo,</p>
                <p>Se ha generado un <strong>Nuevo Reporte de Gestión Consolidado</strong> en la plataforma <strong>NEXUS SENA</strong>.</p>
                <p style="background: #f9f9f9; padding: 12px; border-left: 5px solid #39A900; margin: 16px 0;">
                    <strong>Período de análisis:</strong><br>
                    Desde: {fecha_inicio}<br>
                    Hasta: {fecha_fin}
                </p>
                <p>El documento adjunto contiene las estadísticas detalladas por tipo de falta y el rendimiento del equipo de bienestar.</p>
                <br>
                <p style="font-size: 12px; color: #777;">Este es un correo automático generado por la plataforma NEXUS SENA. Por favor no responder.</p>
            </div>
        </body>
    </html>
    """


def _enviar_resend_payload(payload):
    """
    Envía el payload a Resend usando solo la librería estándar.
    """
    api_key = getattr(mail, "api_key", None) or os.getenv("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY no está configurada.")

    data = json.dumps(payload).encode("utf-8")

    req = urllib_request.Request(
        RESEND_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib_request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")
        return response.status, body


def enviar_reporte_correo_async(destinatarios, pdf_bytes, filename, fecha_inicio, fecha_fin):
    """
    Envía el reporte por Resend con adjunto PDF.
    """
    try:
        if not destinatarios:
            print("No hay destinatarios válidos para enviar el reporte.")
            return

        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        subject = f"Reporte de Gestión NEXUS ({fecha_inicio} a {fecha_fin})"
        cuerpo_html = _construir_html_correo(fecha_inicio, fecha_fin)

        payload = {
            "from": os.getenv("RESEND_FROM_EMAIL", "NEXUS SENA <onboarding@resend.dev>"),
            "to": [destinatarios[0]],
            "subject": subject,
            "html": cuerpo_html,
            "attachments": [
                {
                    "filename": filename,
                    "content": pdf_base64
                }
            ]
        }

        if len(destinatarios) > 1:
            payload["bcc"] = destinatarios[1:]

        status, body = _enviar_resend_payload(payload)
        print(f"Reporte enviado correctamente. HTTP {status}. Respuesta: {body}")

    except urllib_error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        print(f"Error HTTP al enviar el reporte por Resend: {e.code} - {error_body}")
    except Exception as e:
        print(f"Error crítico al enviar reporte por Resend: {e}")


def obtener_datos_reporte(fecha_inicio, fecha_fin, ficha_id=None, profesional_id=None):
    """Consulta la base de datos y organiza las estadísticas."""
    query = Comite.query.filter(
        Comite.fecha >= fecha_inicio,
        Comite.fecha <= fecha_fin
    )

    if ficha_id and ficha_id != "None":
        query = query.filter(Comite.ficha_id == ficha_id)
    if profesional_id and profesional_id != "None":
        query = query.filter(Comite.profesional_bienestar == profesional_id)

    comites = query.all()

    por_tipo = {}
    for c in comites:
        tipo = c.tipo_falta or "Sin clasificar"
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    por_coordinacion = {}
    for c in comites:
        nombre = c.coordinacion.nombre if c.coordinacion else "Sin coordinación"
        por_coordinacion[nombre] = por_coordinacion.get(nombre, 0) + 1

    profesionales = Usuario.query.filter(Usuario.rol.in_(["PSICOLOGA", "T_SOCIAL"])).all()
    rendimiento = []

    for p in profesionales:
        casos = [c for c in comites if c.profesional_bienestar == p.id]
        rendimiento.append({
            "nombre": p.nombre,
            "total": len(casos),
            "abiertos": len([c for c in casos if c.activo and not c.paz_salvo]),
            "en_seguimiento": len([c for c in casos if c.activo and c.paz_salvo]),
            "cerrados": len([c for c in casos if not c.activo]),
        })

    return {
        "comites": comites,
        "total": len(comites),
        "por_tipo": por_tipo,
        "por_coordinacion": por_coordinacion,
        "rendimiento": rendimiento,
    }


@reportes_bp.route("/")
@login_required
def ver_reportes():
    """Vista web con filtros y gráficos."""
    hoy = date.today()
    inicio_anio = date(hoy.year, 1, 1)

    f_inicio = request.args.get("fechaInicio", str(inicio_anio))
    f_fin = request.args.get("fechaFin", str(hoy))
    ficha_id = request.args.get("fichaId")
    profesional_id = request.args.get("profesionalId")

    try:
        fecha_inicio = datetime.strptime(f_inicio, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(f_fin, "%Y-%m-%d").date()
    except ValueError:
        fecha_inicio, fecha_fin = inicio_anio, hoy

    datos = obtener_datos_reporte(fecha_inicio, fecha_fin, ficha_id, profesional_id)
    profesionales = Usuario.query.filter(Usuario.rol.in_(["PSICOLOGA", "T_SOCIAL"])).all()
    fichas = Ficha.query.order_by(Ficha.codigo).all()

    return render_template(
        "reportes/ver_reportes.html",
        datos=datos,
        profesionales=profesionales,
        fichas=fichas,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        ficha_id=ficha_id,
        profesional_id=profesional_id
    )


@reportes_bp.route("/exportar-pdf", methods=["GET", "POST"])
@login_required
def exportar_pdf():
    """Genera el PDF, lo descarga y además lo envía por correo con Resend."""
    hoy = date.today()
    inicio_anio = date(hoy.year, 1, 1)

    if request.method == "POST":
        f_inicio = request.form.get("fechaInicio", str(inicio_anio))
        f_fin = request.form.get("fechaFin", str(hoy))
        ficha_id = request.form.get("fichaId")
        profesional_id = request.form.get("profesionalId")
        img_tipos_64 = request.form.get("chart_tipos_img")
        img_coord_64 = request.form.get("chart_coord_img")
        correo_destino = request.form.get("correoDestino")
    else:
        f_inicio = request.args.get("fechaInicio", str(inicio_anio))
        f_fin = request.args.get("fechaFin", str(hoy))
        ficha_id = request.args.get("fichaId")
        profesional_id = request.args.get("profesionalId")
        img_tipos_64 = None
        img_coord_64 = None
        correo_destino = request.args.get("correoDestino")

    try:
        fecha_inicio = datetime.strptime(f_inicio, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(f_fin, "%Y-%m-%d").date()
    except ValueError:
        fecha_inicio, fecha_fin = inicio_anio, hoy

    datos = obtener_datos_reporte(fecha_inicio, fecha_fin, ficha_id, profesional_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Reporte de Gestión - NEXUS SENA", styles["Title"]))
    elements.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Paragraph(f"Período de análisis: {fecha_inicio} hasta {fecha_fin}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    if img_tipos_64 or img_coord_64:
        elements.append(Paragraph("Análisis Estadístico Visual", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        fila_graficas = []

        if img_tipos_64:
            _, encoded = img_tipos_64.split(",", 1)
            decoded = base64.b64decode(encoded)
            fila_graficas.append(Image(BytesIO(decoded), width=220, height=180))

        if img_coord_64:
            _, encoded = img_coord_64.split(",", 1)
            decoded = base64.b64decode(encoded)
            fila_graficas.append(Image(BytesIO(decoded), width=220, height=180))

        if fila_graficas:
            t_img = Table([fila_graficas], colWidths=[250, 250])
            elements.append(t_img)

        elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        f"Total de comités procesados en el período: <b>{datos['total']}</b>",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Distribución por Tipo de Falta", styles["Heading3"]))
    tipo_data = [["Tipo de Falta", "Cantidad"]]
    for tipo, cantidad in datos["por_tipo"].items():
        tipo_data.append([tipo, cantidad])

    tabla_tipo = Table(tipo_data, colWidths=[350, 100])
    tabla_tipo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6A11CB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(tabla_tipo)
    elements.append(Spacer(1, 25))

    elements.append(Paragraph("Rendimiento Detallado del Equipo de Bienestar", styles["Heading3"]))
    table_rend = [["Profesional", "Total", "Abiertos", "Seguimiento", "Cerrados"]]
    for r in datos["rendimiento"]:
        table_rend.append([r["nombre"], r["total"], r["abiertos"], r["en_seguimiento"], r["cerrados"]])

    tabla_rend = Table(table_rend, colWidths=[160, 60, 70, 90, 70])
    tabla_rend.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(tabla_rend)

    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.seek(0)

    destinatarios = _normalizar_destinatarios(correo_destino)

    if destinatarios:
        nombre_pdf = f"Reporte_NEXUS_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        thread = threading.Thread(
            target=enviar_reporte_correo_async,
            args=(destinatarios, pdf_value, nombre_pdf, fecha_inicio, fecha_fin),
            daemon=True
        )
        thread.start()
    else:
        print("No se encontró ningún destinatario válido. El PDF se descargará sin envío por correo.")

    nombre_archivo = f"Reporte_NEXUS_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    buffer.seek(0)
    return send_file(
        BytesIO(pdf_value),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre_archivo
    )