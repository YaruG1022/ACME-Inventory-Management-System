const select = document.getElementById('donation-item');
const fields = document.getElementById('new-product');
function updateFields() {
  fields.disabled = Boolean(select.value);
  fields.hidden = Boolean(select.value);
}
select.addEventListener('change', updateFields);
updateFields();

