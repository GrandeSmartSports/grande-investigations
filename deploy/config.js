const CONFIG = (() => {
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return { API: 'http://localhost:8000' };
  }
  // Production — update with Railway URL after deploy
  return { API: 'https://grande-investigations-api.up.railway.app' };
})();

async function api(path, opts = {}) {
  const pin = localStorage.getItem('gi_pin') || '1234';
  const res = await fetch(`${CONFIG.API}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      'x-pin': pin,
      ...(opts.headers || {}),
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 401) {
    localStorage.removeItem('gi_pin');
    location.reload();
    return;
  }
  return res.json();
}
