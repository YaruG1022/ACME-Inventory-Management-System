"""Dashboard summaries derived from batch balances."""

from datetime import date
from types import SimpleNamespace

from ..extensions import db
from ..models import Item, Order
from .stock import list_batches, stock_summary


def inventory_overview():
    items = db.session.scalars(db.select(Item).order_by(Item.id)).all()
    summaries = [stock_summary(item) for item in items]
    expiring = list_batches(days=7)
    expired = list_batches(expired=True)
    attention = [
        SimpleNamespace(
            name=b.item.name,
            category=f"{b.item.sku} / {b.code}",
            quantity=b.quantity,
            unit=b.item.unit,
            expires_on=b.expires_on,
        )
        for b in (expired + expiring)[:5]
    ]
    return {
        "total": len(items),
        "in_stock": sum(item.quantity > 0 for item in items),
        "out_of_stock": sum(s["available"] == 0 for s in summaries),
        "low_stock": sum(s["low_stock"] for s in summaries),
        "expiring": expiring,
        "expired": expired,
        "attention": attention,
        "food": sum(item.category == "Food" for item in items),
        "hygiene": sum(item.category == "Hygiene" for item in items),
        "order_count": db.session.scalar(db.select(db.func.count()).select_from(Order)),
        "recent_orders": db.session.scalars(
            db.select(Order).order_by(Order.id.desc()).limit(5)
        ).all(),
        "today": date.today(),
    }
