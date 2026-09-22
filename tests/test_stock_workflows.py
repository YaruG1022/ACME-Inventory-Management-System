from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from test_orders import order_data

from acme_inventory.extensions import db
from acme_inventory.models import StockBatch
from acme_inventory.services.orders import transition_order


def receive(api, item, quantity=5, days=30, **extra):
    return api(
        "POST",
        "/api/receipts",
        {
            "item_id": item["id"],
            "quantity": quantity,
            "received_on": date.today().isoformat(),
            "expires_on": (date.today() + timedelta(days=days)).isoformat(),
            **extra,
        },
    )


def test_products_sku_alias_units_and_filters(api, item_data):
    item = api(
        "POST",
        "/api/items",
        {
            **item_data,
            "sku": "rice-01",
            "unit": "bag",
            "aliases": "wholegrain, brown rice",
            "minimum_stock": 12,
        },
    ).json
    assert item["sku"] == "RICE-01"
    for query in ("rice-01", "wholegrain", str(item["id"])):
        assert api("GET", f"/api/items?search={query}").json[0]["id"] == item["id"]
    assert len(api("GET", "/api/items?status=low").json) == 1
    assert api("GET", "/api/items?category=Hygiene").json == []
    assert api("POST", "/api/items", {**item_data, "sku": "rice-01"}).status_code == 400
    assert api("PUT", f"/api/items/{item['id']}", {**item_data, "unit": "box"}).status_code == 400


def test_receipt_separates_batches_and_deduplicates(api, item_data):
    item = api("POST", "/api/items", item_data).json
    receipt = receive(
        api, item, request_key="receipt-one", batch_code="DONATION-2", source="Local market"
    )
    assert receipt.status_code == 201
    assert (
        receive(
            api, item, request_key="receipt-one", batch_code="DONATION-2", source="Local market"
        ).status_code
        == 201
    )
    batches = api("GET", "/api/batches").json
    assert len(batches) == 2
    assert sum(b["quantity"] for b in batches) == 15
    assert {b["expires_on"] for b in batches} == {
        item_data["expires_on"],
        (date.today() + timedelta(days=30)).isoformat(),
    }
    assert receive(api, item, quantity=2, request_key="receipt-one").status_code == 400
    assert receive(api, item, batch_code="DONATION-2").status_code == 400
    assert api("GET", "/api/items").json[0]["on_hand"] == 15


def test_preview_fefo_reserve_cancel_and_fulfill(api, item_data):
    item = api("POST", "/api/items", item_data).json
    receive(api, item, quantity=3, days=2, batch_code="EARLY")
    data = order_data([{"item_id": item["id"], "quantity": 5}])
    preview = api("POST", "/api/orders/preview", data).json
    assert preview["can_fulfill"]
    assert preview["lines"][0]["allocations"][0]["code"] == "EARLY"
    assert preview["lines"][0]["allocations"][0]["quantity"] == 3
    assert api("GET", "/api/items").json[0]["reserved"] == 0
    data["request_key"] = "order-one"
    order = api("POST", "/api/orders", data).json
    assert api("POST", "/api/orders", data).json["id"] == order["id"]
    stock = api("GET", "/api/items").json[0]
    assert (stock["on_hand"], stock["reserved"], stock["available"]) == (13, 5, 8)
    assert api("GET", f"/api/orders/{order['id']}").json["lines"][0]["quantity"] == 5
    cancel = {"action": "cancel", "reason": "Recipient changed plans", "request_key": "cancel-one"}
    path = f"/api/orders/{order['id']}/transition"
    assert api("POST", path, cancel).json["status"] == "Cancelled"
    assert api("POST", path, cancel).status_code == 200
    assert api("POST", path, {**cancel, "request_key": "cancel-twice"}).status_code == 400
    assert api("GET", "/api/items").json[0]["available"] == 13
    data["request_key"] = "order-two"
    order = api("POST", "/api/orders", data).json
    response = api(
        "POST",
        f"/api/orders/{order['id']}/transition",
        {"action": "fulfill", "reason": "Collected"},
    )
    assert response.json["status"] == "Fulfilled"
    stock = api("GET", "/api/items").json[0]
    assert (stock["on_hand"], stock["reserved"], stock["available"]) == (8, 0, 8)
    movements = api("GET", "/api/movements").json
    assert sum(m["delta"] for m in movements) == 8
    assert sum(m["reserved_delta"] for m in movements) == 0
    assert all("Operator" in m["actor"] for m in movements)


