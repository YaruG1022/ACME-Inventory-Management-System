import { jsonRequest, showMessage } from '../common/api.js';
import { enableSorting, matchesSearch, textCell } from '../common/table.js';

const page = document.getElementById('inventory-page');
const table = document.getElementById('inventory-table');
const form = document.getElementById('item-form');
const dialog = document.getElementById('item-dialog');
const search = document.getElementById('inventory-search');
const editButton = document.getElementById('edit-item');
const deleteButton = document.getElementById('delete-items');
const category = document.getElementById('inventory-category');
const status = document.getElementById('inventory-status');
const requestedStatus = new URLSearchParams(window.location.search).get('status');
if ([...status.options].some(option => option.value === requestedStatus)) status.value = requestedStatus;
let items = [];

function stockStatus(item) {
  if (item.expired > 0) return { key: 'expired', label: 'Expired stock', style: 'danger-badge' };
  if (item.expiring > 0) return { key: 'expiring', label: 'Expiring soon', style: 'warning' };
  if (item.available === 0) return { key: 'out', label: 'Unavailable', style: 'neutral' };
  if (item.low_stock) return { key: 'low', label: 'Below minimum', style: 'warning' };
  return { key: 'available', label: 'Available', style: '' };
}

function selectedIds() {
  return [...table.querySelectorAll('input:checked')].map(input => Number(input.value));
}

function updateButtons() {
  const count = selectedIds().length;
  editButton.disabled = count !== 1;
  deleteButton.disabled = count === 0;
  document.getElementById('selection-count').textContent = count
    ? `${count} product${count === 1 ? '' : 's'} selected` : 'Select a product to manage it';
}

function render() {
  const body = table.tBodies[0];
  body.replaceChildren();
  const visible = items.filter(item =>
    matchesSearch([item.id, item.sku, item.aliases, item.name, item.category], search.value)
    && (!category.value || item.category === category.value)
    && (!status.value || ({available: item.available > 0, out: item.available === 0, low: item.low_stock, expired: item.expired > 0, expiring: item.expiring > 0}[status.value]))
  );
  for (const item of visible) {
    const row = document.createElement('tr');
    const selection = document.createElement('td');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = item.id;
    checkbox.setAttribute('aria-label', `Select ${item.name}`);
    checkbox.addEventListener('change', updateButtons);
    selection.append(checkbox);
    const imageCell = document.createElement('td');
    const image = document.createElement('img');
    image.src = item.image_url || '/static/images/placeholder.svg';
    image.alt = '';
    imageCell.append(image);
    row.append(selection, imageCell);
    for (const key of ['sku', 'name', 'category', 'on_hand', 'reserved', 'available', 'unit']) {
      const cell = textCell(item[key]);
      if (['on_hand', 'reserved', 'available'].includes(key)) cell.className = 'numeric';
      if (key === 'id') { cell.className = 'reference'; cell.textContent = `#${String(item.id).padStart(4, '0')}`; }
      if (key === 'name') { const name = document.createElement('a'); name.textContent = item.name; name.href = `/stock?item_id=${item.id}`; cell.replaceChildren(name); }
      if (key === 'unit') cell.textContent = `${item.unit} / ${item.minimum_stock}`;
      if (key === 'category') {
        const tag = document.createElement('span');
        tag.className = `category-tag ${item.category === 'Hygiene' ? 'hygiene' : ''}`;
        tag.textContent = item.category;
        cell.replaceChildren(tag);
      }
      row.append(cell);
    }
    const state = stockStatus(item);
    const stateCell = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = `badge ${state.style}`;
    badge.textContent = state.label;
    stateCell.append(badge);
    row.append(stateCell);
    body.append(row);
  }
  table.querySelectorAll('th').forEach(th => th.removeAttribute('aria-sort'));
  document.getElementById('inventory-empty').hidden = visible.length > 0;
  document.getElementById('inventory-count').textContent = `${visible.length} of ${items.length} products`;
  const counts = { total: items.length, available: items.filter(item => item.available > 0).length,
    expiring: items.filter(item => item.expiring > 0).length,
    out: items.filter(item => item.available === 0).length };
  for (const [key, value] of Object.entries(counts)) document.getElementById(`count-${key}`).textContent = value;
  updateButtons();
}

async function load() {
  items = await jsonRequest(page.dataset.api);
  render();
}

function openForm(item = {}) {
  form.reset();
  for (const key of ['id', 'name', 'sku', 'category', 'unit', 'minimum_stock', 'aliases']) {
    if (item[key] !== undefined) form.elements.namedItem(key).value = item[key];
  }
  document.getElementById('item-form-title').textContent = item.id ? 'Edit item' : 'Add item';
  document.getElementById('item-error').hidden = true;
  form.dataset.requestKey = crypto.randomUUID();
  dialog.showModal();
}

document.getElementById('add-item').addEventListener('click', () => openForm());
editButton.addEventListener('click', () => openForm(items.find(item => item.id === selectedIds()[0])));
document.getElementById('close-item').addEventListener('click', () => dialog.close());
search.addEventListener('input', render);
category.addEventListener('change', render);
status.addEventListener('change', render);
document.getElementById('clear-filters').addEventListener('click', () => {
  search.value = ''; category.value = ''; status.value = ''; render();
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  const id = data.id;
  delete data.id;
  if (!id) data.request_key = form.dataset.requestKey;
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    await jsonRequest(id ? `${page.dataset.api}/${id}` : page.dataset.api, {
      method: id ? 'PUT' : 'POST', body: JSON.stringify(data),
    });
    dialog.close();
    await load();
    showMessage('Inventory saved.');
  } catch (error) {
    const message = document.getElementById('item-error');
    message.textContent = error.message;
    message.hidden = false;
    showMessage(error.message, true);
  } finally { button.disabled = false; }
});

deleteButton.addEventListener('click', async () => {
  const ids = selectedIds();
  if (!window.confirm(`Delete ${ids.length} selected item(s)?`)) return;
  deleteButton.disabled = true;
  try {
    await jsonRequest(page.dataset.delete, { method: 'POST', body: JSON.stringify({ ids }) });
    await load();
    showMessage('Items deleted.');
  } catch (error) { showMessage(error.message, true); }
  finally { updateButtons(); }
});

table.querySelectorAll('th').forEach((th, index) => {
  if (index >= 2) th.dataset.column = index;
});
enableSorting(table);
load().catch(error => showMessage(error.message, true));
