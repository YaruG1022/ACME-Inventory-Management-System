from flask import Blueprint, render_template
from flask_login import current_user

from ..services.overview import inventory_overview

bp = Blueprint("home", __name__)


@bp.get("/")
@bp.get("/home")
def index():
    return render_template(
        "home/index.html",
        title="Overview",
        overview=inventory_overview() if current_user.is_authenticated else None,
    )
