from datetime import date

from flask import Blueprint, jsonify, render_template
from flask_login import login_required

from ..extensions import db
from ..models import Order
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
        today=date.today(),
    )


@bp.get("/add_order")
@login_required
def create_page():
    return render_template(
        "orders/create.html",
        title="Create order",
        items=[item.serialize() for item in list_items()],
        today=date.today(),
    )


@bp.post("/api/orders")
@login_required
@validation_errors
def create():
    return jsonify(orders.create_order(json_object()).serialize()), 201


@bp.post("/api/orders/preview")
@login_required
@validation_errors
def preview():
    return jsonify(orders.preview_order(json_object()))


@bp.get("/api/orders/<int:order_id>")
@login_required
@validation_errors
def detail(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        raise ValueError("Order not found.")
    return jsonify(order.serialize())


@bp.post("/api/orders/<int:order_id>/transition")
@login_required
@validation_errors
def transition(order_id):
    return jsonify(orders.transition_order(order_id, json_object()).serialize())
