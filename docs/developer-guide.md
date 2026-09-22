# Developer guide

ACME is a small food-bank inventory application: operators receive donations,
track dated batches, reserve supplies for recipients, and record distribution.
It is a modular Flask monolith with server-rendered pages, page-specific JavaScript,
and SQLite. This guide describes the implemented system, not a proposed redesign.
Documentation baseline: the batch-inventory release through `cd4aba2`.

## Read this first

| Reading order | Document | What you should understand afterwards |
| --- | --- | --- |
| 1 | [Architecture](architecture.md) | System boundary, running parts, module responsibilities and request flow |
| 2 | [Data model](data-model.md) | Product, batch, order and ledger relationships; authoritative balances |
| 3 | [Workflows](workflows.md) | Business flow, legal states, transactions and failure paths |
| 4 | [Development](development.md) | Local deployment, configuration, API entry points, tests and migration |

Each document contains editable Mermaid diagrams. Read them in a Markdown viewer
with Mermaid support (including GitHub); the fenced source remains readable in a
plain editor. Keep the diagrams with the code. PDF is an optional distribution
format, not a separately maintained source of truth.

## Run and inspect

Follow [README setup](../README.md#setup) for a fresh checkout. For an existing
database, stop the server and follow [migration and recovery](data-model.md#migration-and-recovery)
before starting this release. With the virtual environment activated:

```powershell
python -m flask --app acme_inventory run --port 5055
```

Open `http://127.0.0.1:5055`. The repository's Codex launch action uses this port;
plain `flask run` defaults to port 5000. Register an account in a fresh database.
There are no repository-shipped account credentials or sample inventory.

For a hands-on walkthrough in a disposable instance: create a product, receive two
batches with different expiry dates, preview an order, confirm it, and fulfill or
cancel it. Compare the on-hand, reserved and available columns, then inspect
Movements. Never use a working business database for destructive experiments.

## Where to change a feature

| Concern | Entry points | Useful regression tests |
| --- | --- | --- |
| Startup, sessions, CSRF | [factory](../src/acme_inventory/__init__.py), [configuration](../src/acme_inventory/config.py) | [authentication](../tests/test_auth.py), [structure](../tests/test_structure.py) |
| Products and receipts | [inventory service](../src/acme_inventory/services/inventory.py), [donation routes](../src/acme_inventory/routes/donations.py) | [inventory](../tests/test_inventory.py) |
| Batches, counts and movement ledger | [stock service](../src/acme_inventory/services/stock.py), [stock routes](../src/acme_inventory/routes/stock.py) | [stock workflows](../tests/test_stock_workflows.py) |
| Preview, reservation and fulfillment | [order service](../src/acme_inventory/services/orders.py), [order routes](../src/acme_inventory/routes/orders.py) | [orders](../tests/test_orders.py), [stock workflows](../tests/test_stock_workflows.py) |
| Dashboard and exports | [overview](../src/acme_inventory/services/overview.py), [reports](../src/acme_inventory/services/reports.py) | [overview tests](../tests/test_overview.py), [report tests](../tests/test_reports.py) |
| Schema and legacy compatibility | [models](../src/acme_inventory/models), [migration](../src/acme_inventory/migrations.py), [CLI](../src/acme_inventory/cli.py) | [legacy import](../tests/test_legacy.py) |
| UI and interaction | [templates](../src/acme_inventory/templates), [page scripts](../src/acme_inventory/static/js/pages), [shared CSS](../src/acme_inventory/static/css) | [page and asset checks](../tests/test_structure.py), browser walkthrough |

A typical feature change touches a route, a service, its template/page script, and
behavioral tests. Put balance rules in services rather than duplicating them in JS.
The browser may preview or filter; the server validates every write again.

## Rules that prevent inventory errors

- A product identifies a type of supply; a batch identifies one receipt of it.
- On-hand is physical stock. Reserved is committed to open orders. Available is
  eligible stock minus reservations, not simply the product's physical total.
- Creating an order reserves stock. Only fulfillment deducts physical stock.
- Order preview neither persists an order nor holds stock. Confirmation recalculates.
- FEFO means first expiry, first out; equal expiry dates are ordered by batch ID.
- Business dates use the server's local date; movement timestamps are stored as UTC.
- Stock writes and their ledger entries commit together. Never update just the
  compatibility `Item.quantity` field or bypass the stock services.
- `request_key` protects supported successful writes from replay. It is optional
  in the API, so clients must supply it to receive that protection.
- Legacy orders are read-only historical records, not live reservations.

## Current limits and extension points

All registered users have the same access. The application has no role model,
warehouse locations, fractional quantities, unit conversion, purchase orders,
shipping integration, background worker, Agent, or model-training pipeline.
Donors and recipients are recorded as text, not separate account/entity tables.
SQLite is the supported database; its writer-lock strategy is not a portable
concurrency solution for other engines. The movement ledger is append-only through
application workflows, not a tamper-proof audit store.

Future work should be explicitly labelled as proposed. For example, a future Agent
could reuse business services, but no Agent component belongs in the current diagrams.
Production infrastructure is not defined in this repository; the deployment diagram
shows local development only.

## Keeping the guide accurate

Update the owning document in the same change as a modified module, relationship,
state transition or deployment assumption. Use meaningful arrow labels and keep
static dependencies separate from runtime sequences. The ER diagram shows declared
relationships; consult models and migrations for full schema details. Add a short
architectural decision record when a substantial tradeoff changes (for example,
replacing SQLite), rather than expanding every diagram.
