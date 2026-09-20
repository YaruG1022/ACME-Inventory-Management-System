import pytest

from acme_inventory import create_app
from acme_inventory.extensions import db


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("ACME_INSTANCE_PATH", str(tmp_path / "instance"))
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
            "UPLOAD_DIR": str(tmp_path / "uploads"),
            "BCRYPT_LOG_ROUNDS": 4,
        }
    )
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client):
    client.get("/")
    with client.session_transaction() as session:
        return session["csrf_token"]


@pytest.fixture
def authenticated(client):
    response = client.post(
        "/signup",
        data={
            "email": "operator@example.com",
            "username": "Operator",
            "password": "password123",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 302
    return client


@pytest.fixture
def api(authenticated):
    def send(method, path, data=None):
        return authenticated.open(
            path, method=method, json=data, headers={"X-CSRF-Token": csrf(authenticated)}
        )

    return send


@pytest.fixture
def item_data():
    return {
        "name": "Rice",
        "category": "Food",
        "quantity": 10,
        "received_on": "2026-09-20",
        "expires_on": "2027-09-20",
    }
