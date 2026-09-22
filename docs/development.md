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

The original item and order payloads below are extended by the Batch inventory
release section. Opening stock accepts quantity, received_on and expires_on;
subsequent balance changes require audited batch operations.
Order payload: ordered_on, recipient_name, recipient_address, items (objects with
item_id and quantity). Export payload: report_type and format (`csv` or `xlsx`).
Delete payload: ids list. HTML forms send csrf_token; JSON uses X-CSRF-Token from
the page meta tag. Operational endpoints require login. Logout is now POST.

## Validation

`python -m pytest` runs against temporary data, covering authentication/CSRF,
inventory, order rollback, export, images, page assets, and legacy import.
`python -m ruff check src/acme_inventory tests` checks code quality.
`python -m build` verifies packaging; templates and assets are included in wheels.


## Batch inventory release

New pages: `/stock` and `/movements`. Run `flask --app acme_inventory upgrade-db`
with the server stopped before using this release with an existing database.
`init-db` now uses the same versioned upgrade path; import-legacy upgrades its copy.

| Endpoint | Payload / query |
| --- | --- |
| GET /api/items | search, category, status (available/out/low/expired/expiring), on_date |
| POST /api/items | name, category, optional sku/unit/aliases/minimum_stock; optional opening quantity and dates |
| PUT /api/items/{id} | name, category, sku, unit, aliases, minimum_stock; balance/date edits rejected |
| GET /api/batches | item_id, category, days, expired=1 |
| POST /api/receipts | item_id OR new-product fields; quantity, received_on, expires_on, optional batch_code/source |
| POST /api/batches/{id}/adjust | action=count/dispose/quarantine/release, reason; count uses counted_quantity + expected_quantity; disposal uses quantity |
| GET /api/movements | item_id, kind |
| POST /api/orders/preview | ordered_on, scheduled_on, recipient_name, recipient_address, items [{item_id, quantity}] |
| POST /api/orders | same as preview; creates reservations, not physical deductions |
| GET /api/orders/{id} | Returns status, normalized lines and batch allocations |
| POST /api/orders/{id}/transition | action=cancel/fulfill, reason, optional delivered_on (defaults to today) |

Product creation, receipts, batch adjustments, and order writes accept optional
`request_key`. The UI supplies one for these writes. Successful retries with the
same payload return the existing result; reusing a key with different details fails.
Failed writes do not consume a key. All endpoints use the existing login and CSRF
mechanism. The APIs are application endpoints; no Agent layer is included.

Tests cover expiry boundaries, FEFO allocation, independent lots, reservations,
cancellation, fulfillment, replay protection, concurrent writes, stale physical
counts, protected history, migration re-entry, page assets and all report formats.
