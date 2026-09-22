import { jsonRequest, showMessage } from '../common/api.js';
const dialog = document.getElementById('order-action-dialog');
const form = document.getElementById('order-action-form');
let orderId;
let action;
let key;
for (const button of document.querySelectorAll('.order-action')) {
  button.addEventListener('click', () => {
    form.reset();
    orderId = button.dataset.id;
    action = button.dataset.action;
    key = crypto.randomUUID();
    document.getElementById('action-title').textContent = `${action === 'fulfill' ? 'Fulfill' : 'Cancel'} order #${orderId}`;
    document.getElementById('delivery-field').hidden = action !== 'fulfill';
    form.elements.delivered_on.disabled = action !== 'fulfill';
    dialog.showModal();
  });
}
form.addEventListener('input', () => { key = crypto.randomUUID(); });
document.getElementById('close-order-action').addEventListener('click', () => dialog.close());
form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('[type="submit"]');
  button.disabled = true;
  try {
    await jsonRequest(`/api/orders/${orderId}/transition`, {method: 'POST', body: JSON.stringify({
      ...Object.fromEntries(new FormData(form)), action, request_key: key,
    })});
    location.reload();
  } catch (error) { dialog.close(); showMessage(error.message, true); }
  finally { button.disabled = false; }
});
