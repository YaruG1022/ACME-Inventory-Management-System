from ..extensions import db


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    ordered_on = db.Column("orderdate", db.Date, nullable=False)
    delivered_on = db.Column("deliverydate", db.Date)
    status = db.Column(db.String(255), nullable=False)
    # Retained for historical exports; normalized lines are authoritative for new orders.
    items = db.Column(db.String(255), nullable=False)
    recipient_name = db.Column(db.String(255), nullable=False)
    recipient_address = db.Column(db.String(255), nullable=False)
    scheduled_on = db.Column(db.Date)
    legacy_status = db.Column(db.String(255))
    lines = db.relationship("OrderLine", back_populates="order", lazy="selectin")

    def serialize(self):
        return {
            "id": self.id,
            "ordered_on": self.ordered_on.isoformat(),
            "delivered_on": self.delivered_on.isoformat() if self.delivered_on else None,
            "status": self.status,
            "items": self.items,
            "recipient_name": self.recipient_name,
            "recipient_address": self.recipient_address,
            "scheduled_on": self.scheduled_on.isoformat() if self.scheduled_on else None,
            "legacy_status": self.legacy_status,
            "lines": [line.serialize() for line in self.lines],
        }


class OrderLine(db.Model):
    __tablename__ = "order_line"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(32), nullable=False)
    order = db.relationship("Order", back_populates="lines")
    allocations = db.relationship("OrderAllocation", lazy="selectin")

    def serialize(self):
        return {
            "item_id": self.item_id,
            "name": self.product_name,
            "unit": self.unit,
            "quantity": self.quantity,
            "allocations": [
                {"batch_id": a.batch_id, "quantity": a.quantity} for a in self.allocations
            ],
        }


class OrderAllocation(db.Model):
    __tablename__ = "order_allocation"
    id = db.Column(db.Integer, primary_key=True)
    line_id = db.Column(db.Integer, db.ForeignKey("order_line.id"), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("stock_batch.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
