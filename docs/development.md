# Development and migration

Install `.[dev]` and run commands from the repository root. Package configuration,
dependencies, pytest and lint settings live in pyproject.toml.

## Configuration

Flask CLI loads `.env`; WSGI deployments must supply process environment variables.

| Variable | Meaning |
| --- | --- |
| ACME_INSTANCE_PATH | Absolute runtime directory; defaults to Flask's instance path |
| ACME_DATABASE_URL | Database URL; default is inventory.db in the instance directory |
| ACME_UPLOAD_DIR | Upload directory, separate from image URL paths |
| ACME_SECRET_KEY | Stable secret; local default is generated in instance/secret.txt |
| FLASK_DEBUG | Explicit Flask CLI debug setting |

The old server.ini and certificate placeholders are retired. Use a production
WSGI server and HTTPS reverse proxy for deployment.

## Legacy import

Stop the old app and back up its database/images. Set a fresh ACME_INSTANCE_PATH,
then run `flask --app acme_inventory import-legacy --database <old-db> --images <old-images>`.
Do not run init-db first. The importer refuses an existing destination, uses SQLite
backup, and rewrites image references only in the copy. Omitting --images uses
bundled placeholders. Source files are unchanged. Users sign in again because
the old session secret is not imported; their passwords and TOTP secrets remain.

## HTTP changes

Page URLs remain /, /home, /inventory, /add_donation, /orders, /add_order, /report,
/account, /login_form, and /signup_form. Prototype /item_form, /item_list, /login_test,
and /success are removed. Old JSON APIs are replaced; update external clients:

| Previous | Replacement |
| --- | --- |
| GET /getInventoryData, /search_item | GET /api/items?search=... |
| POST /addItem | POST /api/items |
| POST /updateItem | PUT /api/items/{id} |
| POST /deleteItem | POST /api/items/delete |
| POST /neworder | POST /api/orders |
| GET /getReportData | GET /api/reports?report_type=inventory or orders |
| POST /generateReport | POST /api/reports/export |

Item payload: name, category, quantity, received_on, expires_on.
Order payload: ordered_on, recipient_name, recipient_address, items (objects with
item_id and quantity). Export payload: report_type and format (`csv` or `xlsx`).
Delete payload: ids list. HTML forms send csrf_token; JSON uses X-CSRF-Token from
the page meta tag. Operational endpoints require login. Logout is now POST.

## Validation

`python -m pytest` runs against temporary data, covering authentication/CSRF,
inventory, order rollback, export, images, page assets, and legacy import.
`python -m ruff check src/acme_inventory tests` checks code quality.
`python -m build` verifies packaging; templates and assets are included in wheels.

