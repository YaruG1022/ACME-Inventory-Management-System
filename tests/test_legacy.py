import sqlite3
from pathlib import Path

import pyotp

from acme_inventory import create_app
from acme_inventory.extensions import bcrypt, db
from acme_inventory.models import Item, Order, StockBatch, StockMovement, User


def test_import_preserves_old_schema_and_source(tmp_path, monkeypatch):
    source = tmp_path / "legacy.db"
    images = tmp_path / "old-images"
    (images / "profiles").mkdir(parents=True)
    (images / "profiles" / "avatar.png").write_bytes(b"old-image")
    token = pyotp.random_base32()
    password = bcrypt.generate_password_hash("old-password", rounds=4)
    with sqlite3.connect(source) as connection:
        connection.executescript("""
            CREATE TABLE user (id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL UNIQUE,
              password VARCHAR(255) NOT NULL, name VARCHAR(255) NOT NULL, pfp_url VARCHAR(255),
              joindate DATETIME NOT NULL, is_2fa_enabled BOOLEAN NOT NULL, token_2fa VARCHAR UNIQUE);
            CREATE TABLE item (id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL,
              type VARCHAR(255) NOT NULL, quantity INTEGER NOT NULL, stockdate DATE NOT NULL,
              expdate DATE NOT NULL, image VARCHAR(255));
            CREATE TABLE "order" (id INTEGER PRIMARY KEY, orderdate DATE NOT NULL,
              deliverydate DATE, status VARCHAR(255) NOT NULL, items VARCHAR(255) NOT NULL,
              recipient_name VARCHAR(255) NOT NULL, recipient_address VARCHAR(255) NOT NULL);
        """)
        connection.execute(
            "INSERT INTO user VALUES (1, ?, ?, ?, ?, ?, 1, ?)",
            (
                "old@example.com",
                password,
                "Old User",
                "static\\img\\profiles\\avatar.png",
                "2021-06-01 00:00:00",
                token,
            ),
        )
        connection.execute(
            "INSERT INTO item VALUES (1, 'Rice', 'Food', 7, '2026-01-01', '2027-01-01', 'static/img/missing.png')"
        )
        connection.execute(
            "INSERT INTO \"order\" VALUES (1, '2026-01-02', NULL, 'Confirmed', '1x3', 'Recipient', 'Address')"
        )
    original = source.read_bytes()
    monkeypatch.setenv("ACME_INSTANCE_PATH", str(tmp_path / "new-instance"))
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    runner = app.test_cli_runner()
    args = ["import-legacy", "--database", str(source), "--images", str(images)]
    result = runner.invoke(args=args)
    assert result.exit_code == 0, result.output
    assert source.read_bytes() == original
    with app.app_context():
        user = db.session.get(User, 1)
        assert user.check_password("old-password")
        assert user.token_2fa == token
        assert user.is_2fa_enabled
        assert user.avatar_url == "/uploads/legacy/profiles/avatar.png"
        assert db.session.get(Item, 1).quantity == 7
        assert db.session.get(Item, 1).image_url == "/static/images/placeholder.svg"
        assert db.session.get(Order, 1).items == "1x3"
        assert db.session.get(Order, 1).status == "Legacy recorded"
        assert db.session.get(Order, 1).legacy_status == "Confirmed"
        assert db.session.get(Order, 1).lines[0].quantity == 3
        assert db.session.scalar(db.select(StockBatch)).quantity == 7
        assert db.session.scalar(db.select(StockMovement)).delta == 7
        db.session.remove()
        db.engine.dispose()
    assert (
        Path(app.config["UPLOAD_DIR"]) / "legacy/profiles/avatar.png"
    ).read_bytes() == b"old-image"
    assert runner.invoke(args=["upgrade-db"]).exit_code == 0
    assert runner.invoke(args=["upgrade-db"]).exit_code == 0
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(StockBatch)) == 1
        assert db.session.scalar(db.select(db.func.count()).select_from(StockMovement)) == 1
        assert db.session.get(Item, 1).quantity == 7
        db.session.remove()
        db.engine.dispose()
    assert runner.invoke(args=args).exit_code != 0
    assert source.read_bytes() == original
