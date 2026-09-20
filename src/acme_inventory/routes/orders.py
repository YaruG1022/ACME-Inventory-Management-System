from flask import Blueprint, jsonify, render_template
from flask_login import login_required

from ..services import orders
from ..services.inventory import list_items
from .common import json_object, validation_errors

bp = Blueprint("orders", __name__)


@bp.get("/orders")
@login_required
def index():
    records = orders.list_orders()
    return render_template(
        "orders/list.html",
        title="Orders",
        orders=records,
        details={order.id: orders.order_details(order) for order in records},
    )


@bp.get("/add_order")
@login_required
def create_page():
    return render_template("orders/create.html", title="Create order", items=list_items())


@bp.post("/api/orders")
@login_required
@validation_errors
def create():
    return jsonify(orders.create_order(json_object()).serialize()), 201
