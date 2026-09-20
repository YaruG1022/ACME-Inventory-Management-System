export async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content,
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });
  if (response.redirected) throw new Error('Your session expired. Log in again.');
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message || `Request failed (${response.status}). Reload and try again.`);
  }
  return response;
}

export async function jsonRequest(url, options = {}) {
  return (await request(url, options)).json();
}

export function showMessage(message, error = false) {
  const element = document.getElementById('page-message');
  element.textContent = message;
  element.hidden = false;
  element.classList.toggle('error', error);
}

