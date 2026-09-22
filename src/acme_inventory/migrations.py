"""Versioned, additive migration of the original SQLite schema."""

import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect, text

from .extensions import db
from .models import Item, Order, OrderLine, SchemaVersion, StockBatch, StockMovement


def upgrade_database():
    if db.engine.dialect.name != "sqlite":
        raise ValueError("This migration supports SQLite only.")
    tables = inspect(db.engine).get_table_names()
    if "schema_version" in tables:
        with db.engine.connect() as connection:
            if connection.execute(
                text("SELECT version FROM schema_version WHERE version=1")
            ).first():
                return None
    backup = None
    path = db.engine.url.database
    if tables and path and path != ":memory:":
        source = Path(path).resolve()
        backup = source.with_name(source.name + f".before-v1-{datetime.now():%Y%m%d-%H%M%S-%f}.bak")
        with sqlite3.connect(source) as origin, sqlite3.connect(backup) as destination:
            origin.backup(destination)
    # SQLite DDL and the data backfill share a single explicit transaction.
    db.session.remove()
    with db.engine.connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            additions = {
                "item": {
                    "sku": "VARCHAR(64)",
                    "unit": "VARCHAR(32) NOT NULL DEFAULT 'unit'",
                    "aliases": "VARCHAR(500) NOT NULL DEFAULT ''",
                    "minimum_stock": "INTEGER NOT NULL DEFAULT 0",
                },
                "order": {"scheduled_on": "DATE", "legacy_status": "VARCHAR(255)"},
            }
            for table, columns in additions.items():
                if table not in tables:
                    continue
                present = {c["name"] for c in inspect(connection).get_columns(table)}
                for name, definition in columns.items():
                    if name not in present:
                        connection.exec_driver_sql(
                            f'ALTER TABLE "{table}" ADD COLUMN {name} {definition}'
                        )
            db.metadata.create_all(connection)
            connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_item_sku ON item(sku)")
            # A separate session bound to this transaction makes the migration atomic.
            from sqlalchemy.orm import Session

            with Session(bind=connection) as session:
                for item in session.scalars(db.select(Item)):
                    item.sku = item.sku or f"ACME-{item.id:06d}"
                    if not item.batches:
                        batch = StockBatch(
                            item=item,
                            code=f"LEGACY-{item.id}",
                            quantity=item.quantity,
                            reserved=0,
                            received_on=item.received_on,
                            expires_on=item.expires_on,
                            status="Available",
                            source="Legacy opening balance",
                        )
                        session.add(batch)
                        session.flush()
                        session.add(
                            StockMovement(
                                batch_id=batch.id,
                                kind="Opening",
                                delta=item.quantity,
                                reserved_delta=0,
                                balance=item.quantity,
                                reserved_balance=0,
                                reason="Migrated current balance; earlier movements are unknown",
                                actor="Migration",
                            )
                        )
                for order in session.scalars(db.select(Order)):
                    if order.lines:
                        continue
                    order.legacy_status = order.status
                    order.status = "Legacy recorded"
                    order.scheduled_on = order.delivered_on or order.ordered_on
                    for entry in order.items.split(","):
                        item_id, quantity = map(int, entry.split("x"))
                        item = session.get(Item, item_id)
                        if item is None or quantity <= 0:
                            raise ValueError(
                                f"Historical order #{order.id} has invalid product data."
                            )
                        session.add(
                            OrderLine(
                                order=order,
                                item_id=item_id,
                                quantity=quantity,
                                product_name=item.name,
                                unit=item.unit,
                            )
                        )
                session.add(SchemaVersion(version=1))
                session.flush()
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return backup
