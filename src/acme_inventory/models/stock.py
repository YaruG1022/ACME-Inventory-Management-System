from datetime import datetime, timezone

from ..extensions import db


class StockBatch(db.Model):
    __tablename__ = "stock_batch"
    __table_args__ = (
        db.CheckConstraint("quantity >= 0 AND reserved >= 0 AND reserved <= quantity"),
        db.UniqueConstraint("item_id", "code"),
    )
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False, index=True)
    code = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reserved = db.Column(db.Integer, nullable=False, default=0)
    received_on = db.Column(db.Date, nullable=False)
    expires_on = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Available")
    source = db.Column(db.String(255), nullable=False, default="")
    item = db.relationship("Item", back_populates="batches")

    def serialize(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "code": self.code,
            "name": self.item.name,
            "sku": self.item.sku,
            "unit": self.item.unit,
            "category": self.item.category,
            "quantity": self.quantity,
            "reserved": self.reserved,
            "received_on": self.received_on.isoformat(),
            "expires_on": self.expires_on.isoformat(),
            "status": self.status,
            "source": self.source,
        }


class StockMovement(db.Model):
    __tablename__ = "stock_movement"
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("stock_batch.id"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"))
    kind = db.Column(db.String(32), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reserved_delta = db.Column(db.Integer, nullable=False, default=0)
    balance = db.Column(db.Integer, nullable=False)
    reserved_balance = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    actor = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    batch = db.relationship("StockBatch")

    def serialize(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "batch": self.batch.code,
            "item_id": self.batch.item_id,
            "name": self.batch.item.name,
            "sku": self.batch.item.sku,
            "unit": self.batch.item.unit,
            "order_id": self.order_id,
            "kind": self.kind,
            "delta": self.delta,
            "reserved_delta": self.reserved_delta,
            "balance": self.balance,
            "reserved_balance": self.reserved_balance,
            "reason": self.reason,
            "actor": self.actor,
            "created_at": self.created_at.isoformat() + "Z",
        }


class Operation(db.Model):
    """Deduplicate successful writes; failed writes never retain a key."""

    __tablename__ = "operation"
    key = db.Column(db.String(100), primary_key=True)
    fingerprint = db.Column(db.String(64), nullable=False)
    result_id = db.Column(db.Integer, nullable=False)


class SchemaVersion(db.Model):
    __tablename__ = "schema_version"
    version = db.Column(db.Integer, primary_key=True)
