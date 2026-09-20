from flask import Blueprint, render_template

bp = Blueprint("home", __name__)


@bp.get("/")
@bp.get("/home")
def index():
    return render_template("home/index.html", title="Home")
