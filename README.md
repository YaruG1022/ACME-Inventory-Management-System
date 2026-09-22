# ACME Food Bank Inventory Tracking System

**English** | [简体中文](README.zh-CN.md)

A Flask application for tracking donated food and hygiene products, recipient
orders, and inventory reports. Originally created for WSU SU21 CPTS 322.

## System overview

Start with the [system overview](docs/system-overview.md) to understand the app's
purpose, terminology, workflows, structure and limits. It directs operators,
project stakeholders, testers, developers and maintainers to the relevant topic
documents. Diagrams are maintained as Mermaid inside Markdown.

## Setup

Python 3.10 or newer is required. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m flask --app acme_inventory init-db
python -m flask --app acme_inventory run
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy configuration
with `cp .env.example .env`. Open http://127.0.0.1:5000 and register a local account.
No default account or password is created.

Imports do not create database tables. `init-db` initializes a fresh database and applies the versioned schema upgrade.
For existing installations, stop the server and run `flask --app acme_inventory upgrade-db`.
The SQLite upgrade creates a timestamped backup alongside the database before making changes. Local data, secrets,
and uploads live in Flask's instance directory, outside the application package.
Set `ACME_INSTANCE_PATH` in `.env` to select a specific absolute directory.

## Features

- Registration, login, logout, profile/password updates, authenticator-based 2FA.
- Products with unique SKUs, aliases, fixed base units, and minimum stock thresholds.
- Separate receipt batches with source, expiry, on-hand and reserved quantities.
- Order availability preview, FEFO allocation, reservations, cancellation and fulfillment.
- Audited physical counts, disposal, quarantine/release, and stock movement history.
- Low-stock and expiration filters, plus inventory/order/batch/movement CSV/XLSX exports.

Quantities are whole numbers in each product's base unit; there is no unit conversion.
Locations, purchasing, demand forecasting and role-based permissions remain out of scope.
All registered users have the same operational access. No Agent or model training is included.
Public registration is intended for the course/demo workflow and should be reviewed
before public deployment.

## Existing installations

Stop the old app and back up its data. Do **not** run `init-db` before importing.
With a fresh instance directory:

```powershell
python -m flask --app acme_inventory import-legacy --database src/data/inventory.db --images src/static/img
```

Use absolute source paths when importing from another checkout. The command copies
the database and optional images, rewrites image URLs in the copy, and leaves the
originals untouched. It refuses to overwrite an existing destination database.
Users, password hashes and 2FA secrets are preserved. Current balances become opening
batches. Historical orders are retained as read-only `Legacy recorded` entries, with
their original status preserved; no historical stock is deducted a second time. Users must
log in again. See [development notes](docs/development.md).

## Structure

```text
src/acme_inventory/
  __init__.py       application factory
  config.py        runtime configuration
  extensions.py    shared Flask extensions
  cli.py           initialization, upgrade and legacy import
  migrations.py    versioned SQLite schema/data migration
  models/          database mappings
  routes/          HTTP endpoints and access checks
  services/        business operations and integrations
  templates/       feature folders and shared components
  static/          shared CSS, page JS modules, bundled images
tests/             isolated regression tests
docs/              architecture, data model, workflows and development
```

## Validation

```powershell
python -m pytest
python -m ruff check src/acme_inventory tests
python -m build
```

For development, enable debug explicitly with `flask run --debug`. The old
`src/app.py`, `server.ini`, TLS launcher and prototype routes are retired.
For deployment, use a production WSGI server with `acme_inventory:create_app()`,
terminate HTTPS at a reverse proxy, configure a stable `ACME_SECRET_KEY`, and
back up instance data. Do not disable the firewall to expose the app.

## Documentation

- [System overview and documentation navigation](docs/system-overview.md)

- [Architecture and naming](docs/architecture.md)
- [Data model and compatibility](docs/data-model.md)
- [Business workflows](docs/workflows.md)
- [Development and API changes](docs/development.md)

Licensed under the [MIT License](LICENSE.txt).
