# Architecture and naming

The application is a modular Flask monolith. `create_app` loads configuration,
binds shared extensions, and registers routes and CLI commands. Importing the
package does not create database tables or start a server.

Request flow: route → service → model/database. Routes handle HTTP input and access
checks. Services validate business rules and own commit/rollback boundaries.
Models describe persisted data and serialization; they do not commit transactions.
Order creation and all stock deductions commit together, using conditional SQL
updates to prevent stale-balance deductions.

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

