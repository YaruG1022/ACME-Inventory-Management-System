import { jsonRequest, showMessage } from '../common/api.js';
import { textCell } from '../common/table.js';
const filters = document.getElementById('batch-filters');
const form = document.getElementById('batch-form');
const dialog = document.getElementById('batch-dialog');
let selected;
let key;
const initial = new URLSearchParams(location.search);
filters.elements.item_id.value = initial.get('item_id') || '';
if (['expiring', 'expired', 'quarantine'].includes(initial.get('view'))) filters.elements.view.value = initial.get('view');
function fields() {
  const count = form.elements.action.value === 'count';
  const disposal = form.elements.action.value === 'dispose';
  document.getElementById('count-field').hidden = !count;
  document.getElementById('dispose-field').hidden = !disposal;
  form.elements.counted_quantity.required = count;
  form.elements.counted_quantity.disabled = !count;
  form.elements.quantity.required = disposal;
  form.elements.quantity.disabled = !disposal;
}
form.elements.action.addEventListener('change', fields);
form.addEventListener('input', () => { key = crypto.randomUUID(); });
function manage(batch) {
  selected = batch;
  key = crypto.randomUUID();
  form.reset();
  form.elements.counted_quantity.value = batch.quantity;
  document.getElementById('batch-title').textContent = batch.code;
  document.getElementById('batch-context').textContent = `${batch.name} · ${batch.quantity} ${batch.unit} on hand · ${batch.reserved} reserved`;
  document.getElementById('batch-error').hidden = true;
  fields();
  dialog.showModal();
}
async function load() {
  const params = new URLSearchParams();
  const data = Object.fromEntries(new FormData(filters));
  if (data.item_id) params.set('item_id', data.item_id);
  if (data.category) params.set('category', data.category);
  if (data.view === 'expiring') params.set('days', data.days);
  if (data.view === 'expired') params.set('expired', '1');
  let batches = await jsonRequest(`/api/batches?${params}`);
  if (data.view === 'quarantine') batches = batches.filter(b => b.status === 'Quarantined');
  const body = document.querySelector('#batch-table tbody');
  body.replaceChildren();
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  for (const batch of batches) {
    const row = document.createElement('tr');
    const expired = batch.expires_on < today;
    const available = !expired && batch.status === 'Available' && batch.received_on <= today ? batch.quantity - batch.reserved : 0;
    for (const value of [`${batch.sku} · ${batch.name} / ${batch.code}`, batch.source,
      `${batch.quantity} ${batch.unit}`, batch.reserved, available, batch.received_on, batch.expires_on,
      expired ? `Expired · ${batch.status}` : batch.status]) row.append(textCell(value));
    const actions = document.createElement('td');
    const button = document.createElement('button');
    button.className = 'secondary';
    button.textContent = 'Manage';
    button.addEventListener('click', () => manage(batch));
    actions.append(button);
    row.append(actions);
    body.append(row);
  }
  document.getElementById('batch-empty').hidden = batches.length > 0;
  document.getElementById('batch-count').textContent = `${batches.length} batches`;
}
filters.addEventListener('submit', event => { event.preventDefault(); load().catch(e => showMessage(e.message, true)); });
document.getElementById('close-batch').addEventListener('click', () => dialog.close());
form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('[type="submit"]');
  button.disabled = true;
  try {
    const data = {...Object.fromEntries(new FormData(form)), expected_quantity: selected.quantity, request_key: key};
    await jsonRequest(`/api/batches/${selected.id}/adjust`, {method: 'POST', body: JSON.stringify(data)});
    dialog.close();
    await load();
    showMessage('Stock change recorded in the movement history.');
  } catch (error) {
    const message = document.getElementById('batch-error');
    message.textContent = error.message;
    message.hidden = false;
  } finally { button.disabled = false; }
});
load().catch(e => showMessage(e.message, true));
