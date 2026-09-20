"""Configuration evaluated when each application is created."""

import os
from pathlib import Path


def default_config(instance_path):
    instance = Path(instance_path)
    return {
        "SECRET_KEY": os.environ.get("ACME_SECRET_KEY"),
        "SQLALCHEMY_DATABASE_URI": os.environ.get(
            "ACME_DATABASE_URL", f"sqlite:///{(instance / 'inventory.db').as_posix()}"
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "UPLOAD_DIR": os.environ.get("ACME_UPLOAD_DIR", str(instance / "uploads")),
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
    }
