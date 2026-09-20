export function textCell(value) {
  const cell = document.createElement('td');
  cell.textContent = value ?? '—';
  return cell;
}

export function matchesSearch(values, search) {
  const query = search.trim().toLocaleLowerCase();
  return values.some(value => String(value ?? '').toLocaleLowerCase().includes(query));
}

export function enableSorting(table) {
  table.querySelectorAll('th[data-column]').forEach(header => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = header.textContent;
    header.replaceChildren(button);
    button.addEventListener('click', () => {
      const ascending = header.getAttribute('aria-sort') !== 'ascending';
      table.querySelectorAll('th').forEach(th => th.removeAttribute('aria-sort'));
      header.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
      const index = Number(header.dataset.column);
      const rows = [...table.tBodies[0].rows];
      rows.sort((a, b) => a.cells[index].textContent.localeCompare(
        b.cells[index].textContent, undefined, { numeric: true }
      ) * (ascending ? 1 : -1));
      table.tBodies[0].append(...rows);
    });
  });
}

