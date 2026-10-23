import { useEffect, useMemo, useState } from 'react'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createSocialApi, trustedConsentUrl } from './social-api.mjs'
import { SocialAuthoringPanel } from './SocialAuthoringPanel.jsx'
import { SocialStatusPanel } from './SocialStatusPanel.jsx'

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
  const [days, setDays] = useState([])
  const [reloadVersion, setReloadVersion] = useState(0)
  const [busy, setBusy] = useState(false)
  const [oauthBusy, setOAuthBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  // Release guard is only UX; server-side OAuth, approvals and subscription gates
  // remain mandatory regardless of any client-side flag.
  const enabled = import.meta.env?.VITE_PART2_SOCIAL_ENABLED === 'true'
  const oauthEnabled = enabled && import.meta.env?.VITE_PART2_SOCIAL_OAUTH_ENABLED === 'true'
  const oauthConnectable = {
    youtube: oauthEnabled,
    linkedin: oauthEnabled && import.meta.env?.VITE_PART2_LINKEDIN_OAUTH_ENABLED === 'true',
    facebook: oauthEnabled && import.meta.env?.VITE_PART2_META_OAUTH_ENABLED === 'true',
    instagram: oauthEnabled && import.meta.env?.VITE_PART2_META_OAUTH_ENABLED === 'true',
  }
  const authoringEnabled = enabled && import.meta.env?.VITE_PART2_SOCIAL_AUTHORING_ENABLED === 'true'
  const api = useMemo(() => enabled && user
    ? createSocialApi({baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL,
                        tokenProvider: () => client.getAccessToken()})
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
    setDays([])
    if (!api || !shopId) return
    setBusy(true)
    setError('')
    Promise.all([api.listAccounts(shopId), api.listJobs(shopId), api.listDays(shopId)])
      .then(([a, j, d]) => { if (live) {
        setAccounts(Array.isArray(a?.accounts) ? a.accounts : [])
        setJobs(Array.isArray(j?.jobs) ? j.jobs : [])
        setDays(Array.isArray(d?.days) ? d.days : [])
      }}).catch(err => { if (live) setError(err.message) })
      .finally(() => { if (live) setBusy(false) })
    return () => { live = false }
  }, [api, shopId, reloadVersion])

  const shop = shops.find(s => s.id === shopId)
  const zone = shop?.timezone || 'Asia/Kolkata'
  const canWrite = ['OWNER', 'EDITOR'].includes(shop?.membership?.role)


  async function connectProvider(provider) {
    if (!api || !shopId || !oauthConnectable[provider]) return
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
        <p>Only approved integrations can be connected. Each provider requires separate backend OAuth app credentials and reviewed permissions before its connect control can be enabled.</p>
        {notice && <p role="status">{notice}</p>}
        <div className="day-grid">
          {PROVIDERS.map(([key,label]) => {
            const connected = accounts.filter(a => a.provider === key && a.connection_status === 'CONNECTED')
            return <div className="day-card" key={key}>
              <div className="day-top">{label}</div>
              <p>{connected.length ? connected.map(a => a.display_name).join(', ') : 'Not connected'}</p>
              {oauthConnectable[key] && !connected.length &&
                <button type="button" disabled={oauthBusy || !shopId || !user}
                  onClick={() => connectProvider(key)}>Connect {label}</button>}
              {oauthEnabled && connected.map(a =>
                <button type="button" key={a.id} disabled={oauthBusy || !shopId}
                  onClick={() => disconnect(a.id)}>Disconnect {a.display_name}</button>)}
              <div className="day-footer">Tokens and publishing permissions remain server-only</div>
            </div>
          })}
        </div>
      </section>
      {enabled && user && shopId && <SocialStatusPanel shopId={shopId}
        jobs={jobs} loading={busy} />}
      {authoringEnabled && user && shopId && <SocialAuthoringPanel
        api={api} shopId={shopId} zone={zone} days={days} jobs={jobs}
        accounts={accounts} canWrite={canWrite}
        onUpdated={async () => setReloadVersion(v => v + 1)} />}
      {!authoringEnabled && <section className="panel" style={{marginTop:16}}>
        <h2>Publishing drafts are disabled</h2>
        <p>The owner-reviewed scheduling and cancellation features are behind a separate
          backend release gate. Your DEV workspace does not publish customer posts.</p>
      </section>}
    </>
  )
}
export default SocialWorkspace
