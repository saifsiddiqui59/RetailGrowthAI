import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createTrendApi } from './trend-api.mjs'
import { reconcileSubmittedDraft } from './trend-draft-reconcile.mjs'
import { offerStandardCampaignFallback } from './trend-empty-state.mjs'
import TrendRecommendations from './TrendRecommendations.jsx'

const PROMPT_FORMATS = [
  'instagram_caption', 'facebook_post', 'linkedin_post',
  'youtube_shorts_description', 'poster_brief', 'reel_storyboard',
]

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
  const [improveEnabled, setImproveEnabled] = useState(false)
  const [realAiEnabled, setRealAiEnabled] = useState(false)
  const [promptLanguage, setPromptLanguage] = useState('en-IN')
  const [promptFormats, setPromptFormats] = useState(PROMPT_FORMATS)
  const [promptPreview, setPromptPreview] = useState(null)
  const [editedPrompt, setEditedPrompt] = useState('')
  const [appliedPrompt, setAppliedPrompt] = useState('')
  const [promptLoading, setPromptLoading] = useState(false)
  const [promptError, setPromptError] = useState('')
  const [chosenTrendId, setChosenTrendId] = useState('')
  const latestShopRef = useRef(shopId)
  const latestAiModeRef = useRef(realAiEnabled)
  const autoPreviewKeyRef = useRef('')
  useEffect(() => { latestShopRef.current = shopId }, [shopId])
  useEffect(() => { latestAiModeRef.current = realAiEnabled }, [realAiEnabled])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(null)
  const [drafts, setDrafts] = useState([])
  const [draftError, setDraftError] = useState('')
  const [draftLoading, setDraftLoading] = useState(false)
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
    setPromptPreview(null)
    setAppliedPrompt('')
    setChosenTrendId('')
    setPromptError('')
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
  useEffect(() => {
    if (!shopId || !api) return
    let active = true
    setDrafts([])
    setDraftError('')
    setDraftLoading(true)
    api.listDrafts(shopId).then(data => {
      if (!active) return
      if (data.shop_id !== shopId || !Array.isArray(data.drafts)) {
        throw new Error('Invalid saved draft response')
      }
      setDrafts(data.drafts.filter(item => item.shop_id === shopId))
    }).catch(() => {
      if (active) setDraftError('Saved drafts could not be loaded; trend recommendations are unaffected.')
    }).finally(() => { if (active) setDraftLoading(false) })
    return () => { active = false }
  }, [shopId, api])
  const member = shops.find(shop => shop.id === shopId)?.membership
  const canWrite = member?.active && ['OWNER', 'EDITOR'].includes(member.role)
  const improve = useCallback(async () => {
    if (!api || !canWrite || !improveEnabled || !shopId || promptLoading) return
    setPromptError('')
    setPromptPreview(null)
    setAppliedPrompt('')
    setPromptLoading(true)
    try {
      const response = realAiEnabled
        ? await api.improvePromptWithAI(shopId, brief, promptFormats, promptLanguage)
        : await api.improvePrompt(shopId, brief, promptFormats, promptLanguage)
      // A slow response for shop A must never render after switching to B.
      if (latestShopRef.current !== shopId || latestAiModeRef.current !== realAiEnabled) return
      if (response.shop_id !== shopId || response.original_prompt !== brief ||
          response.can_publish !== false || response.review_status !== 'NEEDS_REVIEW' ||
          response.provider_mode !== (realAiEnabled ? 'approved_llm' : 'deterministic') ||
          response.usage?.paid_inference_calls !== (realAiEnabled ? 1 : 0) ||
          (realAiEnabled && (!Number.isFinite(response.usage?.actual_paid_cost_usd) ||
            response.usage.actual_paid_cost_usd < 0 || response.usage.actual_paid_cost_usd > 0.05)) ||
          typeof response.improved_prompt !== 'string' ||
          response.improved_prompt.length > 1500) {
        throw new Error('Invalid or stale prompt response')
      }
      setPromptPreview(response)
      setEditedPrompt(response.improved_prompt)
    } catch {
      setPromptError('Prompt improvement was unavailable. Your original request is preserved; no content was generated or saved.')
    } finally {
      setPromptLoading(false)
    }
  }, [api, canWrite, improveEnabled, realAiEnabled, shopId, promptLoading, brief, promptFormats, promptLanguage])
  // Checking the free preview box now SHOWS the enhanced prompt automatically.
  // Never auto-trigger paid Azure AI; that remains a separate explicit click.
  useEffect(() => {
    if (!improveEnabled || realAiEnabled || !canWrite || !shopId ||
        promptPreview || promptLoading || promptError || brief.trim().length < 10 ||
        !promptFormats.length) return
    const key = JSON.stringify([shopId, brief, promptFormats, promptLanguage])
    if (autoPreviewKeyRef.current === key) return
    autoPreviewKeyRef.current = key
    void improve()
  }, [improveEnabled, realAiEnabled, canWrite, shopId, promptPreview,
      promptLoading, promptError, brief, promptFormats, promptLanguage, improve])
  const originalChanged = value => {
    setBrief(value)
    setAppliedPrompt('')
    setPromptPreview(null)
    setPromptError('')
  }
  const restoreOriginal = () => {
    setAppliedPrompt('')
    setEditedPrompt(promptPreview?.original_prompt || brief)
  }
  const applyImproved = () => {
    if (promptPreview && editedPrompt.trim() && editedPrompt.length <= 1500 &&
        promptPreview.original_prompt === brief) {
      setAppliedPrompt(editedPrompt.trim())
      setPromptError('')
    }
  }
  const createDraft = useCallback(async trend => {
    if (!api || !canWrite || !assetId || saving) return
    setSaving(true)
    setError('')
    setSaved(null)
    const targetShop = shopId
    const submissionId = crypto.randomUUID()
    let postAttempted = false
    try {
      // GET must work before attempting an irreversible POST. This protects
      // against blind retries when the Azure #249 gateway loses an ACK.
      const before = await api.listDrafts(targetShop)
      if (before.shop_id !== targetShop || !Array.isArray(before.drafts)) {
        throw new Error('Recent draft readback unavailable')
      }
      const campaign = {
        shop_id: targetShop, brief: appliedPrompt || brief, duration_days: 7, start_date: startDate,
        timezone: 'Asia/Kolkata', language: 'en-IN',
        platforms: ['linkedin', 'instagram'],
        media_asset_ids: [assetId], offer: null,
      }
      postAttempted = true
      // Once attempted, never automatically send this POST a second time.
      const data = realAiEnabled
        ? await api.createDraftWithAI(targetShop, trend.trend_id, campaign, submissionId)
        : await api.createDraft(targetShop, trend.trend_id, campaign, submissionId)
      if (data.shop_id !== targetShop || data.status !== 'DRAFT') {
        throw new Error('Unconfirmed draft acknowledgement')
      }
      setSaved(data.draft_id)
      try {
        const recent = await api.listDrafts(targetShop)
        if (recent.shop_id === targetShop && Array.isArray(recent.drafts)) {
          setDrafts(recent.drafts)
          setDraftError('')
        }
      } catch {
        setDraftError('Draft saved, but the review list could not refresh.')
      }
    } catch {
      if (!postAttempted) {
        setError('Saved draft history could not be verified. No new draft was submitted.')
      } else {
        // A failed HTTP response is NOT evidence that Azure did not commit.
        // Re-read using the signed-in user's RLS view; no mutation/retry.
        try {
          const recent = await api.listDrafts(targetShop)
          if (recent.shop_id !== targetShop || !Array.isArray(recent.drafts)) {
            throw new Error('Invalid readback shop')
          }
          const recoveredId = reconcileSubmittedDraft(recent.drafts, {
            shopId: targetShop, trendId: trend.trend_id, submissionId,
          })
          setDrafts(recent.drafts)
          if (recoveredId) {
            setSaved(recoveredId)
            setDraftError('')
            setError('Azure interrupted the response, but this draft was confirmed in your saved history. It was not submitted again.')
          } else {
            setError('The save outcome is not confirmed. Check Saved drafts before starting another request; no automatic retry was made.')
          }
        } catch {
          setError('The save outcome is unknown because the signed-in read-back failed. Do not retry until you can check Saved drafts.')
        }
      }
    } finally { setSaving(false) }
  }, [api, canWrite, assetId, brief, appliedPrompt, realAiEnabled, startDate, saving, shopId])
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
          <select value={shopId} onChange={event => { latestShopRef.current = event.target.value; setShopId(event.target.value) }}>
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
        <textarea rows={3} maxLength={1500} minLength={10} value={brief}
          onChange={event => originalChanged(event.target.value)} />
      </label>
      <section className="feature2-prompt-workspace" aria-label="AI prompt improver">
        <h2>Prompt Improver</h2>
        <label className="feature2-check">
          <input type="checkbox" checked={realAiEnabled} onChange={event => {
            latestAiModeRef.current = event.target.checked
            setRealAiEnabled(event.target.checked)
            autoPreviewKeyRef.current = ''
            setPromptPreview(null)
            setAppliedPrompt('')
            setEditedPrompt('')
            setPromptError('')
          }} />
          Use real Azure AI model (requires approved shop budget)
        </label>
        <p>{realAiEnabled
          ? 'Real AI is explicitly selected. Model calls require a separately approved server-side shop spending limit; unavailable or rejected calls do not silently use a mock.'
          : 'Free local template mode selected. No paid AI model calls.'}</p>
        <label className="feature2-check">
          <input type="checkbox" checked={improveEnabled}
            onChange={event => {
              setImproveEnabled(event.target.checked)
              autoPreviewKeyRef.current = ''
              if (!event.target.checked) { setAppliedPrompt(''); setPromptPreview(null); }
            }} />
          Improve Prompt with AI
        </label>
        <p>When checked, a free enhanced prompt preview appears automatically. For actual Azure AI enhancement, also enable the budget-controlled model above and click Improve Prompt. Both versions require your review before use; neither automatically generates a Reel.</p>
        {improveEnabled && <>
          <div className="feature2-filters">
            <label>Prompt language
              <select value={promptLanguage} onChange={event => {
                setPromptLanguage(event.target.value); setPromptPreview(null); setAppliedPrompt('')
              }}>
                <option value="en-IN">English (India)</option>
                <option value="hi-IN">Hindi</option>
                <option value="mr-IN">Marathi</option>
              </select>
            </label>
          </div>
          <fieldset className="feature2-output-formats">
            <legend>Requested creative outputs</legend>
            {PROMPT_FORMATS.map(fmt => <label key={fmt} className="feature2-check">
              <input type="checkbox" checked={promptFormats.includes(fmt)}
                onChange={event => {
                  setPromptFormats(rows => event.target.checked ?
                    [...rows, fmt] : rows.filter(row => row !== fmt))
                  setPromptPreview(null); setAppliedPrompt('')
                }} />
              {fmt.replaceAll('_', ' ')}
            </label>)}
          </fieldset>
          <button type="button" onClick={improve} disabled={!canWrite || promptLoading ||
            !brief.trim() || !promptFormats.length}>
            {promptLoading ? 'Improving…' : 'Improve Prompt'}
          </button>
        </>}
        {promptError && <p role="alert">{promptError}</p>}
        {promptPreview && improveEnabled && (
          <div aria-label="Original and improved prompt preview">
            <p role="status">Enhanced prompt ready for your review. Compare, edit, then choose Use Improved Prompt.</p>
            <div className="feature2-prompt-pair">
              <label>Original prompt
                <textarea readOnly value={promptPreview.original_prompt} rows={8} />
              </label>
              <label>Improved prompt (editable)
                <textarea value={editedPrompt} maxLength={1500} rows={8}
                  onChange={event => { setEditedPrompt(event.target.value); setAppliedPrompt('') }} />
              </label>
            </div>
            <h3>What changed and why</h3>
            <ul>{promptPreview.improvement_suggestions.map((point, index) =>
              <li key={index}>{point}</li>)}</ul>
            <p>Business context used: {Object.entries(promptPreview.business_context_used)
              .filter(([, value]) => typeof value === 'string' && value)
              .map(([key, value]) => key.replaceAll('_', ' ') + ': ' + value).join('; ')}.</p>
            <p>Provider: {promptPreview.provider_mode}; paid calls: {promptPreview.usage.paid_inference_calls}.
              {promptPreview.usage.actual_paid_cost_usd != null &&
                <> Actual model cost: USD {promptPreview.usage.actual_paid_cost_usd.toFixed(6)}.</>}
              Status: Human review required. Outputs: {promptPreview.output_formats.join(', ')}.</p>
            <div className="feature2-prompt-actions">
              <button type="button" onClick={applyImproved}
                disabled={!editedPrompt.trim() || editedPrompt.length > 1500}>Use Improved Prompt</button>
              <button type="button" onClick={restoreOriginal}>Restore Original</button>
            </div>
          </div>
        )}
        <p role="status">{appliedPrompt ? 'Improved prompt selected for the next draft.' :
          'Original request selected. Improvement never runs automatically.'}</p>
        {promptLanguage !== 'en-IN' && <p>Current canonical v1 campaigns remain English.
          This language selection prepares prompt guidance only; it does not claim translated output.</p>}
        <div className="feature2-prompt-actions">
          <label>Verified trend for this draft
            <select value={chosenTrendId} onChange={event => setChosenTrendId(event.target.value)}>
              <option value="">Select a relevant current trend</option>
              {(results?.recommendations || []).map(t =>
                <option value={t.trend_id} key={t.trend_id}>{t.title}</option>)}
            </select>
          </label>
          <button type="button" disabled={!canWrite || !assetId || saving ||
            !chosenTrendId || (appliedPrompt || brief).trim().length < 10 ||
            startDate < tomorrowIndia()}
            onClick={() => {
              const t = (results?.recommendations || []).find(x => x.trend_id === chosenTrendId)
              if (t) createDraft(t)
            }}>
            {realAiEnabled ? 'Generate with real AI' : 'Generate Content'}
          </button>
        </div>
        {!chosenTrendId && <p>Generating a trend-backed draft requires a verified matching trend.
          For an ordinary, nontrend campaign use <Link to="/campaigns">Campaign Studio</Link>.</p>}
      </section>
      {!assets.length && <p><Link to="/campaigns">Upload a licensed image in Campaigns</Link> before creating a draft.</p>}
      {!canWrite && shops.length > 0 && <p>Viewer access: you can read trends but cannot create drafts.</p>}
      {loading && <p role="status">Loading authorized recommendations…</p>}
      {error && <p role="alert">{error}</p>}
      {offerStandardCampaignFallback({ loading, error, results }) && (
        <div className="feature2-evergreen-fallback" role="status">
          <p>No verified, relevant trend is needed for a regular campaign. Use your own approved media
            to create a standard seven-day draft instead. It will not claim that your topic is trending.</p>
          <Link to="/campaigns">Create a standard campaign without a trend</Link>
        </div>
      )}
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
      <section aria-label="Saved content drafts" className="feature2-saved-drafts">
        <h2>Saved drafts for review</h2>
        <p>Five most recent drafts for this shop. These are not published or approved.</p>
        {draftLoading && <p role="status">Loading saved drafts…</p>}
        {draftError && <p role="alert">{draftError}</p>}
        {!draftLoading && !draftError && !drafts.length && <p>No saved drafts for this shop.</p>}
        {drafts.map(item => <details key={item.id}>
          <summary>Draft {item.id.slice(0, 8)} · {item.review_state} · {item.created_at || 'No date'}</summary>
          <p>Verified trend reference: {item.trend_id}. Retailer approval is still required.</p>
          <ol>{(item.content?.campaign?.days || []).slice(0, 7).map((day, index) =>
            <li key={day.id || index}>
              <strong>Day {index + 1}: {day.topic}</strong>
              <p>{day.linkedin?.post_text || 'LinkedIn copy unavailable'}</p>
              <p>{day.instagram?.caption || 'Instagram caption unavailable'}</p>
            </li>)}</ol>
        </details>)}
      </section>
    </section>
  )
}
