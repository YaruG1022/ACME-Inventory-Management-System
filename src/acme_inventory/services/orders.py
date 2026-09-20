from sqlalchemy import update

from ..extensions import db
from ..models import Item, Order
from .validation import integer, parse_date, required_text


def create_order(data):
    lines = data.get("items")
    if not isinstance(lines, list) or not lines:
        raise ValueError("Add at least one item.")
    quantities = {}
    for line in lines:
        if not isinstance(line, dict):
            raise ValueError("Invalid order line.")
        item_id = integer(line.get("item_id"), "Item ID")
        quantities[item_id] = quantities.get(item_id, 0) + integer(line.get("quantity"), "Quantity")
    encoded = ",".join(f"{item_id}x{quantity}" for item_id, quantity in quantities.items())
    if len(encoded) > 255:
        raise ValueError("This order contains too many items.")
    order = Order(
        ordered_on=parse_date(data.get("ordered_on"), "Order date"),
        recipient_name=required_text(data.get("recipient_name"), "Recipient name"),
        recipient_address=required_text(data.get("recipient_address"), "Recipient address"),
        status="Confirmed",
        items=encoded,
    )
    try:
        for item_id, quantity in quantities.items():
            result = db.session.execute(
                update(Item)
                .where(Item.id == item_id, Item.quantity >= quantity)
                .values(quantity=Item.quantity - quantity)
            )
            if result.rowcount != 1:
                raise ValueError(f"Item #{item_id} is missing or has insufficient stock.")
        db.session.add(order)
        db.session.commit()
        return order
    except Exception:
        db.session.rollback()
        raise


def list_orders():
    return db.session.scalars(db.select(Order).order_by(Order.id.desc())).all()


def order_details(order):
    details = []
    for entry in order.items.split(","):
        item_id, quantity = map(int, entry.split("x"))
        item = db.session.get(Item, item_id)
        details.append((item.name if item else f"Unavailable item #{item_id}", quantity))
    return details
