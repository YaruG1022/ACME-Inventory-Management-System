from flask import Blueprint, current_app, send_from_directory
from flask_login import login_required

bp = Blueprint("media", __name__)


@bp.get("/uploads/<path:filename>")
@login_required
def upload(filename):
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename)
