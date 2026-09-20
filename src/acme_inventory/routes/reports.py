from flask import Blueprint, jsonify, make_response, render_template, request
from flask_login import login_required

from ..services.reports import export_report, report_data
from .common import json_object, validation_errors

bp = Blueprint("reports", __name__)


@bp.get("/report")
@login_required
def index():
    return render_template("reports/index.html", title="Reports")


@bp.get("/api/reports")
@login_required
@validation_errors
def preview():
    return jsonify(report_data(request.args.get("report_type", "inventory")))


@bp.post("/api/reports/export")
@login_required
@validation_errors
def export():
    data = json_object()
    content, content_type, extension = export_report(data.get("report_type"), data.get("format"))
    response = make_response(content)
    response.headers["Content-Type"] = content_type
    response.headers["Content-Disposition"] = f"attachment; filename=report.{extension}"
    return response
