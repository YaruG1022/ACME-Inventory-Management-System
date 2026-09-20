import { jsonRequest, showMessage } from '../common/api.js';
import { enableSorting, matchesSearch, textCell } from '../common/table.js';

const page = document.getElementById('inventory-page');
const table = document.getElementById('inventory-table');
const form = document.getElementById('item-form');
const dialog = document.getElementById('item-dialog');
const search = document.getElementById('inventory-search');
const editButton = document.getElementById('edit-item');
const deleteButton = document.getElementById('delete-items');
let items = [];

function selectedIds() {
  return [...table.querySelectorAll('input:checked')].map(input => Number(input.value));
}

function updateButtons() {
  const count = selectedIds().length;
  editButton.disabled = count !== 1;
  deleteButton.disabled = count === 0;
}

function render() {
  const body = table.tBodies[0];
  body.replaceChildren();
  const visible = items.filter(item => matchesSearch(Object.values(item), search.value));
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
    for (const key of ['id', 'name', 'category', 'quantity', 'received_on', 'expires_on']) {
      row.append(textCell(item[key]));
    }
    body.append(row);
  }
  table.querySelectorAll('th').forEach(th => th.removeAttribute('aria-sort'));
  document.getElementById('inventory-empty').hidden = visible.length > 0;
  updateButtons();
}

async function load() {
  items = await jsonRequest(page.dataset.api);
  render();
}

function openForm(item = {}) {
  form.reset();
  for (const key of ['id', 'name', 'category', 'quantity', 'received_on', 'expires_on']) {
    if (item[key] !== undefined) form.elements.namedItem(key).value = item[key];
  }
  document.getElementById('item-form-title').textContent = item.id ? 'Edit item' : 'Add item';
  document.getElementById('item-error').hidden = true;
  dialog.showModal();
}

document.getElementById('add-item').addEventListener('click', () => openForm());
editButton.addEventListener('click', () => openForm(items.find(item => item.id === selectedIds()[0])));
document.getElementById('close-item').addEventListener('click', () => dialog.close());
search.addEventListener('input', render);

form.addEventListener('submit', async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  const id = data.id;
  delete data.id;
  const button = form.querySelector('button');
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

