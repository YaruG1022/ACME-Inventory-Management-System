from datetime import date

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from ..services import inventory, stock
from .common import json_object, validation_errors

bp = Blueprint("stock", __name__)


@bp.get("/stock")
@login_required
def index():
    return render_template(
        "inventory/stock.html",
        title="Batches & stock",
        today=date.today(),
        items=inventory.list_items(),
    )


@bp.get("/movements")
@login_required
def movements_page():
    return render_template(
        "inventory/movements.html", title="Stock movements", items=inventory.list_items()
    )


@bp.get("/api/batches")
@login_required
@validation_errors
def batches():
    return jsonify(
        [
            b.serialize()
            for b in stock.list_batches(
                request.args.get("item_id"),
                request.args.get("days"),
                request.args.get("expired") == "1",
                request.args.get("category"),
            )
        ]
    )


@bp.post("/api/receipts")
@login_required
@validation_errors
def receive():
    return jsonify(inventory.receive_donation(json_object()).serialize()), 201


@bp.post("/api/batches/<int:batch_id>/adjust")
@login_required
@validation_errors
def adjust(batch_id):
    return jsonify(stock.adjust_batch(batch_id, json_object()).serialize())


@bp.get("/api/movements")
@login_required
@validation_errors
def movements():
    return jsonify(
        [
            m.serialize()
            for m in stock.list_movements(request.args.get("item_id"), request.args.get("kind"))
        ]
    )
