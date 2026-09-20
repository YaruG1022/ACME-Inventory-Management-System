import re
from pathlib import Path

from acme_inventory import create_app


def test_pages_and_linked_assets(authenticated):
    for page in (
        "/",
        "/home",
        "/inventory",
        "/add_donation",
        "/orders",
        "/add_order",
        "/report",
        "/account",
        "/login_form",
        "/signup_form",
        "/setup_otp",
    ):
        response = authenticated.get(page)
        assert response.status_code == 200, page
        html = response.get_data(as_text=True)
        for path in re.findall(r'(?:src|href)="(/static/[^\"]+)"', html):
            assert authenticated.get(path).status_code == 200, path
        assert "action_page.php" not in html
        assert not re.search(r"<script(?![^>]*src=)[^>]*>\s*\S", html)


def test_factory_does_not_create_tables_and_cli_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("ACME_INSTANCE_PATH", str(tmp_path / "fresh"))
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    database = Path(app.instance_path) / "inventory.db"
    assert not database.exists()
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert database.exists()
    assert runner.invoke(args=["init-db"]).exit_code == 0


def test_routes_have_no_duplicate_method_path(app):
    seen = set()
    for rule in app.url_map.iter_rules():
        for method in rule.methods - {"OPTIONS", "HEAD"}:
            key = (str(rule), method)
            assert key not in seen, key
            seen.add(key)


def test_prototype_routes_removed(client):
    for path in ("/item_form", "/item_list", "/login_test", "/success"):
        assert client.get(path).status_code == 404
