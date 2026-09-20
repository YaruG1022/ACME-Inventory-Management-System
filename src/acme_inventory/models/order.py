from ..extensions import db


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    ordered_on = db.Column("orderdate", db.Date, nullable=False)
    delivered_on = db.Column("deliverydate", db.Date)
    status = db.Column(db.String(255), nullable=False)
    # Keep the legacy representation until a separate order-line migration is introduced.
    items = db.Column(db.String(255), nullable=False)
    recipient_name = db.Column(db.String(255), nullable=False)
    recipient_address = db.Column(db.String(255), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "ordered_on": self.ordered_on.isoformat(),
            "delivered_on": self.delivered_on.isoformat() if self.delivered_on else None,
            "status": self.status,
            "items": self.items,
            "recipient_name": self.recipient_name,
            "recipient_address": self.recipient_address,
        }
