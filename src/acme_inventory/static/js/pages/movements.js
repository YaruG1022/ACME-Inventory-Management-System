import { jsonRequest, showMessage } from '../common/api.js';
import { textCell } from '../common/table.js';
const filters = document.getElementById('movement-filters');
filters.elements.item_id.value = new URLSearchParams(location.search).get('item_id') || '';
async function load() {
  const params = new URLSearchParams(new FormData(filters));
  const rows = await jsonRequest(`/api/movements?${params}`);
  const body = document.querySelector('#movement-table tbody');
  body.replaceChildren();
  for (const movement of rows) {
    const row = document.createElement('tr');
    const signed = value => value > 0 ? `+${value}` : String(value);
    for (const value of [movement.created_at.replace('T', ' ').replace('Z', ''),
      `${movement.sku} · ${movement.name} / ${movement.batch}`, movement.kind,
      `${signed(movement.delta)} ${movement.unit}`, signed(movement.reserved_delta),
      `${movement.balance} / ${movement.reserved_balance}`, movement.reason,
      `${movement.actor}${movement.order_id ? ` / #${movement.order_id}` : ''}`]) row.append(textCell(value));
    body.append(row);
  }
  document.getElementById('movement-empty').hidden = rows.length > 0;
  document.getElementById('movement-count').textContent = `${rows.length} movements`;
}
filters.addEventListener('submit', event => { event.preventDefault(); load().catch(e => showMessage(e.message, true)); });
load().catch(e => showMessage(e.message, true));