def test_expiry_quarantine_future_distribution_and_shortage(api, item_data):
    item = api("POST", "/api/items", {**item_data, "quantity": 2}).json
    receive(api, item, quantity=5, days=2)
    batch = api("GET", "/api/batches").json[-1]
    assert (
        api(
            "POST",
            f"/api/batches/{batch['id']}/adjust",
            {"action": "quarantine", "reason": "Check packaging"},
        ).status_code
        == 200
    )
    data = order_data([{"item_id": item["id"], "quantity": 6}])
    preview = api("POST", "/api/orders/preview", data).json
    assert preview["lines"][0]["shortage"] == 1
    assert api("POST", "/api/orders", data).status_code == 400
    data["scheduled_on"] = (date.today() + timedelta(days=3)).isoformat()
    assert api("POST", "/api/orders/preview", data).json["lines"][0]["available"] == 0
    assert api("GET", f"/api/items?status=available&on_date={data['scheduled_on']}").json == []
    assert api("GET", "/api/batches?days=2").json[0]["quantity"] == 5
    expired_data = {
        **item_data,
        "name": "Expired",
        "received_on": (date.today() - timedelta(days=5)).isoformat(),
        "expires_on": (date.today() - timedelta(days=1)).isoformat(),
    }
    expired = api("POST", "/api/items", expired_data).json
    assert expired["available"] == 0
    assert len(api("GET", "/api/batches?expired=1").json) == 1
    assert api("GET", "/api/batches?days=-1").status_code == 400


def test_counts_disposal_reserved_protection_and_stale_count(api, item_data):
    item = api("POST", "/api/items", item_data).json
    batch = api("GET", "/api/batches").json[0]
    path = f"/api/batches/{batch['id']}/adjust"
    order = api("POST", "/api/orders", order_data([{"item_id": item["id"], "quantity": 7}])).json
    for data in (
        {"action": "count", "counted_quantity": 6, "expected_quantity": 10},
        {"action": "dispose", "quantity": 4},
        {"action": "quarantine"},
    ):
        assert api("POST", path, {**data, "reason": "Test"}).status_code == 400
    assert api("POST", path, {"action": "dispose", "quantity": 1}).status_code == 400
    assert (
        api("POST", path, {"action": "dispose", "quantity": 1, "reason": "Damaged"}).status_code
        == 200
    )
    assert (
        api(
            "POST",
            path,
            {"action": "count", "counted_quantity": 8, "expected_quantity": 10, "reason": "Count"},
        ).status_code
        == 400
    )
    count = {
        "action": "count",
        "counted_quantity": 8,
        "expected_quantity": 9,
        "reason": "Count",
        "request_key": "count-once",
    }
    assert api("POST", path, count).status_code == 200
    assert api("POST", path, count).status_code == 200
    assert api("GET", "/api/items").json[0]["available"] == 1
    assert (
        api(
            "POST",
            f"/api/orders/{order['id']}/transition",
            {"action": "cancel", "reason": "Cancelled"},
        ).status_code
        == 200
    )
    assert api("POST", path, {"action": "quarantine", "reason": "Inspection"}).status_code == 200
    assert api("GET", "/api/items").json[0]["available"] == 0
    assert (
        api("POST", path, {"action": "release", "reason": "Inspection passed"}).status_code == 200
    )
    assert api("GET", "/api/items").json[0]["available"] == 8
    rows = api("GET", "/api/movements?kind=Count").json
    assert len(rows) == 1 and rows[0]["delta"] == -1 and rows[0]["balance"] == 8


def test_expired_reservation_cannot_be_fulfilled_but_can_be_cancelled(app, api, item_data):
    item = api("POST", "/api/items", item_data).json
    order = api("POST", "/api/orders", order_data([{"item_id": item["id"], "quantity": 3}])).json
    with app.app_context():
        batch = db.session.scalar(db.select(StockBatch))
        batch.expires_on = date.today() - timedelta(days=1)
        db.session.commit()
    path = f"/api/orders/{order['id']}/transition"
    assert api("POST", path, {"action": "fulfill", "reason": "Deliver"}).status_code == 400
    stock = api("GET", "/api/items").json[0]
    assert stock["on_hand"] == 10 and stock["reserved"] == 3
    assert api("POST", path, {"action": "cancel", "reason": "Expired"}).status_code == 200
    assert api("GET", "/api/items").json[0]["reserved"] == 0


def test_concurrent_fulfillment_cannot_deduct_twice(app, api, item_data):
    item = api("POST", "/api/items", item_data).json
    order = api("POST", "/api/orders", order_data([{"item_id": item["id"], "quantity": 3}])).json

    def submit():
        with app.app_context():
            try:
                transition_order(order["id"], {"action": "fulfill", "reason": "Collected"})
                return True
            except ValueError:
                return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))
    assert sorted(results) == [False, True]
    assert api("GET", "/api/items").json[0]["on_hand"] == 7


def test_new_routes_require_login_and_csrf(app, authenticated):
    client = app.test_client()
    for path in ("/stock", "/movements", "/api/batches", "/api/movements", "/api/orders/1"):
        assert client.get(path).status_code == 302
    for path in (
        "/api/receipts",
        "/api/orders/preview",
        "/api/orders/1/transition",
        "/api/batches/1/adjust",
    ):
        assert authenticated.post(path, json={}).status_code == 400
