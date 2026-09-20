import { jsonRequest, request, showMessage } from '../common/api.js';
import { enableSorting, matchesSearch, textCell } from '../common/table.js';

const page = document.getElementById('reports-page');
const table = document.getElementById('report-table');
const type = document.getElementById('report-type');
const search = document.getElementById('report-search');
let report = { columns: [], data: [] };
let latestRequest = 0;

function render() {
  const head = document.createElement('tr');
  for (const [index, column] of report.columns.entries()) {
    const th = document.createElement('th');
    th.textContent = column.replaceAll('_', ' ').replace(/^./, letter => letter.toUpperCase());
    th.dataset.column = index;
    head.append(th);
  }
  table.tHead.replaceChildren(head);
  table.tBodies[0].replaceChildren();
  const visible = report.data.filter(row => matchesSearch(Object.values(row), search.value));
  for (const record of visible) {
    const row = document.createElement('tr');
    for (const column of report.columns) row.append(textCell(record[column]));
    table.tBodies[0].append(row);
  }
  document.getElementById('report-empty').hidden = visible.length > 0;
  enableSorting(table);
}

async function load() {
  const currentRequest = ++latestRequest;
  try {
    const result = await jsonRequest(`${page.dataset.api}?report_type=${encodeURIComponent(type.value)}`);
    if (currentRequest !== latestRequest) return;
    report = result;
    render();
  } catch (error) { showMessage(error.message, true); }
}

type.addEventListener('change', load);
search.addEventListener('input', render);
document.getElementById('export-report').addEventListener('click', async event => {
  const button = event.currentTarget;
  button.disabled = true;
  const format = document.getElementById('report-format').value;
  try {
    const response = await request(page.dataset.export, {
      method: 'POST', body: JSON.stringify({ report_type: type.value, format }),
    });
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = `report.${format}`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) { showMessage(error.message, true); }
  finally { button.disabled = false; }
});
load();
