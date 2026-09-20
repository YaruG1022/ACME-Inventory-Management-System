import csv
from io import BytesIO, StringIO

import xlsxwriter

from .inventory import list_items
from .orders import list_orders

REPORT_COLUMNS = {
    "inventory": ["id", "name", "category", "quantity", "received_on", "expires_on", "image_url"],
    "orders": [
        "id",
        "ordered_on",
        "delivered_on",
        "status",
        "items",
        "recipient_name",
        "recipient_address",
    ],
}


def report_data(report_type):
    if report_type not in REPORT_COLUMNS:
        raise ValueError("Choose a valid report type.")
    rows = list_items() if report_type == "inventory" else list_orders()
    return {"columns": REPORT_COLUMNS[report_type], "data": [row.serialize() for row in rows]}


def export_report(report_type, export_format):
    report = report_data(report_type)
    columns = report["columns"]
    rows = [[row[column] for column in columns] for row in report["data"]]
    if export_format == "csv":
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(
                [
                    "'" + value
                    if isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
                    else value
                    for value in row
                ]
            )
        return output.getvalue().encode("utf-8-sig"), "text/csv", "csv"
    if export_format == "xlsx":
        output = BytesIO()
        with xlsxwriter.Workbook(
            output, {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False}
        ) as workbook:
            sheet = workbook.add_worksheet("Report")
            sheet.write_row(0, 0, columns)
            for index, row in enumerate(rows, 1):
                sheet.write_row(index, 0, row)
        return (
            output.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx",
        )
    raise ValueError("Choose CSV or XLSX.")
