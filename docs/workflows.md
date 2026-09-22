# Business workflows

## Products and units

Inventory -> Add item creates a product with no stock. Set a unique SKU (or let the
system generate one), name, Food/Hygiene category, aliases, base unit and minimum
available stock. Search supports name, SKU, alias and numeric ID. Edit selected changes
product metadata. Product names link to that product's batches. Use a fixed base unit
such as bag or carton; all quantities are whole numbers and are not converted.

## Receipts and batches

Donations -> choose an existing product or define a new one -> enter quantity,
receipt/expiry dates, optional batch code and donor/source -> Receive donation.
Each receipt creates a separate lot. It never overwrites another lot's dates.
Receipt date cannot be future; expiry cannot precede receipt. Expired receipts are
recorded but excluded from available stock. Same-product batch codes cannot repeat.

## Orders

Orders -> Create order -> select products and quantities -> enter recipient,
address, order date and scheduled distribution date -> Check availability.
The preview shows eligible balances, shortages and proposed earliest-expiry-first
batch allocations without changing inventory. Confirmation revalidates the plan.

Confirm & reserve creates normalized order lines and reservations in one transaction.
It leaves physical on-hand balances unchanged and reduces availability. Insufficient
stock for any line rejects the whole order. Duplicate product lines are aggregated.
The scheduled date must be today or later and cannot precede the order date.

A Reserved order has two actions:
- Fulfill: enter actual delivery date and reference/reason. Eligible reserved stock
  is deducted from physical balances, reservations are released, status is Fulfilled.
- Cancel order: enter a reason. Reservations are released without physical deductions;
  status is Cancelled.

Completed/cancelled orders cannot transition again. Fulfillment rechecks expiry and
batch status. If a reserved batch has expired, cancel and recreate the order with
eligible stock. Fulfillment dates cannot be future, before the order, or before
receipt. Historical migrated orders are read-only and never deduct stock again.

## Physical counts and disposal

Batches & stock -> Manage -> select an operation and enter a reason:
- Physical count sets the batch's total on-hand quantity to what was counted.
- Dispose / write off removes the specified quantity and records why.
- Quarantine blocks a batch from new orders; Release quarantine makes it eligible
  again if its dates are valid.

Counts cannot fall below reserved quantities. Disposal cannot consume reserved
stock. Quarantine changes require reservations to be cancelled first. If physical
stock changed since a count form was opened, the count is rejected; reload and count
again. Stock movements lists every physical/reserved change, resulting balance,
operator, reason and associated order. Filter by product or movement type.

## Low-stock and expiration review

Set minimum stock on products. Inventory -> Below minimum stock uses eligible,
unreserved availability. The overview links to low-stock products and expiry alerts.
Batches & stock filters by product, category, quarantine, expired stock, or expiry
within N days (inclusive, maximum 3650). Expiry views exclude zero-quantity batches.
Use quarantine or disposal to record the disposition of problem stock.

## Accounts and reports

Accounts retain registration, login, password changes and optional authenticator 2FA.
All registered users have the same operational access. All writes require CSRF.
Reports offers Inventory, Orders, Stock batches and Stock movements previews and
CSV/XLSX exports. Preview search does not restrict export. Spreadsheet formula
prefixes are escaped; empty reports retain headers.
