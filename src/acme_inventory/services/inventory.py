from datetime import date

from sqlalchemy import or_

from ..extensions import db
from ..models import Item, OrderLine
from .stock import add_batch, atomic, operation, stock_summary
from .validation import integer, parse_date, required_text


def list_items(search="", category=None, status=None, on_date=None):
    query = db.select(Item).order_by(Item.id)
    if search:
        pattern = f"%{search}%"
        conditions = [
            Item.name.ilike(pattern),
            Item.sku.ilike(pattern),
            Item.aliases.ilike(pattern),
        ]
        if search.isdigit():
            conditions.append(Item.id == int(search))
        query = query.where(or_(*conditions))
    if category:
        if category not in {"Food", "Hygiene"}:
            raise ValueError("Choose Food or Hygiene.")
        query = query.where(Item.category == category)
    when = parse_date(on_date, "Availability date") if on_date else None
    items = db.session.scalars(query).all()
    if status:
        if status not in {"available", "out", "low", "expired", "expiring"}:
            raise ValueError("Invalid stock status.")

        def matches(item):
            summary = stock_summary(item, when)
            return {
                "available": summary["available"] > 0,
                "out": summary["available"] == 0,
                "low": summary["low_stock"],
                "expired": summary["expired"] > 0,
                "expiring": summary["expiring"] > 0,
            }[status]

        items = [item for item in items if matches(item)]
    return items


def product_values(data, existing=None):
    category = required_text(data.get("category"), "Category")
    if category not in {"Food", "Hygiene"}:
        raise ValueError("Choose Food or Hygiene.")
    aliases = data.get("aliases", existing.aliases if existing else "")
    if not isinstance(aliases, str) or len(aliases) > 500:
        raise ValueError("Aliases must be text of at most 500 characters.")
    sku = data.get("sku") or (existing.sku if existing else None)
    if sku:
        sku = required_text(sku, "SKU", 64).upper()
    return dict(
        name=required_text(data.get("name"), "Name"),
        category=category,
        sku=sku,
        unit=required_text(
            data.get("unit", existing.unit if existing else "unit"), "Base unit", 32
        ),
        aliases=aliases.strip(),
        minimum_stock=integer(
            data.get("minimum_stock", existing.minimum_stock if existing else 0),
            "Minimum stock",
            minimum=0,
        ),
    )


def new_item(data):
    item = Item(
        **product_values(data), quantity=0, received_on=date.today(), expires_on=date.today()
    )
    db.session.add(item)
    db.session.flush()
    if not item.sku:
        item.sku = f"ACME-{item.id:06d}"
    return item


@atomic
def save_item(data, item_id=None):
    if item_id is None:
        previous = operation(data, "product")
        if previous:
            return db.session.get(Item, previous)
        item = new_item(data)
        if data.get("quantity") not in (None, "", 0, "0"):
            add_batch(item, data, "Opening")
        elif "quantity" in data and data["quantity"] != "":
            integer(data["quantity"], "Quantity", minimum=0)
        operation(data, "product", item.id)
        return item
    item = db.session.get(Item, item_id)
    if item is None:
        raise ValueError("Item not found.")
    # Stock quantities and lot dates must be changed through audited batch operations.
    if "quantity" in data and integer(data["quantity"], "Quantity", minimum=0) != item.quantity:
        raise ValueError("Use the batch physical-count form to adjust stock, with a reason.")
    for key in ("received_on", "expires_on"):
        if key in data and parse_date(data[key], key) != getattr(item, key):
            raise ValueError("Dates belong to batches. Receive a new batch instead.")
    values = product_values(data, item)
    if values["unit"] != item.unit and item.batches:
        raise ValueError(
            "Base unit cannot change after stock history exists. Create a new product."
        )
    for key, value in values.items():
        setattr(item, key, value)
    return item


@atomic
def receive_donation(data, image_url=None):
    previous = operation(data, "receipt")
    if previous:
        return db.session.get(Item, previous)
    if data.get("item_id"):
        item = db.session.get(Item, integer(data["item_id"], "Item ID"))
        if item is None:
            raise ValueError("Item not found.")
    else:
        item = new_item(data)
    add_batch(item, data)
    if image_url:
        item.image_url = image_url
    operation(data, "receipt", item.id)
    return item


@atomic
def delete_items(ids):
    ids = {integer(value, "Item ID") for value in ids}
    if not ids:
        raise ValueError("Select at least one item.")
    items = db.session.scalars(db.select(Item).where(Item.id.in_(ids))).all()
    if len(items) != len(ids):
        raise ValueError("An item no longer exists. Reload the list.")
    for item in items:
        referenced = db.session.scalar(db.select(OrderLine.id).where(OrderLine.item_id == item.id))
        if item.batches or referenced:
            raise ValueError("Products with batch or order history cannot be deleted.")
        db.session.delete(item)
