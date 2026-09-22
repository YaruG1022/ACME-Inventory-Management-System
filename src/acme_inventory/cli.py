"""Explicit database initialization and non-destructive legacy import."""

import shutil
import sqlite3
from pathlib import Path

import click
from flask import current_app
from sqlalchemy.engine import make_url

from .extensions import db
from .migrations import upgrade_database
from .models import Item, User


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        """Create missing tables without deleting existing data."""
        upgrade_database()
        click.echo("Database tables are ready.")

    @app.cli.command("upgrade-db")
    def upgrade_db():
        """Back up and migrate inventory, batches, and historical orders."""
        backup = upgrade_database()
        click.echo(f"Database upgraded. Backup: {backup}" if backup else "Database is up to date.")

    @app.cli.command("import-legacy")
    @click.option(
        "--database", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path)
    )
    @click.option("--images", type=click.Path(exists=True, file_okay=False, path_type=Path))
    def import_legacy(database, images):
        """Copy a legacy SQLite database and optional images into this instance."""
        url = make_url(current_app.config["SQLALCHEMY_DATABASE_URI"])
        if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
            raise click.ClickException("Legacy import requires a file-backed SQLite destination.")
        target = Path(db.engine.url.database).resolve()
        if target.exists():
            raise click.ClickException(
                "Destination already exists; choose a fresh instance directory."
            )
        destination = Path(current_app.config["UPLOAD_DIR"]) / "legacy"
        if images and destination.exists():
            raise click.ClickException("Legacy image destination already exists.")
        target.parent.mkdir(parents=True, exist_ok=True)
        # SQLite's backup API also includes committed WAL contents.
        with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as source:
            tables = {
                row[0]
                for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if not {"item", "order", "user"}.issubset(tables):
                raise click.ClickException("The source is not an ACME inventory database.")
            with sqlite3.connect(target) as destination_connection:
                source.backup(destination_connection)
        if images:
            shutil.copytree(images, destination)
        upgrade_database()

        def image_url(value, fallback):
            normalized = (value or "").replace("\\", "/").lstrip("/")
            prefix = "static/img/"
            if images and normalized.startswith(prefix):
                relative = normalized[len(prefix) :]
                resolved = (images / relative).resolve()
                if resolved.is_relative_to(images.resolve()) and resolved.is_file():
                    return "/uploads/legacy/" + relative
            return fallback

        for item in db.session.scalars(db.select(Item)):
            item.image_url = image_url(item.image_url, "/static/images/placeholder.svg")
        for user in db.session.scalars(db.select(User)):
            user.avatar_url = image_url(user.avatar_url, "/static/images/default-profile.svg")
        db.session.commit()
        click.echo("Legacy data copied. The source database and images were not changed.")
