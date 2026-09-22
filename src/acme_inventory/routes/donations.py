import secrets

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..services.image_storage import store_image
from ..services.inventory import list_items, receive_donation

bp = Blueprint("donations", __name__)


@bp.get("/add_donation")
@login_required
def create_page():
    return render_template(
        "donations/create.html",
        title="Add donation",
        items=list_items(),
        request_key=secrets.token_urlsafe(24),
    )


@bp.post("/additem")
@login_required
def create():
    try:
        file = request.files.get("image")
        image_url = store_image(file, "items") if file and file.filename else None
        receive_donation(request.form, image_url)
        flash("Donation received.")
        return redirect(url_for("inventory.index"))
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("donations.create_page"))
