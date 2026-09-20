# Data model and compatibility

The refactor preserves the original user, item and order tables and column types.

| Model | Python attribute | Database column |
| --- | --- | --- |
| User | avatar_url | pfp_url |
| User | joined_at | joindate |
| Item | category | type |
| Item | received_on | stockdate |
| Item | expires_on | expdate |
| Item | image_url | image |
| Order | ordered_on | orderdate |
| Order | delivered_on | deliverydate |

Other columns retain their names. JSON serializers use the new attribute names
and ISO dates. Order items still use the legacy `1x3,2x5` representation. Creation
aggregates duplicate products and validates the 255-character field limit.
Deletion explicitly protects references from orders because the old schema has
no foreign keys for order lines.

No schema migration is needed for these mappings. `init-db` creates missing tables
only. Introduce versioned migrations and conversion tests when adding order lines,
batches, or stock movements. Do not use create_all as a schema upgrade mechanism.

Known domain limits remain: no batches, locations, movement ledger, donor records,
reservations, or order-line snapshots. Receiving an existing item replaces its
dates; creating an order deducts stock immediately.

