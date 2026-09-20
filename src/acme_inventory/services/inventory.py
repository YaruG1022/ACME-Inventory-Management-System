from sqlalchemy import update

from ..extensions import db
from ..models import Item, Order
from .validation import integer, parse_date, required_text


def list_items(search=""):
    query = db.select(Item).order_by(Item.id)
    if search:
        query = (
            query.where(Item.id == int(search))
            if search.isdigit()
            else query.where(Item.name.ilike(f"%{search}%"))
        )
    return db.session.scalars(query).all()


def item_values(data):
    category = required_text(data.get("category"), "Category")
    if category not in {"Food", "Hygiene"}:
        raise ValueError("Choose Food or Hygiene.")
    received_on = parse_date(data.get("received_on"), "Received date")
    expires_on = parse_date(data.get("expires_on"), "Expiration date")
    if expires_on < received_on:
        raise ValueError("Expiration date cannot precede the received date.")
    return dict(
        name=required_text(data.get("name"), "Name"),
        category=category,
        quantity=integer(data.get("quantity"), "Quantity", minimum=0),
        received_on=received_on,
        expires_on=expires_on,
    )


def save_item(data, item_id=None):
    values = item_values(data)
    try:
        item = db.session.get(Item, item_id) if item_id is not None else Item()
        if item is None:
            raise ValueError("Item not found.")
        for key, value in values.items():
            setattr(item, key, value)
        db.session.add(item)
        db.session.commit()
        return item
    except Exception:
        db.session.rollback()
        raise


def receive_donation(data, image_url=None):
    quantity = integer(data.get("quantity"), "Quantity")
    try:
        if data.get("item_id"):
            item = db.session.get(Item, integer(data["item_id"], "Item ID"))
            if item is None:
                raise ValueError("Item not found.")
            values = item_values({**data, "name": item.name, "category": item.category})
            db.session.execute(
                update(Item)
                .where(Item.id == item.id)
                .values(
                    quantity=Item.quantity + quantity,
                    received_on=values["received_on"],
                    expires_on=values["expires_on"],
                )
            )
        else:
            item = Item(**item_values(data))
            db.session.add(item)
        if image_url:
            item.image_url = image_url
        db.session.commit()
        return item
    except Exception:
        db.session.rollback()
        raise


def delete_items(ids):
    ids = {integer(value, "Item ID") for value in ids}
    if not ids:
        raise ValueError("Select at least one item.")
    try:
        # Legacy orders have no foreign key; explicitly protect historical references.
        for order in db.session.scalars(db.select(Order)):
            referenced = {int(entry.split("x")[0]) for entry in order.items.split(",")}
            if ids & referenced:
                raise ValueError("An item is referenced by an order and cannot be deleted.")
        items = db.session.scalars(db.select(Item).where(Item.id.in_(ids))).all()
        if len(items) != len(ids):
            raise ValueError("An item no longer exists. Reload the list.")
        for item in items:
            db.session.delete(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
