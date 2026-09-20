# ACME Food Bank Inventory Tracking System

A Flask application for tracking donated food and hygiene products, recipient
orders, and inventory reports. Originally created for WSU SU21 CPTS 322.

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

Imports do not create database tables. `init-db` creates missing tables without
clearing existing ones; it is not a schema migration command. Local data, secrets,
and uploads live in Flask's instance directory, outside the application package.
Set `ACME_INSTANCE_PATH` in `.env` to select a specific absolute directory.

## Features

- Registration, login, logout, profile/password updates, authenticator-based 2FA.
- Inventory listing, filtering, sorting, creating, editing, and protected deletion.
- Receiving donations into new/existing items, with optional image uploads.
- Recipient orders with atomic stock deductions and validation.
- Inventory/order report previews and CSV/XLSX exports.

Each item still has a single balance and expiration date; replenishment updates
its dates. Batches, locations, reservations, cancellation workflows, and role-based
permissions are future work. All registered users have the same operational access.
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
Users, password hashes, 2FA secrets, items, and orders remain compatible. Users must
log in again. See [development notes](docs/development.md).

## Structure

```text
src/acme_inventory/
  __init__.py       application factory
  config.py        runtime configuration
  extensions.py    shared Flask extensions
  cli.py           initialization and legacy import
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

- [Architecture and naming](docs/architecture.md)
- [Data model and compatibility](docs/data-model.md)
- [Business workflows](docs/workflows.md)
- [Development and API changes](docs/development.md)

Licensed under the [MIT License](LICENSE.txt).
