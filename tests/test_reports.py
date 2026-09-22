from io import BytesIO
from zipfile import ZipFile


def test_empty_report_and_both_export_formats(api):
    for report_type in ("inventory", "orders", "batches", "movements"):
        response = api("GET", f"/api/reports?report_type={report_type}")
        assert response.status_code == 200
        assert response.json["columns"]
        assert response.json["data"] == []
        for extension in ("csv", "xlsx"):
            response = api(
                "POST", "/api/reports/export", {"report_type": report_type, "format": extension}
            )
            assert response.status_code == 200
            assert f"report.{extension}" in response.headers["Content-Disposition"]
            if extension == "xlsx":
                with ZipFile(BytesIO(response.data)) as archive:
                    assert "xl/worksheets/sheet1.xml" in archive.namelist()
            else:
                assert "id," in response.data.decode("utf-8-sig")


def test_report_values_and_formula_escaping(api, item_data):
    api("POST", "/api/items", {**item_data, "name": "=1+1"})
    preview = api("GET", "/api/reports?report_type=inventory").json
    assert preview["data"][0]["name"] == "=1+1"
    response = api("POST", "/api/reports/export", {"report_type": "inventory", "format": "csv"})
    assert "'=1+1" in response.data.decode("utf-8-sig")
    assert api("GET", "/api/reports?report_type=invalid").status_code == 400
    assert (
        api(
            "POST", "/api/reports/export", {"report_type": "inventory", "format": "pdf"}
        ).status_code
        == 400
    )
