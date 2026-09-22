import { jsonRequest, showMessage } from '../common/api.js';

const form = document.getElementById('order-form');
const select = document.getElementById('order-item');
const quantityInput = document.getElementById('order-quantity');
const lines = new Map();
let requestKey = crypto.randomUUID();
form.addEventListener("input", () => { requestKey = crypto.randomUUID(); document.getElementById("order-preview").hidden = true; });

function renderLines() {
  requestKey = crypto.randomUUID();
  document.getElementById("order-preview").hidden = true;
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
  data.request_key = requestKey;
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  try {
    await jsonRequest(form.action, { method: 'POST', body: JSON.stringify(data) });
    window.location.assign(form.dataset.success);
  } catch (error) { showMessage(error.message, true); submit.disabled = false; }
});

document.getElementById('preview-order').addEventListener('click', async () => {
  if (!form.reportValidity()) return;
  const button = document.getElementById('preview-order');
  button.disabled = true;
  const data = Object.fromEntries(new FormData(form));
  data.items = [...lines].map(([item_id, line]) => ({item_id, quantity: line.quantity}));
  try {
    const plan = await jsonRequest('/api/orders/preview', {method: 'POST', body: JSON.stringify(data)});
    const preview = document.getElementById('order-preview');
    preview.replaceChildren();
    const heading = document.createElement('strong');
    heading.textContent = plan.can_fulfill ? 'All items can be reserved.' : 'Some items need more stock.';
    preview.append(heading);
    for (const line of plan.lines) {
      const row = document.createElement('p');
      row.textContent = `${line.name}: ${line.quantity} ${line.unit} requested, ${line.available} eligible, ${line.shortage} short. ` + line.allocations.map(a => `${a.code}: ${a.quantity}`).join('; ');
      preview.append(row);
    }
    preview.hidden = false;
    preview.classList.toggle('error', !plan.can_fulfill);
  } catch (error) { showMessage(error.message, true); }
  finally { button.disabled = false; }
});
