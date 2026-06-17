from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.database import db
from app.modules.auth.models import Usuario
# Importa tus otros modelos aquí, ej:
# from app.modules.aprendiz.models import Aprendiz, Ficha, etc.

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Aquí haces las consultas equivalentes a tus servicios de Java
    stats = {
        'totalUsuarios': Usuario.query.count(),
        'totalFichas': 0, # Reemplaza con Ficha.query.count() cuando tengas el modelo
        'totalAprendices': 0,
        'totalCoordinaciones': 0,
        'totalInstructores': 0
    }
    return render_template('dashboard.html', **stats)