from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User
from ..services import totp
from ..services.validation import required_text

bp = Blueprint("auth", __name__)


def safe_destination(value):
    if not value or "\\" in value or any(ord(char) < 32 for char in value):
        return url_for("home.index")
    parts = urlsplit(value)
    return (
        value
        if value.startswith("/") and not parts.netloc and not parts.scheme
        else url_for("home.index")
    )


@bp.get("/login_form")
def login_page():
    return render_template(
        "auth/login.html", title="Login", destination=safe_destination(request.args.get("next"))
    )


@bp.get("/signup_form")
def register_page():
    return render_template("auth/register.html", title="Register")


@bp.post("/signup")
def register():
    try:
        email = required_text(request.form.get("email"), "Email").lower()
        name = required_text(request.form.get("username"), "Name", 48)
        password = required_text(request.form.get("password"), "Password", 72)
        if "@" not in email:
            raise ValueError("Enter a valid email address.")
        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    except (ValueError, IntegrityError) as error:
        db.session.rollback()
        flash(str(error) if isinstance(error, ValueError) else "Email address already in use.")
        return redirect(url_for("auth.register_page"))
    session.clear()
    login_user(user)
    return redirect(url_for("home.index"))


@bp.post("/login")
def login():
    email = request.form.get("email", "").strip().lower()
    user = db.session.scalar(db.select(User).where(User.email == email))
    if not user or not user.check_password(request.form.get("password", "")):
        flash("Incorrect email or password.")
        return redirect(url_for("auth.login_page"))
    destination = safe_destination(request.form.get("next"))
    remember = request.form.get("remember") == "on"
    session.clear()
    if user.is_2fa_enabled:
        session.update(pending_user_id=user.id, destination=destination, remember=remember)
        return redirect(url_for("auth.verify_page"))
    login_user(user, remember=remember)
    return redirect(destination)


@bp.get("/otp_check")
def verify_page():
    if not session.get("pending_user_id"):
        return redirect(url_for("auth.login_page"))
    return render_template("auth/two_factor_verify.html", title="Verify login")


@bp.post("/verify_otp")
def verify_otp():
    if current_user.is_authenticated:
        if not totp.verify_code(current_user, request.form.get("code")):
            flash("Incorrect authentication code.")
            return redirect(url_for("auth.setup_otp"))
        current_user.is_2fa_enabled = True
        db.session.commit()
        flash("Two-factor authentication enabled.")
        return redirect(url_for("account.profile"))
    user = (
        db.session.get(User, session["pending_user_id"]) if session.get("pending_user_id") else None
    )
    if not user:
        return redirect(url_for("auth.login_page"))
    if not totp.verify_code(user, request.form.get("code")):
        flash("Incorrect authentication code.")
        return redirect(url_for("auth.verify_page"))
    destination = safe_destination(session.get("destination"))
    remember = session.get("remember", False)
    session.clear()
    login_user(user, remember=remember)
    return redirect(destination)


@bp.get("/setup_otp")
@login_required
def setup_otp():
    return render_template(
        "auth/two_factor_setup.html",
        title="Set up two-factor authentication",
        qr_image=totp.qr_base64(current_user),
    )


@bp.post("/log_out")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("home.index"))
