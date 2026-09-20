from ..extensions import db


class Item(db.Model):
    __tablename__ = "item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column("type", db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    received_on = db.Column("stockdate", db.Date, nullable=False)
    expires_on = db.Column("expdate", db.Date, nullable=False)
    image_url = db.Column("image", db.String(255), default="/static/images/placeholder.svg")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "received_on": self.received_on.isoformat(),
            "expires_on": self.expires_on.isoformat(),
            "image_url": self.image_url,
        }
