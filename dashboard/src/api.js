// All backend access lives here. Nothing on screen is hard-coded: every value comes from a region API.
const DEFAULT = 'mum=http://127.0.0.1:8001,pun=http://127.0.0.1:8002'

export const REGIONS = (import.meta.env.VITE_REGIONS || DEFAULT)
  .split(',')
  .map((s) => s.trim().split('='))
  .map(([id, url]) => ({ id, url: url.replace(/\/$/, '') }))

const KEY = import.meta.env.VITE_API_KEY || 'dev-officer'
const H = { 'X-API-Key': KEY, 'Content-Type': 'application/json' }

async function call(url, opts = {}) {
  const ctl = new AbortController()
  const t = setTimeout(() => ctl.abort(), 1500)
  try {
    const r = await fetch(url, { ...opts, headers: H, signal: ctl.signal })
    const body = await r.json().catch(() => null)
    if (!r.ok) throw Object.assign(new Error(`HTTP ${r.status}`), { status: r.status, body })
    return body
  } finally {
    clearTimeout(t)
  }
}

// One poll of one region. An unreachable region is reported as {ok:false}, never thrown.
export async function pollRegion({ id, url }) {
  try {
    const [status, reports] = await Promise.all([call(`${url}/v1/status`), call(`${url}/v1/reports`)])
    return { id, url, ok: true, status, reports }
  } catch (e) {
    return { id, url, ok: false, error: String(e.message || e) }
  }
}

export const createReport = (r, body) => call(`${r.url}/v1/reports`, { method: 'POST', body: JSON.stringify(body) })
export const patchField = (r, id, field, value) =>
  call(`${r.url}/v1/reports/${id}`, { method: 'PATCH', body: JSON.stringify({ field, value }) })
export const addNote = (r, id, text) =>
  call(`${r.url}/v1/reports/${id}/notes`, { method: 'POST', body: JSON.stringify({ text }) })

// Cut or heal the pair: the switch must be set on BOTH regions (enforced in each backend).
export async function setPairLink(a, b, mode) {
  return Promise.allSettled([
    call(`${a.url}/admin/links/${b.id}`, { method: 'POST', body: JSON.stringify({ mode }) }),
    call(`${b.url}/admin/links/${a.id}`, { method: 'POST', body: JSON.stringify({ mode }) }),
  ])
}
