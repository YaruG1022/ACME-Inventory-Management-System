"""Application factory for the ACME Food Bank inventory system."""

import os
import secrets
from pathlib import Path

from flask import Flask, abort, request, session

from .config import default_config
from .extensions import bcrypt, db, login_manager


def create_app(test_config=None):
    instance_path = os.environ.get("ACME_INSTANCE_PATH")
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)
    app.config.from_mapping(default_config(app.instance_path))
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config["SECRET_KEY"]:
        secret_path = Path(app.instance_path) / "secret.txt"
        try:
            with secret_path.open("x", encoding="utf-8") as secret_file:
                secret_file.write(secrets.token_urlsafe(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = secret_path.read_text(encoding="utf-8").strip()

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"

    from .cli import register_commands
    from .models import User
    from .routes import register_routes

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_mutations():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = session.get("csrf_token", "")
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected.encode(), supplied.encode()):
                abort(400, description="The form expired. Reload the page and try again.")

    register_routes(app)
    register_commands(app)
    return app
