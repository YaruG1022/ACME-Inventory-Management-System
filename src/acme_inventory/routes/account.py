from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..services.image_storage import store_image
from ..services.validation import required_text

bp = Blueprint("account", __name__)


@bp.get("/account")
@login_required
def profile():
    return render_template("account/profile.html", title="Account")


@bp.post("/upload_profile_image")
@login_required
def upload_avatar():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            raise ValueError("Choose an image.")
        current_user.avatar_url = store_image(file, "profiles")
        db.session.commit()
        flash("Avatar updated.")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("account.profile"))


@bp.post("/update_user_data")
@login_required
def update_profile():
    try:
        name = required_text(request.form.get("username"), "Name", 48)
        email = required_text(request.form.get("email"), "Email").lower()
        if "@" not in email:
            raise ValueError("Enter a valid email address.")
        current_user.name, current_user.email = name, email
        db.session.commit()
        flash("Account updated.")
    except (ValueError, IntegrityError) as error:
        db.session.rollback()
        flash(str(error) if isinstance(error, ValueError) else "Email address already in use.")
    return redirect(url_for("account.profile"))


@bp.post("/update_user_password")
@login_required
def update_password():
    try:
        if not current_user.check_password(request.form.get("current_password", "")):
            raise ValueError("Current password is incorrect.")
        current_user.set_password(required_text(request.form.get("password"), "Password", 72))
        db.session.commit()
        flash("Password updated.")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("account.profile"))
