from io import BytesIO

from conftest import csrf
from PIL import Image


def test_create_search_edit_zero_and_delete(api, item_data):
    assert api("GET", "/api/items").json == []
    created = api("POST", "/api/items", item_data)
    assert created.status_code == 201
    item_id = created.json["id"]
    assert api("GET", "/api/items?search=Rice").json[0]["category"] == "Food"
    assert api("GET", "/api/items?search=missing").json == []
    updated = api("PUT", f"/api/items/{item_id}", {**item_data, "quantity": 0})
    assert updated.status_code == 200
    assert updated.json["quantity"] == 0
    assert api("POST", "/api/items/delete", {"ids": [item_id]}).status_code == 200
    assert api("GET", "/api/items").json == []


def test_invalid_mutations_leave_stock_unchanged(api, item_data):
    created = api("POST", "/api/items", item_data).json
    for changes in (
        {"quantity": -1},
        {"quantity": 1.5},
        {"category": "Other"},
        {"expires_on": "2020-01-01"},
        {"received_on": "bad"},
    ):
        assert (
            api("PUT", f"/api/items/{created['id']}", {**item_data, **changes}).status_code == 400
        )
    assert api("POST", "/api/items", []).status_code == 400
    assert api("GET", "/api/items").json[0]["quantity"] == 10


def test_receive_existing_preserves_image(authenticated, api, item_data):
    item = api("POST", "/api/items", item_data).json
    response = authenticated.post(
        "/additem",
        data={
            **item_data,
            "item_id": str(item["id"]),
            "quantity": 3,
            "csrf_token": csrf(authenticated),
        },
    )
    assert response.location.endswith("/inventory")
    updated = api("GET", "/api/items").json[0]
    assert updated["quantity"] == 13
    assert updated["image_url"] == item["image_url"]


def test_upload_is_private_and_rejects_fake_images(authenticated, app):
    image = BytesIO()
    Image.new("RGB", (2, 2), "white").save(image, format="PNG")
    image.seek(0)
    response = authenticated.post(
        "/upload_profile_image",
        data={
            "file": (image, "avatar.png"),
            "csrf_token": csrf(authenticated),
        },
    )
    assert response.status_code == 302
    from acme_inventory.extensions import db
    from acme_inventory.models import User

    with app.app_context():
        url = db.session.scalar(db.select(User)).avatar_url
    assert url.startswith("/uploads/profiles/")
    assert authenticated.get(url).status_code == 200
    assert app.test_client().get(url).status_code == 302
    response = authenticated.post(
        "/upload_profile_image",
        data={
            "file": (BytesIO(b"not an image"), "fake.png"),
            "csrf_token": csrf(authenticated),
        },
        follow_redirects=True,
    )
    assert b"Upload a valid image" in response.data
