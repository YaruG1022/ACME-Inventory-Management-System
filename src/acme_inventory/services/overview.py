"""Read-only dashboard summaries using the existing inventory model."""

from datetime import date, timedelta

from ..extensions import db
from ..models import Item, Order


def inventory_overview():
    today = date.today()
    items = db.session.scalars(db.select(Item).order_by(Item.expires_on, Item.id)).all()
    expiring = [
        item
        for item in items
        if item.quantity > 0 and today <= item.expires_on <= today + timedelta(days=7)
    ]
    expired = [item for item in items if item.quantity > 0 and item.expires_on < today]
    recent_orders = db.session.scalars(db.select(Order).order_by(Order.id.desc()).limit(5)).all()
    return {
        "total": len(items),
        "in_stock": sum(item.quantity > 0 for item in items),
        "out_of_stock": sum(item.quantity == 0 for item in items),
        "expiring": expiring,
        "expired": expired,
        "attention": (expired + expiring)[:5],
        "food": sum(item.category == "Food" for item in items),
        "hygiene": sum(item.category == "Hygiene" for item in items),
        "order_count": db.session.scalar(db.select(db.func.count()).select_from(Order)),
        "recent_orders": recent_orders,
        "today": today,
    }
