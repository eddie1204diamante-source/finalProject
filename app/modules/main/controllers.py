from flask import Blueprint, render_template
from flask_login import login_required

from app.modules.aprendiz.models import Aprendiz
from app.modules.ficha.models import Ficha
from app.modules.coordinacion.models import Coordinacion
from app.modules.auth.models import Usuario

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():

    total_usuarios = Usuario.query.count() or 0
    total_fichas = Ficha.query.count() or 0
    total_aprendices = Aprendiz.query.count() or 0
    total_coordinaciones = Coordinacion.query.count() or 0

    return render_template(
        'main/index.html',  # ← lo dejamos como lo tienes
        totalUsuarios=total_usuarios,
        totalFichas=total_fichas,
        totalAprendices=total_aprendices,
        totalCoordinaciones=total_coordinaciones
    )