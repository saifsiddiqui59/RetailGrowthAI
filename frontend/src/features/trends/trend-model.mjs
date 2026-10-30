// Feature #2 presentation-only normalization. Authorization/data loading stays server owned.
const ALLOWED = {
  google_rss: ['trends.google.com', 'www.google.com'],
  youtube: ['www.youtube.com'],
  festival_calendar: ['gov.in'],
}
const nowDate = (now) => now instanceof Date ? now : new Date(now)

export function safeEvidence(url, source) {
  if (typeof url !== 'string' || url.length > 600) return null
  try {
    const u = new URL(url)
    const allowed = ALLOWED[source]
    if (!allowed || u.protocol !== 'https:' || u.username || u.password || u.port) return null
    const ok = source === 'festival_calendar'
      ? u.hostname === 'gov.in' || u.hostname.endsWith('.gov.in')
      : allowed.includes(u.hostname)
    return ok ? u.href : null
  } catch { return null }
}

export function filterRecommendations(rows, { category = 'all', language = 'all',
  freshness = 'active', city = '', now = new Date() } = {}) {
  const reference = nowDate(now)
  if (!Number.isFinite(reference.valueOf())) return []
  if (!Array.isArray(rows)) return []
  return rows.filter((row) => {
    if (!row || typeof row !== 'object' ||
      !safeEvidence(row.evidence_url, row.source) ||
      !/^[a-f0-9]{32}$/.test(row.trend_id || '')) return false
    const observed = new Date(row.observed_at)
    const expiry = new Date(row.expires_at)
    if (!Number.isFinite(observed.valueOf()) || !Number.isFinite(expiry.valueOf()) ||
      observed > new Date(reference.valueOf() + 5 * 60000)) return false
    if (category !== 'all' && row.category !== category) return false
    if (language !== 'all' && row.language !== language) return false
    if (city && (row.city || '').toLocaleLowerCase() !== city.toLocaleLowerCase()) return false
    return freshness === 'all' || (expiry > reference && reference - observed <= 48 * 3600000)
  }).sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 25)
}

export function sourceSummary(sources) {
  if (!Array.isArray(sources) || sources.length === 0) return 'Sources not configured or not loaded'
  const failed = sources.filter((s) => s?.status !== 'ok')
  return failed.length
    ? 'Incomplete sources: ' + failed.map((s) => s.source + ' (' + s.status + ')').join(', ')
    : 'All configured sources responded'
}
