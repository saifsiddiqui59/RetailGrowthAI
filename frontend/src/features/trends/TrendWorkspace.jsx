import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createTrendApi } from './trend-api.mjs'
import TrendRecommendations from './TrendRecommendations.jsx'

const tomorrowIndia = () => {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date())
  const get = type => parts.find(part => part.type === type)?.value
  const date = new Date(Date.UTC(Number(get('year')), Number(get('month')) - 1, Number(get('day')) + 1))
  return date.toISOString().slice(0, 10)
}

export default function TrendWorkspace() {
  const { configured, user, client } = useRetailAuth()
  const [shops, setShops] = useState([])
  const [shopId, setShopId] = useState('')
  const [assets, setAssets] = useState([])
  const [assetId, setAssetId] = useState('')
  const [results, setResults] = useState(null)
  const [brief, setBrief] = useState('Write seven days of practical marketing content using my licensed product photos.')
  const [startDate, setStartDate] = useState(tomorrowIndia)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(null)
  const api = useMemo(() => createTrendApi({
    baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL,
    tokenProvider: () => client.getAccessToken(),
  }), [client])
  useEffect(() => {
    if (!configured || !user || !api) return
    let active = true
    client.listShops().then(rows => {
      if (!active) return
      setShops(rows)
      setShopId(current => rows.some(row => row.id === current) ? current : (rows[0]?.id || ''))
    }).catch(() => { if (active) setError('Your authorized businesses could not be loaded.') })
    return () => { active = false }
  }, [client, configured, user?.id, api])
  useEffect(() => {
    if (!shopId || !api) return
    let active = true
    setLoading(true)
    setResults(null)
    setAssets([])
    setAssetId('')
    setSaved(null)
    setError('')
    Promise.all([api.getRecommendations(shopId), client.listMediaAssets(shopId)])
      .then(([data, media]) => {
        if (!active) return
        if (data.shop_id !== shopId) throw new Error('The trend service returned the wrong shop')
        setResults(data)
        const safeAssets = media.filter(item => item.shop_id === shopId && item.license_name)
        setAssets(safeAssets)
        setAssetId(safeAssets[0]?.id || '')
      }).catch(() => {
        if (active) setError('Trend data or authorized media are unavailable. No content was generated.')
      }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [shopId, api, client])
  const member = shops.find(shop => shop.id === shopId)?.membership
  const canWrite = member?.active && ['OWNER', 'EDITOR'].includes(member.role)
  const createDraft = useCallback(async trend => {
    if (!api || !canWrite || !assetId || saving) return
    setSaving(true)
    setError('')
    setSaved(null)
    try {
      const data = await api.createDraft(shopId, trend.trend_id, {
        shop_id: shopId, brief, duration_days: 7, start_date: startDate,
        timezone: 'Asia/Kolkata', language: 'en-IN',
        platforms: ['linkedin', 'instagram'],
        media_asset_ids: [assetId], offer: null,
      })
      if (data.shop_id !== shopId || data.status !== 'DRAFT') {
        throw new Error('Unexpected draft response')
      }
      setSaved(data.draft_id)
    } catch {
      setError('Draft could not be saved. Verify your business profile, image license and source availability.')
    } finally { setSaving(false) }
  }, [api, canWrite, assetId, brief, startDate, saving, shopId])
  if (!configured || !api) return (
    <section className="feature2-trends" aria-label="Trends unavailable">
      <h1>Trend Intelligence</h1>
      <p>Demo / setup mode. Connect RetailGrowthAI DEV authentication and campaign API to access real tenant recommendations. No fabricated trends are shown.</p>
      <Link to="/account">Configure your business profile</Link>
    </section>
  )
  if (!user) return <p>Sign in to view authorized business trends.</p>
  return (
    <section className="feature2-trends" aria-label="Trend intelligence workspace">
      <h1>Trend Intelligence</h1>
      <p>Daily, source-linked India insights for your own business. Drafts require retailer review; publishing is never automatic.</p>
      <div className="feature2-filters">
        <label>Business
          <select value={shopId} onChange={event => setShopId(event.target.value)}>
            {shops.map(shop => <option key={shop.id} value={shop.id}>{shop.name}</option>)}
          </select>
        </label>
        <label>Approved business image
          <select value={assetId} onChange={event => setAssetId(event.target.value)}>
            {!assets.length && <option value="">No licensed images uploaded</option>}
            {assets.map(asset => <option key={asset.id} value={asset.id}>
              {asset.id.slice(0, 8)} · {asset.license_name}
            </option>)}
          </select>
        </label>
        <label>Campaign start date
          <input type="date" value={startDate} min={tomorrowIndia()} onChange={event => setStartDate(event.target.value)} />
        </label>
      </div>
      <label className="feature2-brief">Content brief
        <textarea rows={3} maxLength={2000} minLength={10} value={brief}
          onChange={event => setBrief(event.target.value)} />
      </label>
      {!assets.length && <p><Link to="/campaigns">Upload a licensed image in Campaigns</Link> before creating a draft.</p>}
      {!canWrite && shops.length > 0 && <p>Viewer access: you can read trends but cannot create drafts.</p>}
      {loading && <p role="status">Loading authorized recommendations…</p>}
      {error && <p role="alert">{error}</p>}
      {saved && <p role="status">Content draft saved for retailer review: {saved}. It has not been published or added to an existing campaign.</p>}
      {saving && <p role="status">Saving draft…</p>}
      {results?.profile_required && <p role="status">
        Complete your business city in <Link to="/account">Business account &amp; profile</Link> to enable relevant trend recommendations.
        We do not guess a shop's location or create promotional drafts from incomplete business information.
      </p>}
      {results && !results.profile_required && <TrendRecommendations recommendations={results.recommendations}
        sources={results.sources}
        onDraft={canWrite && assetId && !saving && brief.trim().length >= 10 && startDate >= tomorrowIndia()
          ? createDraft : null} />}
    </section>
  )
}
