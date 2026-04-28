const B = ''

export const analyzeText   = (content, filename='.gitlab-ci.yml') =>
  post('/analyze/', { content, filename })

export const analyzeFile   = file => {
  const fd = new FormData(); fd.append('file', file)
  return req('/analyze/upload', { method:'POST', body: fd })
}

export const getHistory    = (limit=50, offset=0) => req(`/history?limit=${limit}&offset=${offset}`)
export const getResult     = id  => req(`/result/${id}`)
export const deleteResult  = id  => req(`/result/${id}`, { method:'DELETE' })
export const getHealth     = ()  => req('/health')

async function post(url, body) {
  return req(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) })
}
async function req(url, opts={}) {
  const r = await fetch(B+url, opts)
  if (r.status === 204) return null
  const j = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(j.detail || `HTTP ${r.status}`)
  return j
}
