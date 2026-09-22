from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from ..services import inventory
from ..services.stock import stock_summary
from ..services.validation import integer, parse_date
from .common import json_object, validation_errors

bp = Blueprint("inventory", __name__)


@bp.get("/inventory")
@login_required
def index():
    return render_template("inventory/list.html", title="Inventory")


@bp.get("/api/items")
@login_required
@validation_errors
def list_items():
    when = request.args.get("on_date")
    records = inventory.list_items(
        request.args.get("search", ""),
        request.args.get("category"),
        request.args.get("status"),
        when,
    )
    return jsonify(
        [
            {
                **item.serialize(),
                **stock_summary(item, parse_date(when, "Availability date") if when else None),
            }
            for item in records
        ]
    )


@bp.post("/api/items")
@login_required
@validation_errors
def create_item():
    return jsonify(inventory.save_item(json_object()).serialize()), 201


@bp.put("/api/items/<int:item_id>")
@login_required
@validation_errors
def update_item(item_id):
    return jsonify(inventory.save_item(json_object(), item_id).serialize())


@bp.post("/api/items/delete")
@login_required
@validation_errors
def delete_items():
    ids = json_object().get("ids")
    if not isinstance(ids, list):
        raise ValueError("Select items to delete.")
    inventory.delete_items([integer(value, "Item ID") for value in ids])
    return jsonify(message="Items deleted.")
