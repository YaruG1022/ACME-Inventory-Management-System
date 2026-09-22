"""Batch balances and auditable transactions. Quantities use each product's base unit."""

import hashlib
import json
from datetime import date, timedelta
from functools import wraps

from flask import has_request_context
from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Operation, StockBatch, StockMovement
from .validation import integer, parse_date, required_text


def atomic(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            # SQLite is the supported runtime. Acquire the writer lock before reading balances.
            if db.engine.dialect.name == "sqlite":
                db.session.execute(text("BEGIN IMMEDIATE"))
            result = function(*args, **kwargs)
            db.session.commit()
            return result
        except IntegrityError:
            db.session.rollback()
            raise ValueError(
                "SKU or batch code already exists, or a stock constraint failed."
            ) from None
        except Exception:
            db.session.rollback()
            raise

    return wrapped


def actor_name():
    if has_request_context() and current_user.is_authenticated:
        return f"{current_user.name} (#{current_user.id})"
    return "System"


def operation(data, scope, result_id=None):
    key = data.get("request_key")
    if not key:
        return None
    key = required_text(key, "Request key", 100)
    payload = {k: v for k, v in data.items() if k not in {"request_key", "csrf_token"}}
    fingerprint = hashlib.sha256(
        json.dumps([scope, actor_name(), payload], sort_keys=True).encode()
    ).hexdigest()
    previous = db.session.get(Operation, key)
    if previous:
        if previous.fingerprint != fingerprint:
            raise ValueError("This request key was already used for different details. Reload.")
        return previous.result_id
    if result_id is not None:
        db.session.add(Operation(key=key, fingerprint=fingerprint, result_id=result_id))
    return None


def movement(batch, kind, delta, reason, reserved_delta=0, order_id=None):
    db.session.flush()
    db.session.add(
        StockMovement(
            batch_id=batch.id,
            kind=kind,
            delta=delta,
            reserved_delta=reserved_delta,
            balance=batch.quantity,
            reserved_balance=batch.reserved,
            reason=reason,
            actor=actor_name(),
            order_id=order_id,
        )
    )


def sync_item(item):
    db.session.flush()
    item.quantity = sum(batch.quantity for batch in item.batches)
    remaining = [b for b in item.batches if b.quantity > 0]
    if remaining:
        item.received_on = min(b.received_on for b in remaining)
        item.expires_on = min(b.expires_on for b in remaining)


def stock_summary(item, on_date=None):
    today = date.today()
    on_date = max(today, on_date or today)
    batches = item.batches
    usable = [
        b
        for b in batches
        if b.status == "Available" and b.expires_on >= on_date and b.received_on <= today
    ]
    return {
        "on_hand": sum(b.quantity for b in batches),
        "reserved": sum(b.reserved for b in batches),
        "available": sum(b.quantity - b.reserved for b in usable),
        "unusable": sum(b.quantity for b in batches if b not in usable),
        "expired": sum(b.quantity for b in batches if b.expires_on < today),
        "expiring": sum(
            b.quantity for b in batches if today <= b.expires_on <= today + timedelta(days=7)
        ),
        "low_stock": sum(b.quantity - b.reserved for b in usable) < item.minimum_stock,
    }


def add_batch(item, data, kind="Receipt"):
    quantity = integer(data.get("quantity"), "Quantity", minimum=0 if kind == "Opening" else 1)
    received = parse_date(data.get("received_on"), "Received date")
    expires = parse_date(data.get("expires_on"), "Expiration date")
    if received > date.today():
        raise ValueError("Received date cannot be in the future.")
    if expires < received:
        raise ValueError("Expiration date cannot precede the received date.")
    import secrets

    code = required_text(
        data.get("batch_code") or f"LOT-{secrets.token_hex(4).upper()}", "Batch code", 64
    )
    batch = StockBatch(
        item=item,
        code=code,
        quantity=quantity,
        reserved=0,
        received_on=received,
        expires_on=expires,
        status="Available",
        source=required_text(data.get("source") or "Unspecified", "Source"),
    )
    db.session.add(batch)
    movement(batch, kind, quantity, data.get("reason") or "Stock received")
    sync_item(item)
    return batch


def list_batches(item_id=None, days=None, expired=False, category=None):
    query = db.select(StockBatch).order_by(StockBatch.expires_on, StockBatch.id)
    if item_id:
        query = query.where(StockBatch.item_id == integer(item_id, "Product ID"))
    batches = db.session.scalars(query).all()
    if category:
        batches = [b for b in batches if b.item.category == category]
    if expired:
        batches = [b for b in batches if b.quantity > 0 and b.expires_on < date.today()]
    elif days is not None:
        days = integer(days, "Days", minimum=0)
        if days > 3650:
            raise ValueError("Days must not exceed 3650.")
        end = date.today() + timedelta(days=days)
        batches = [b for b in batches if b.quantity > 0 and date.today() <= b.expires_on <= end]
    return batches


@atomic
def adjust_batch(batch_id, data):
    batch = db.session.get(StockBatch, batch_id)
    if batch is None:
        raise ValueError("Batch not found.")
    if operation(data, f"adjust:{batch_id}"):
        return batch
    reason = required_text(data.get("reason"), "Reason")
    action = data.get("action")
    delta = 0
    if action == "count":
        count = integer(data.get("counted_quantity"), "Physical count", minimum=0)
        expected = integer(data.get("expected_quantity"), "Previous on-hand quantity", minimum=0)
        if batch.quantity != expected:
            raise ValueError("Stock changed since you opened this form. Reload and count again.")
        if count < batch.reserved:
            raise ValueError("Count is below reserved stock. Cancel affected orders first.")
        delta = count - batch.quantity
        batch.quantity = count
        kind = "Count"
    elif action == "dispose":
        quantity = integer(data.get("quantity"), "Quantity")
        if quantity > batch.quantity - batch.reserved:
            raise ValueError("Cannot dispose of reserved or unavailable quantities.")
        delta = -quantity
        batch.quantity -= quantity
        kind = "Disposal"
    elif action in {"quarantine", "release"}:
        if batch.reserved:
            raise ValueError("Cancel affected orders before changing this batch's status.")
        target = "Quarantined" if action == "quarantine" else "Available"
        if batch.status == target:
            raise ValueError("Batch already has this status.")
        batch.status = target
        kind = "Quarantine" if action == "quarantine" else "Release"
    else:
        raise ValueError("Choose count, dispose, quarantine, or release.")
    movement(batch, kind, delta, reason)
    sync_item(batch.item)
    operation(data, f"adjust:{batch_id}", batch.id)
    return batch


def list_movements(item_id=None, kind=None):
    query = db.select(StockMovement).join(StockBatch).order_by(StockMovement.id.desc())
    if item_id:
        query = query.where(StockBatch.item_id == integer(item_id, "Product ID"))
    if kind:
        query = query.where(StockMovement.kind == kind)
    return db.session.scalars(query).all()
