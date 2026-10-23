import { useEffect, useMemo, useState } from 'react'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createSocialApi, trustedConsentUrl } from './social-api.mjs'

const PROVIDERS = [
  ['instagram', 'Instagram professional / Reels'],
  ['facebook', 'Facebook Pages'],
  ['linkedin', 'LinkedIn'],
  ['youtube', 'YouTube Shorts'],
]

export function SocialWorkspace() {
  const { client, user, loading } = useRetailAuth()
  const [shops, setShops] = useState([])
  const [shopId, setShopId] = useState('')
  const [accounts, setAccounts] = useState([])
  const [jobs, setJobs] = useState([])
  const [busy, setBusy] = useState(false)
  const [oauthBusy, setOAuthBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [day, setDay] = useState('')
  const [clock, setClock] = useState('10:00')
  const [preview, setPreview] = useState('')

  // Release guard is only UX; server-side OAuth, approvals and subscription gates
  // remain mandatory regardless of any client-side flag.
  const enabled = import.meta.env?.VITE_PART2_SOCIAL_ENABLED === 'true'
  const oauthEnabled = enabled && import.meta.env?.VITE_PART2_SOCIAL_OAUTH_ENABLED === 'true'
  const api = useMemo(() => enabled && user
    ? createSocialApi({baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL,
                        tokenProvider: () => client.accessToken()})
    : null, [enabled, user, client])

  useEffect(() => {
    let live = true
    if (!user) { setShops([]); setShopId(''); return }
    client.listShops().then(data => {
      if (live) {
        setShops(data)
        setShopId(old => data.some(s => s.id === old) ? old : (data[0]?.id || ''))
      }
    }).catch(() => { if (live) setError('Unable to load businesses. Refresh Account.') })
    return () => { live = false }
  }, [client, user])

  useEffect(() => {
    let live = true
    setAccounts([])
    setJobs([])
    if (!api || !shopId) return
    setBusy(true)
    setError('')
    Promise.all([api.listAccounts(shopId), api.listJobs(shopId)])
      .then(([a, j]) => { if (live) {
        setAccounts(Array.isArray(a?.accounts) ? a.accounts : [])
        setJobs(Array.isArray(j?.jobs) ? j.jobs : [])
      }}).catch(err => { if (live) setError(err.message) })
      .finally(() => { if (live) setBusy(false) })
    return () => { live = false }
  }, [api, shopId])

  const shop = shops.find(s => s.id === shopId)
  const zone = shop?.timezone || 'Asia/Kolkata'
  function previewSchedule(event) {
    event.preventDefault()
    if (!day || !/^\d{2}:\d{2}$/.test(clock)) {
      setPreview('Choose a date and a time.')
      return
    }
    setPreview(day + ' at ' + clock + ' (' + zone +
      '). Preview only: this is not scheduled or approved. Final time and DST validation happen on the server.')
  }


  async function connectProvider(provider) {
    if (!api || !shopId || !oauthEnabled || provider !== 'youtube') return
    setOauthBusy(true)
    setError('')
    setNotice('')
    try {
      const result = await api.startOAuth(shopId, provider)
      const consentUrl = trustedConsentUrl(result.authorization_url, provider)
      window.sessionStorage.setItem('rgai-part2-oauth-pending',
        JSON.stringify({shopId, provider}))
      window.location.assign(consentUrl)
    } catch {
      setError('Unable to start authorization. Verify you are the business OWNER and try again.')
      setOauthBusy(false)
    }
  }

  async function disconnect(accountId) {
    if (!api || !shopId || !oauthEnabled) return
    setOauthBusy(true)
    setError('')
    setNotice('')
    try {
      await api.disconnectAccount(shopId, accountId)
      setAccounts(old => old.filter(item => item.id !== accountId))
      setNotice('Local account disconnected. Any scheduled posts for this account were cancelled.')
    } catch {
      setError('Unable to disconnect this account. Business OWNER permissions are required.')
    } finally {
      setOauthBusy(false)
    }
  }

  if (loading) return <p role="status">Checking session…</p>
  return (
    <>
      <div className="eyebrow">PART 2 · APPROVAL-GATED DEVELOPMENT</div>
      <h1>Social publishing</h1>
      <p className="lead">Connect business-owned social accounts, approve posts and schedule publication only after official platform permissions and server controls are enabled.</p>
      {!enabled && <section className="panel" role="status">
        <h2>Publishing is not enabled</h2>
        <p>This is a preview workspace. No social account is connected, no OAuth permission is granted, and nothing can be published from this screen.</p>
      </section>}
      {!user && <p role="status">Sign in through Account to see your authorized businesses.</p>}
      {user && <section className="panel" style={{marginTop:16}}>
        <h2>Authorized business</h2>
        <label htmlFor="social-shop">Business</label>
        <select id="social-shop" value={shopId} onChange={e=>setShopId(e.target.value)}
          style={{display:'block',marginTop:8,padding:10,width:'100%',maxWidth:450}}>
          {shops.length===0 && <option value="">No business available</option>}
          {shops.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <p>Business timezone: <strong>{zone}</strong>. Roles and account permissions are always rechecked server-side.</p>
        {error && <p role="alert">{error}</p>}
        {busy && <p role="status">Loading publishing metadata…</p>}
      </section>}
      <section className="panel" style={{marginTop:16}}>
        <h2>Platforms</h2>
        <p>Only approved integrations can be connected. YouTube starts as the first gated connection; Meta and LinkedIn require separate app credentials and platform permissions.</p>
        {notice && <p role="status">{notice}</p>}
        <div className="day-grid">
          {PROVIDERS.map(([key,label]) => {
            const connected = accounts.filter(a => a.provider === key && a.connection_status === 'CONNECTED')
            return <div className="day-card" key={key}>
              <div className="day-top">{label}</div>
              <p>{connected.length ? connected.map(a => a.display_name).join(', ') : 'Not connected'}</p>
              {oauthEnabled && key === 'youtube' && !connected.length &&
                <button type="button" disabled={oauthBusy || !shopId || !user}
                  onClick={() => connectProvider(key)}>Connect YouTube</button>}
              {oauthEnabled && connected.map(a =>
                <button type="button" key={a.id} disabled={oauthBusy || !shopId}
                  onClick={() => disconnect(a.id)}>Disconnect {a.display_name}</button>)}
              <div className="day-footer">Tokens and publishing permissions remain server-only</div>
            </div>
          })}
        </div>
      </section>
      <section className="panel" style={{marginTop:16}}>
        <h2>Scheduling preview</h2>
        <p>Plan a local wall-clock time. A server-side DST and entitlement check will be required before a job can actually be scheduled.</p>
        <form onSubmit={previewSchedule} style={{display:'flex',gap:12,flexWrap:'wrap',alignItems:'end'}}>
          <label>Date<input type="date" value={day} onChange={e=>setDay(e.target.value)}
            style={{display:'block',marginTop:6,padding:10}} required /></label>
          <label>Local time<input type="time" value={clock} onChange={e=>setClock(e.target.value)}
            style={{display:'block',marginTop:6,padding:10}} required /></label>
          <button type="submit" style={{padding:'12px 16px'}}>Preview only</button>
        </form>
        {preview && <p role="status">{preview}</p>}
        <p>Scheduled jobs loaded: {jobs.length}. The preview never submits a publishing job.</p>
      </section>
    </>
  )
}
export default SocialWorkspace
