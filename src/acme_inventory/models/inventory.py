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
    sku = db.Column(db.String(64), unique=True)
    unit = db.Column(db.String(32), nullable=False, default="unit")
    aliases = db.Column(db.String(500), nullable=False, default="")
    minimum_stock = db.Column(db.Integer, nullable=False, default=0)
    batches = db.relationship("StockBatch", back_populates="item", lazy="selectin")

    def serialize(self):
        from ..services.stock import stock_summary

        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "received_on": self.received_on.isoformat(),
            "expires_on": self.expires_on.isoformat(),
            "image_url": self.image_url,
            "sku": self.sku,
            "unit": self.unit,
            "aliases": self.aliases,
            "minimum_stock": self.minimum_stock,
            **stock_summary(self),
        }
