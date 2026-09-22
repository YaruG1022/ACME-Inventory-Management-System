from datetime import date

from ..extensions import db
from ..models import Item, Order, OrderAllocation, OrderLine, StockBatch
from .stock import atomic, movement, operation, stock_summary, sync_item
from .validation import integer, parse_date, required_text


def order_values(data):
    lines = data.get("items")
    if not isinstance(lines, list) or not lines:
        raise ValueError("Add at least one product.")
    quantities = {}
    for line in lines:
        if not isinstance(line, dict):
            raise ValueError("Invalid order line.")
        item_id = integer(line.get("item_id"), "Item ID")
        quantities[item_id] = quantities.get(item_id, 0) + integer(line.get("quantity"), "Quantity")
    ordered = parse_date(data.get("ordered_on"), "Order date")
    scheduled = parse_date(data.get("scheduled_on") or data.get("ordered_on"), "Scheduled date")
    if scheduled < ordered:
        raise ValueError("Scheduled date cannot precede the order date.")
    if scheduled < date.today():
        raise ValueError("Scheduled date cannot be in the past.")
    return quantities, dict(
        ordered_on=ordered,
        scheduled_on=scheduled,
        recipient_name=required_text(data.get("recipient_name"), "Recipient name"),
        recipient_address=required_text(data.get("recipient_address"), "Address"),
    )


def build_plan(quantities, scheduled):
    result = []
    for item_id, quantity in quantities.items():
        item = db.session.get(Item, item_id)
        if item is None:
            raise ValueError(f"Product #{item_id} does not exist.")
        need = quantity
        allocations = []
        for batch in sorted(item.batches, key=lambda b: (b.expires_on, b.id)):
            if (
                batch.status != "Available"
                or batch.expires_on < max(scheduled, date.today())
                or batch.received_on > date.today()
            ):
                continue
            take = min(need, batch.quantity - batch.reserved)
            if take:
                allocations.append({"batch_id": batch.id, "code": batch.code, "quantity": take})
                need -= take
            if not need:
                break
        result.append(
            {
                "item_id": item.id,
                "name": item.name,
                "sku": item.sku,
                "unit": item.unit,
                "quantity": quantity,
                "available": stock_summary(item, scheduled)["available"],
                "shortage": need,
                "allocations": allocations,
            }
        )
    return {"can_fulfill": all(line["shortage"] == 0 for line in result), "lines": result}


def preview_order(data):
    quantities, values = order_values(data)
    return build_plan(quantities, values["scheduled_on"])


@atomic
def create_order(data):
    previous = operation(data, "order")
    if previous:
        return db.session.get(Order, previous)
    quantities, values = order_values(data)
    plan = build_plan(quantities, values["scheduled_on"])
    if not plan["can_fulfill"]:
        missing = "; ".join(
            f"{x['name']}: short {x['shortage']} {x['unit']}"
            for x in plan["lines"]
            if x["shortage"]
        )
        raise ValueError(f"Insufficient eligible stock. {missing}")
    encoded = ",".join(f"{key}x{value}" for key, value in quantities.items())
    order = Order(**values, status="Reserved", items=encoded)
    db.session.add(order)
    db.session.flush()
    for planned in plan["lines"]:
        line = OrderLine(
            order=order,
            item_id=planned["item_id"],
            quantity=planned["quantity"],
            product_name=planned["name"],
            unit=planned["unit"],
        )
        db.session.add(line)
        db.session.flush()
        for allocated in planned["allocations"]:
            batch = db.session.get(StockBatch, allocated["batch_id"])
            quantity = allocated["quantity"]
            batch.reserved += quantity
            db.session.add(OrderAllocation(line_id=line.id, batch_id=batch.id, quantity=quantity))
            movement(batch, "Reservation", 0, "Order confirmed", quantity, order.id)
    operation(data, "order", order.id)
    return order


@atomic
def transition_order(order_id, data):
    order = db.session.get(Order, order_id)
    if order is None:
        raise ValueError("Order not found.")
    if operation(data, f"transition:{order_id}"):
        return order
    if order.status != "Reserved":
        raise ValueError("Only reserved orders can be cancelled or fulfilled.")
    action = data.get("action")
    if action not in {"cancel", "fulfill"}:
        raise ValueError("Choose cancel or fulfill.")
    reason = required_text(data.get("reason"), "Reason")
    delivered = parse_date(data.get("delivered_on") or date.today().isoformat(), "Delivery date")
    if action == "fulfill" and (delivered < order.ordered_on or delivered > date.today()):
        raise ValueError("Delivery date must be between the order date and today.")
    affected = set()
    for line in order.lines:
        for allocation in line.allocations:
            batch = db.session.get(StockBatch, allocation.batch_id)
            if action == "fulfill" and (
                batch.status != "Available"
                or batch.expires_on < max(date.today(), delivered)
                or batch.received_on > delivered
            ):
                raise ValueError(
                    "A reserved batch is no longer eligible. Cancel and re-create the order."
                )
            if batch.reserved < allocation.quantity:
                raise ValueError("Reservation mismatch. Contact an administrator.")
            batch.reserved -= allocation.quantity
            delta = -allocation.quantity if action == "fulfill" else 0
            batch.quantity += delta
            movement(
                batch,
                "Fulfillment" if action == "fulfill" else "Cancellation",
                delta,
                reason,
                -allocation.quantity,
                order.id,
            )
            affected.add(batch.item)
    for item in affected:
        sync_item(item)
    order.status = "Fulfilled" if action == "fulfill" else "Cancelled"
    order.delivered_on = delivered if action == "fulfill" else None
    operation(data, f"transition:{order_id}", order.id)
    return order


def list_orders():
    return db.session.scalars(db.select(Order).order_by(Order.id.desc())).all()


def order_details(order):
    return [(f"{line.product_name} ({line.unit})", line.quantity) for line in order.lines]
