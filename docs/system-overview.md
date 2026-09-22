# ACME Inventory System Overview

**English** | [简体中文](system-overview.zh-CN.md)

ACME supports food-bank operations from receiving donated supplies to distributing
them to recipients. It tracks stock by batch, reserves supplies for orders, and
records stock changes so the team can understand both current balances and their history.

This overview introduces the system's purpose, business concepts, structure and
operating context. It is intended for operators, project stakeholders, testers,
developers and maintainers. Detailed procedures, code references and configuration
instructions live in the linked topic documents.

The content describes the implemented system. The business and architecture baseline
is the batch-inventory release through `cd4aba2`; later documentation changes clarify
that baseline without adding application capabilities.

## Purpose and scope

Food-bank operators can maintain product records, receive donations, inspect batch
expiry dates, reserve and distribute supplies, record counts or losses, and export
reports. The overview dashboard highlights stock that needs attention.

Donors supply goods and recipients receive them, but neither has a dedicated portal
or login role. Their details are entered by operators. All registered users currently
have the same operational access. The application covers inventory and distribution;
purchasing, payments and shipment tracking are outside its present scope.

## Core business concepts

| Concept | Meaning |
| --- | --- |
| Product | A type of supply identified by a SKU, with a name, aliases, category and base unit |
| Batch | One receipt of a product, with its own source, receipt date and expiry date |
| On-hand stock | The physical quantity recorded in inventory, including stock that cannot currently be issued |
| Reserved stock | The quantity committed to an open recipient order |
| Available stock | Eligible on-hand stock minus reservations; expired or quarantined stock is excluded |
| Order | A recipient's requested products and quantities, with a scheduled distribution date |
| Stock movement | A record of a receipt, reservation, distribution, count, disposal or batch-status change |

Quantities are whole numbers in each product's base unit, such as bags or cartons.
There is no automatic unit conversion. For a worked balance example and entity
relationships, see the [data model](data-model.md).

## Main business workflows

| Task | Main path | Effect on inventory |
| --- | --- | --- |
| Receive supplies | Select or create product, then record a dated batch in Donations | Adds physical stock while preserving earlier batches |
| Plan distribution | Select products and recipient details, then preview availability | Shows a proposed allocation without reserving stock |
| Confirm an order | Recheck availability and reserve eligible batches | Increases reserved stock; physical stock stays unchanged |
| Fulfill an order | Validate reserved batches and record distribution | Decreases physical stock and releases its reservation |
| Cancel an order | Cancel a reserved order with a reason | Releases reservations without deducting physical stock |
| Correct or restrict stock | Record a physical count, disposal, quarantine or release | Updates balances or eligibility and records the reason |
| Review stock | Inspect minimum-stock and expiry alerts, movement history and reports | Provides information without changing balances |

Orders use the batches that expire first, known as FEFO (first expiry, first out).
Confirmation checks availability again because a preview does not hold stock.
Expired stock is excluded from distribution; historical migrated orders remain
read-only rather than creating new reservations or deductions.

The [workflow guide](workflows.md) contains operation details, business-flow and
state diagrams. Its sequence diagrams explain how the software handles successful
operations and failures. A failed stock transaction leaves no partial balance changes.

## System composition

The application has four main parts:

- A browser interface for inventory, donations, orders, movements and reports.
- A Flask application that serves pages, handles requests and applies business rules.
- A SQLite database containing accounts, products, batches, orders and movement records.
- Local file storage for uploaded images and runtime configuration material.

The application is delivered as one modular Python application, rather than a set
of independently deployed services. Pages and JavaScript are served by the same
application. See [architecture](architecture.md) for system context, running parts,
module responsibilities and page navigation; see the [ER diagram](data-model.md#entity-relationships)
for database relationships.

## Operation and maintenance overview

Users access the application through a browser. The repository's local launch action
uses `http://127.0.0.1:5055`; a plain Flask launch defaults to port 5000. These addresses
refer to the machine running the application, not a hosted public service.

Setup instructions are in the [README](../README.md#setup). The application does not
ship account credentials or sample stock. For a fresh database, registration creates
an account. Existing installations require the documented upgrade procedure.

Configuration determines the database and upload locations. By default they reside
in Flask's private instance directory; in the editable source layout this is normally
`src/instance`. Database upgrades create a backup before changing an existing database.
Account information, uploads, secrets and backups are operational data and must be
managed separately from the source repository.

Read [configuration and local deployment](development.md#configuration) for settings
and [migration and recovery](data-model.md#migration-and-recovery) before an upgrade
or restoration. Reverting a code commit does not restore database contents.

## Current limits and design choices

| Area | Current behavior and implication |
| --- | --- |
| Access | Every registered user has the same operational permissions; there is no role-based approval workflow |
| Inventory scope | No warehouse locations, fractional quantities or unit conversion; product units are fixed after stock history exists |
| Business integrations | Donors and recipients are text records, not separate account/entity tables; no purchasing or shipping integration |
| Consistency | Stock updates and their movements commit together; SQLite serializes stock writers before balance calculations |
| Audit history | Workflows append movement records, but the database is not a tamper-proof audit store |
| Runtime | Local deployment is documented; production infrastructure is not provisioned in this repository |
| Automation | No Agent, model training or background-worker pipeline is implemented |

Business dates follow the server's local date, while movement timestamps use UTC.
Changing database engines requires review of migrations and concurrency controls.
Future capabilities should be labelled as proposed rather than included in diagrams
of the current system.

## Documentation by task

| What you need to do | Start here |
| --- | --- |
| Understand capabilities, terminology and limits | This system overview |
| Operate receipts, orders, counts and stock reviews | [Business workflows](workflows.md) |
| Understand boundaries, components and page navigation | [Architecture](architecture.md) |
| Understand records, relationships and balance rules | [Data model](data-model.md) |
| Install or start a local instance | [README setup](../README.md#setup), [run and inspect](development.md#run-and-inspect) |
| Configure, upgrade or restore an instance | [Development and migration](development.md), [recovery guidance](data-model.md#migration-and-recovery) |
| Locate code, modify a feature or investigate behavior | [Code map](development.md#where-to-change-a-feature) |
| Validate a change or plan regression testing | [Development verification](development.md#verifying-a-development-change), [workflow sequences](workflows.md) |

Markdown is the maintained source, with Mermaid diagrams embedded in the topic
documents. Use a Mermaid-capable viewer such as GitHub to view diagrams. PDF may be
exported for sharing, but is not a second source to maintain independently.
