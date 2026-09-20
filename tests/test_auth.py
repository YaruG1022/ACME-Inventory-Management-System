import pyotp
from conftest import csrf

from acme_inventory.extensions import db
from acme_inventory.models import User


def test_login_required_and_csrf(client):
    for url in ("/inventory", "/api/items", "/api/reports", "/orders", "/account"):
        assert client.get(url).status_code == 302
    assert client.post("/signup", data={"email": "user@example.com"}).status_code == 400
    assert client.get("/otp_check").status_code == 302


def test_password_update_persists_and_redirect_is_local(authenticated):
    client = authenticated
    response = client.post(
        "/update_user_password",
        data={
            "current_password": "password123",
            "password": "new-password",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 302
    client.post("/log_out", data={"csrf_token": csrf(client)})
    response = client.post(
        "/login",
        data={
            "email": "operator@example.com",
            "password": "new-password",
            "next": "//outside.example",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 302
    assert response.location in {"/", "/home"}
    assert client.get("/account").status_code == 200


def test_two_factor_requires_code(app, authenticated):
    client = authenticated
    assert client.get("/setup_otp").status_code == 200
    with app.app_context():
        user = db.session.scalar(db.select(User))
        token = user.token_2fa
    client.post("/verify_otp", data={"code": pyotp.TOTP(token).now(), "csrf_token": csrf(client)})
    client.post("/log_out", data={"csrf_token": csrf(client)})
    response = client.post(
        "/login",
        data={
            "email": "operator@example.com",
            "password": "password123",
            "csrf_token": csrf(client),
        },
    )
    assert response.location.endswith("/otp_check")
    assert client.get("/account").status_code == 302
    assert client.get("/otp_check").status_code == 200
    client.post("/verify_otp", data={"code": "invalid", "csrf_token": csrf(client)})
    assert client.get("/account").status_code == 302
    client.post("/verify_otp", data={"code": pyotp.TOTP(token).now(), "csrf_token": csrf(client)})
    assert client.get("/account").status_code == 200
    with client.session_transaction() as session:
        assert "pending_user_id" not in session
