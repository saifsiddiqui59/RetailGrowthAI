import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import './platform-operations.css'

const CATEGORIES = [
  ['all','All'],['onboarding','Onboarding'],['subscription','Subscriptions'],
  ['job','Failed jobs'],['queue','Queue health'],
]
const VIEWS = [['active','Active'],['unread','Unread'],['history','History']]
const PAGE_SIZE = 40

// Server owns all alert categories and read state. No localStorage, fake
// Azure health, browser service key or unauthenticated React-only checks.
export default function PlatformAlerts() {
  const { client } = useRetailAuth()
  const [view,setView] = useState('active')
  const [category,setCategory] = useState('all')
  const [offset,setOffset] = useState(0)
  const [version,setVersion] = useState(0)
  const [loading,setLoading] = useState(true)
  const [working,setWorking] = useState(null)
  const [error,setError] = useState('')
  const [data,setData] = useState(null)

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError('')
    setData(null)
    client.listPlatformNotifications(view,category,PAGE_SIZE,offset)
      .then(next => {if(alive) setData(next)})
      .catch(() => {if(alive) setError('Platform notifications could not be verified. Check the database migration and your root authorization; zero alerts is NOT assumed.')})
      .finally(() => {if(alive) setLoading(false)})
    return () => {alive=false}
  }, [client,view,category,offset,version])

  async function toggleRead(item) {
    if (working!==null) return
    setWorking(item.id)
    setError('')
    try {
      await client.setPlatformNotificationRead(item.id,!item.read_at)
      setVersion(value=>value+1)
    } catch {
      setError('The read status update was rejected. Refresh before retrying.')
    } finally {setWorking(null)}
  }

  function chooseView(next) {setView(next);setOffset(0)}
  function chooseCategory(next) {setCategory(next);setOffset(0)}
  return <section className="platform-alert-page" aria-label="Super Admin notification center">
    <div className="page-heading">
      <div><div className="eyebrow">RETAILGROWTHAI / SUPER ADMIN</div>
        <h1>Notifications &amp; alerts</h1>
        <p className="lead">Persistent, per-admin read/unread history from verified RetailGrowthAI database events.</p>
      </div>
      <button type="button" className="subtle-button" disabled={loading}
        onClick={()=>setVersion(v=>v+1)}>Refresh alerts</button>
    </div>
    <div className="panel platform-alert-disclaimer">
      <strong>Monitoring scope:</strong> database job failures, persisted poison receipts,
      delayed queue outbox records, stale worker leases, account approvals and
      subscription dates. <strong>Azure infrastructure uptime and real queue depths are not connected.</strong>
      No emails or publishing actions are sent.
    </div>
    {loading && <p role="status">Refreshing verified platform notifications…</p>}
    {error && <p className="notice-error" role="alert">{error}</p>}
    {data && !loading && <>
      <div className="platform-alert-tally" aria-label="Notification totals">
        <strong>{data.unread_active} unread / {data.total_active} active alerts</strong>
        <span>Database checked {new Date(data.database_checked_at).toLocaleString('en-IN')} · Azure telemetry unavailable</span>
      </div>
      <div className="platform-alert-filters" role="group" aria-label="Notification view">
        {VIEWS.map(([value,label])=><button type="button" key={value} aria-pressed={view===value}
          onClick={()=>chooseView(value)}>{label}</button>)}
      </div>
      <div className="platform-alert-filters" role="group" aria-label="Notification category">
        {CATEGORIES.map(([value,label])=><button type="button" key={value} aria-pressed={category===value}
          onClick={()=>chooseCategory(value)}>{label}</button>)}
      </div>
      <div className="platform-alert-list">
        {!data.items.length && <p role="status">No matching verified notifications.</p>}
        {data.items.map(item=><article className={'platform-alert-item alert-'+
          (item.severity==='critical'?'action':item.severity==='attention'?'attention':'info')} key={item.id}>
          <div className="platform-alert-indicator" aria-hidden="true">{item.severity==='critical'?'!':item.severity==='attention'?'◷':'i'}</div>
          <div className="platform-alert-body">
            <small>{item.category} · {item.active?'Active':'Resolved'} · {item.read_at?'Read':'Unread'}</small>
            <h2>{item.title}</h2><p>{item.detail}</p>
            <small>First seen {new Date(item.first_seen_at).toLocaleString('en-IN')}</small>
          </div>
          <div className="platform-alert-actions">
            {['onboarding','subscription'].includes(item.category) &&
              <Link className="text-link" to="/platform-admin">
                {item.category==='onboarding'?'Review requests':'Manage subscriptions'} →
              </Link>}
            <button type="button" className="subtle-button"
              disabled={working!==null}
              aria-label={(item.read_at?'Mark unread':'Mark read')+' — '+item.title}
              onClick={()=>toggleRead(item)}>{item.read_at?'Mark unread':'Mark read'}</button>
          </div>
        </article>)}
      </div>
      <div className="platform-pager">
        <button type="button" className="subtle-button" disabled={offset===0}
          onClick={()=>setOffset(Math.max(0,offset-PAGE_SIZE))}>Previous</button>
        <span>Page {Math.floor(offset/PAGE_SIZE)+1} · {data.items.length} shown</span>
        <button type="button" className="subtle-button" disabled={data.items.length<PAGE_SIZE||offset>=100000-PAGE_SIZE}
          onClick={()=>setOffset(o=>o+PAGE_SIZE)}>Next</button>
      </div>
    </>}
  </section>
}
