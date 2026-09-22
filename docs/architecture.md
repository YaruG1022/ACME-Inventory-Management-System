# Architecture and naming

The application is a modular Flask monolith. `create_app` loads configuration,
binds shared extensions, and registers routes and CLI commands. Importing the
package does not create database tables or start a server.

Request flow: route → service → model/database. Routes handle HTTP input and access
checks. Services validate business rules and own commit/rollback boundaries.
Models describe persisted data and serialization; they do not commit transactions.
Stock mutations acquire a SQLite writer lock before reading balances. Batch
changes, reservations, normalized order lines and movement history commit together.
The services/stock.py module owns shared stock summaries and transaction helpers.
Versioned schema and data upgrades live in migrations.py.

Python files/functions/fields use snake_case, classes use PascalCase, constants
use UPPER_SNAKE_CASE. JavaScript functions use camelCase and CSS uses kebab-case.
Dates use `_on`, timestamps use `_at`; API fields match model vocabulary.

Templates are organized by feature. `base.html` loads common CSS, while each page
loads its own ES module. Request, notification, search and sorting helpers live
under `static/js/common`. Navigation is rendered by Jinja; user content is escaped
by templates or inserted using DOM textContent rather than HTML concatenation.

Default images are versioned in static/images. User uploads use UPLOAD_DIR and an
authenticated serving route; databases/secrets live outside the application package.
There is no frontend build step or external CDN dependency.

Do not create empty services, migration directories, or repository abstractions
before they have a concrete responsibility. Add domain modules as features grow.


## Interface

The workspace uses a persistent desktop sidebar and a compact mobile navigation
 grid, a shared page header, reusable metric cards, and consistent forms and tables.
The authenticated overview shows real product counts, batch expiration alerts, category
mix, and recent orders; the public home page does not expose inventory information.

Inventory filters combine product search, category, and stock status. “Expiring
soon” means stock on hand with an expiration date from today through seven days
from today, inclusive. “Expired” excludes products with zero quantity. “In stock”
in the inventory filter means positive eligible unreserved stock. Physical on-hand
and reserved amounts are shown separately. Status is communicated with text as well as color. Overview cards link to
corresponding inventory filters. No sample records are added to the user's database.

Shared colors and layout live in static/css/base.css; components and responsive
rules live in static/css/components.css. Inline SVG icons are defined in the Jinja
icons macro, with no external icon or font dependency. Forms retain visible labels,
keyboard focus states, and a skip-to-content link. Wide tables scroll within their
own container on small screens.
