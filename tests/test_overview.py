from datetime import date, timedelta

from acme_inventory.extensions import db
from acme_inventory.models import Item
from acme_inventory.services.overview import inventory_overview


def test_overview_counts_products_and_only_flags_stock_on_hand(app, authenticated):
    today = date.today()
    with app.app_context():
        for name, quantity, days in [
            ("Expires today", 5, 0),
            ("Expires in seven days", 4, 7),
            ("Expires later", 3, 8),
            ("Already expired", 2, -1),
            ("Empty expired product", 0, -2),
        ]:
            db.session.add(
                Item(
                    name=name,
                    category="Food",
                    quantity=quantity,
                    received_on=today - timedelta(days=10),
                    expires_on=today + timedelta(days=days),
                )
            )
        db.session.commit()
        summary = inventory_overview()
        assert summary["total"] == 5
        assert summary["in_stock"] == 4
        assert summary["out_of_stock"] == 1
        assert len(summary["expiring"]) == 2
        assert len(summary["expired"]) == 1
        assert summary["attention"][0].name == "Already expired"
        assert summary["food"] == 5
        assert summary["hygiene"] == 0
    response = authenticated.get("/home")
    assert response.status_code == 200
    assert b"Already expired" in response.data
    assert b"Empty expired product" not in response.data


def test_public_home_does_not_show_inventory_details(api, client, app, item_data):
    api("POST", "/api/items", {**item_data, "name": "Private stock name"})
    response = app.test_client().get("/home")
    assert response.status_code == 200
    assert b"Private stock name" not in response.data
    assert b"Organized supplies" in response.data
