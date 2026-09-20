import { jsonRequest, showMessage } from '../common/api.js';

const form = document.getElementById('order-form');
const select = document.getElementById('order-item');
const quantityInput = document.getElementById('order-quantity');
const lines = new Map();

function renderLines() {
  const list = document.getElementById('order-lines');
  list.replaceChildren();
  for (const [id, line] of lines) {
    const row = document.createElement('li');
    const label = document.createElement('span');
    label.textContent = `${line.name} × ${line.quantity}`;
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'secondary';
    remove.textContent = 'Remove';
    remove.addEventListener('click', () => { lines.delete(id); renderLines(); });
    row.append(label, remove);
    list.append(row);
  }
}

document.getElementById('add-order-line').addEventListener('click', () => {
  const quantity = Number(quantityInput.value);
  if (!select.value || !Number.isInteger(quantity) || quantity < 1) {
    showMessage('Select a product and enter a positive whole quantity.', true);
    return;
  }
  const id = Number(select.value);
  const previous = lines.get(id);
  lines.set(id, { name: select.selectedOptions[0].textContent,
    quantity: quantity + (previous?.quantity || 0) });
  renderLines();
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  data.items = [...lines].map(([item_id, line]) => ({ item_id, quantity: line.quantity }));
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  try {
    await jsonRequest(form.action, { method: 'POST', body: JSON.stringify(data) });
    window.location.assign(form.dataset.success);
  } catch (error) { showMessage(error.message, true); submit.disabled = false; }
});
