# Current workflows

## Accounts

Register → login → optionally set up an authenticator. Two-factor login completes
only after code verification. Password changes require the current password.
Logout and all other mutations require a session CSRF token.

## Inventory and donations

Create/edit items from Inventory or receive donations into new/existing items.
Server validation covers name, category, whole quantities and dates. Editing
allows zero quantity; donations/orders require positive quantities. Failed edits
keep the dialog open with an error. Items referenced by orders cannot be deleted.
Image uploads are validated by content and receive random filenames.

## Orders

Select items/quantities → enter recipient/date → create. Duplicate products are
aggregated; any missing or insufficient item rolls back all deductions and the
order. The list shows confirmed orders with quantities. Decorative confirmation,
cancellation and delivery buttons were removed because those flows did not exist.

## Reports

Select Inventory/Orders → preview/search/sort → export CSV/XLSX. Search affects the
preview only; exports include the full report. Empty reports retain headers.
CSV formula prefixes are escaped and XLSX automatic formula/URL detection is off.

