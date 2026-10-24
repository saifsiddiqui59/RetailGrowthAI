import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { derivePlatformAlerts } from './alert-signals.mjs'

// PlatformBoundary in App.jsx enforces database-verified root access before mounting.
export default function PlatformAlerts() {
  const { client } = useRetailAuth()
  const [items, setItems] = useState([])
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [reload, setReload] = useState(0)
  const [checkedAt, setCheckedAt] = useState(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setItems([])
    Promise.all([
      client.getPlatformSummary(),
      client.listPlatformOnboardingRequests('PENDING'),
      client.listPlatformShops(25, 0),
    ]).then(([summary, requests, listing]) => {
      if (!active) return
      setItems(derivePlatformAlerts({summary, requests, listing}))
      setCheckedAt(new Date())
    }).catch(() => {
      if (active) setError('Monitoring could not be verified. Alerts are unavailable, not zero. Check authorization and refresh.')
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [client, reload])

  const displayed = filter === 'all' ? items : items.filter(item => item.level === filter)
  const actions = items.filter(item => item.level === 'action').length
  return <section className="platform-alert-page" aria-label="Super Admin notification center">
    <div className="page-heading">
      <div><div className="eyebrow">PLATFORM CONTROL / MONITORING</div>
        <h1>Notifications &amp; alerts</h1>
        <p className="lead">A read-only action center for retailer approvals and subscription signals. Refresh to get the latest server snapshot.</p>
      </div>
      <button type="button" className="subtle-button" disabled={loading}
        onClick={() => setReload(n => n+1)}>Refresh alerts</button>
    </div>
    <div className="panel platform-alert-disclaimer">
      These are <strong>current monitoring signals</strong>, not a persistent message inbox.
      Automated email delivery, job failure alerts and cloud monitoring are not connected.
    </div>
    {loading && <p role="status">Checking verified platform signals…</p>}
    {error && <p role="alert" className="notice-error">{error}</p>}
    {!loading && !error && <>
      <div className="platform-alert-tally">
        <strong>{actions} approval or entitlement alerts</strong>
        <span>Checked {checkedAt?.toLocaleString('en-IN') || '—'} · snapshot, not realtime</span>
      </div>
      <div className="platform-alert-filters" role="group" aria-label="Filter alerts">
        {[
          ['all','All'], ['action','Action required'],
          ['attention','Upcoming'], ['info','Information'],
        ].map(([value,label]) => <button key={value} type="button"
          aria-pressed={filter===value} onClick={() => setFilter(value)}>{label}</button>)}
      </div>
      <div className="platform-alert-list">
        {!displayed.length && <p role="status">No alerts in this category in the latest snapshot.</p>}
        {displayed.map(item => <article className={'platform-alert-item alert-'+item.level} key={item.id}>
          <div className="platform-alert-indicator" aria-hidden="true">{item.level==='action' ? '!' : item.level==='attention' ? '◷' : 'i'}</div>
          <div className="platform-alert-body">
            <small>{item.category} · {item.level==='action' ? 'Action required' : item.level==='attention' ? 'Upcoming' : 'Information'}</small>
            <h2>{item.title}</h2><p>{item.detail}</p>
          </div>
          <Link className="text-link" to={item.destination}>{item.action} →</Link>
        </article>)}
      </div>
    </>}
  </section>
}
