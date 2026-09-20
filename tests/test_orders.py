from concurrent.futures import ThreadPoolExecutor

from acme_inventory.extensions import db
from acme_inventory.models import Item, Order
from acme_inventory.services.orders import create_order


def order_data(lines):
    return {
        "items": lines,
        "ordered_on": "2026-09-20",
        "recipient_name": "Recipient",
        "recipient_address": "123 Main Street",
    }


def test_order_aggregates_lines_and_protects_history(api, item_data):
    item = api("POST", "/api/items", item_data).json
    response = api(
        "POST",
        "/api/orders",
        order_data(
            [
                {"item_id": item["id"], "quantity": 2},
                {"item_id": item["id"], "quantity": 3},
            ]
        ),
    )
    assert response.status_code == 201
    assert response.json["items"] == f"{item['id']}x5"
    assert api("GET", "/api/items").json[0]["quantity"] == 5
    assert api("POST", "/api/items/delete", {"ids": [item["id"]]}).status_code == 400


def test_failed_later_line_rolls_back_earlier_deduction(api, item_data, app):
    item = api("POST", "/api/items", item_data).json
    response = api(
        "POST",
        "/api/orders",
        order_data(
            [
                {"item_id": item["id"], "quantity": 2},
                {"item_id": 99999, "quantity": 1},
            ]
        ),
    )
    assert response.status_code == 400
    assert api("GET", "/api/items").json[0]["quantity"] == 10
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Order)) == 0


def test_negative_and_empty_order_rejected(api, item_data):
    item = api("POST", "/api/items", item_data).json
    for lines in (
        [],
        [{"item_id": item["id"], "quantity": -3}],
        [{"item_id": item["id"], "quantity": 11}],
    ):
        assert api("POST", "/api/orders", order_data(lines)).status_code == 400
    assert api("GET", "/api/items").json[0]["quantity"] == 10


def test_concurrent_orders_cannot_both_spend_same_stock(app, api, item_data):
    item = api("POST", "/api/items", item_data).json

    def submit():
        with app.app_context():
            try:
                create_order(order_data([{"item_id": item["id"], "quantity": 7}]))
                return True
            except ValueError:
                return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))
    assert sorted(results) == [False, True]
    with app.app_context():
        assert db.session.get(Item, item["id"]).quantity == 3
        assert db.session.scalar(db.select(db.func.count()).select_from(Order)) == 1
