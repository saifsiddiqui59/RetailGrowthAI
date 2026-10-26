import { useEffect, useState } from 'react'
import { useAuthorizedShops } from './useAuthorizedShops.js'
import { useSelectedShop } from './useSelectedShop.js'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { Card } from '../../components/ui/card.jsx'
import { Badge } from '../../components/ui/badge.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Skeleton } from '../../components/ui/skeleton.jsx'
import { PROFILE_FIELDS, profileDraft, profilePatch } from './business-settings-model.mjs'

function ProfileEditor({ client, userId, shop }) {
  const shopId = shop.id
  const role = shop.membership?.role
  const editable = role === 'OWNER' || role === 'EDITOR'
  const queryClient = useQueryClient()
  const key = ['settings', 'profile', userId, shopId]
  const profileQuery = useQuery({
    queryKey: key,
    queryFn: async () => {
      const result = await client.getBusinessProfile(shopId)
      if (result && result.shop_id !== shopId) throw new Error('Tenant mismatch')
      return result
    },
    enabled: Boolean(userId && shopId),
    staleTime: 0,
    gcTime: 0,
    retry: false,
  })
  const [draft, setDraft] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  useEffect(() => {
    setDraft(profileQuery.data ? profileDraft(profileQuery.data) : null)
    setError('')
  }, [profileQuery.data])
  const current = profileQuery.data
  let changes = null
  let invalid = ''
  if (current && draft) {
    try { changes = profilePatch(current, draft) }
    catch (problem) { invalid = problem.message }
  }
  const dirty = Boolean(changes && Object.keys(changes).length)
  async function save(event) {
    event.preventDefault()
    if (!editable || busy || !current || !draft) return
    setError('')
    setMessage('')
    let patch
    try {
      patch = profilePatch(current, draft)
      if (!Object.keys(patch).length) throw new Error('No changes to save.')
    } catch (problem) { setError(problem.message); return }
    setBusy(true)
    try {
      // The PostgREST PATCH is subject to OWNER/EDITOR policy. A zero-row
      // response is an authorization failure, never silently "saved".
      const result = await client.updateBusinessProfile(shopId, patch)
      if (!result || result.shop_id !== shopId) throw new Error('Saved profile scope could not be verified.')
      queryClient.setQueryData(key, result)
      // Creative Studio only reads verified, per-shop context. A successful
      // profile PATCH invalidates its matching view so returning from Settings
      // cannot continue to display a stale brand-readiness checklist.
      await queryClient.invalidateQueries({ queryKey: ['creative-launchpad', 'profile', userId, shopId] })
      setMessage('Business profile saved and verified for this business.')
    } catch {
      setError('Profile update was rejected or unavailable. Your changes were not confirmed.')
    } finally { setBusy(false) }
  }
  return <Card className="panel rg-settings-card" aria-label="Business profile settings">
    <div className="rg-settings-top"><div><h2>Business profile</h2>
      <p>Retailer-owned marketing context shared with authorized campaign features.</p></div>
      <Badge>{role === 'OWNER' ? 'Owner' : role === 'EDITOR' ? 'Editor' : 'Read only'}</Badge>
    </div>
    {profileQuery.isFetching && <div role="status"><Skeleton className="rg-skeleton" />Loading verified profile…</div>}
    {profileQuery.isError && <p role="alert">Profile cannot be verified for this business.
      <Button variant="outline" onClick={() => profileQuery.refetch()}>Retry</Button></p>}
    {profileQuery.isSuccess && !current && <p role="status">No business profile is available. Check your business setup in <Link to="/account">Account</Link>.</p>}
    {profileQuery.isSuccess && current && draft && <form aria-label="Business profile settings" onSubmit={save}>
      <div className="rg-settings-fields">
        {PROFILE_FIELDS.map(field => <label key={field.key}>{field.label}
          {field.multiline ? <textarea value={draft[field.key]} maxLength={field.limit}
              readOnly={!editable || busy} rows={field.key === 'description' ? 4 : 3}
              onChange={e => {setDraft(x => ({...x,[field.key]:e.target.value}));setMessage('')}} /> :
            <input value={draft[field.key]} maxLength={field.limit} type={field.kind === 'email' ? 'email' : field.kind === 'url' ? 'url' : 'text'}
              required={Boolean(field.required)} readOnly={!editable || busy}
              onChange={e => {setDraft(x => ({...x,[field.key]:e.target.value}));setMessage('')}} />}
        </label>)}
      </div>
      {!editable && <p role="status">Your VIEWER membership permits reading this profile, not editing it.</p>}
      {invalid && editable && <p className="rg-settings-hint" role="status">{invalid}</p>}
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <div className="rg-settings-actions">
        <Button type="submit" disabled={!editable || busy || !dirty || Boolean(invalid)}>{busy ? 'Saving…' : 'Save business profile'}</Button>
        <Button variant="outline" disabled={busy || !editable || !dirty} onClick={() => {setDraft(profileDraft(current));setError('');setMessage('')}}>Discard changes</Button>
      </div>
    </form>}
  </Card>
}

export default function BusinessSettings() {
  const { client, configured, user } = useRetailAuth()
  const shopsQuery = useAuthorizedShops({ client, user, configured })
  const shops = shopsQuery.data || []
  // Shop scope always derives from RLS-verified memberships, never a URL param.
  const { shopId, selectShop } = useSelectedShop({ user, shops })
  const shop = shops.find(row => row.id === shopId)
  return <div className="rg-workspace-page rg-settings">
    <div className="page-heading"><div><div className="eyebrow">BUSINESS / ACCOUNT</div>
      <h1>Workspace settings</h1>
      <p className="lead">Update your own retailer context; PostgreSQL still enforces role and tenant permissions for every change.</p></div>
      <Button asChild className="primary-action rg-workspace-cta"><Link to="/account">Account &amp; security</Link></Button>
    </div>
    {!configured && <Card className="panel"><p role="status">Connect the dedicated RetailGrowthAI Supabase project. Settings never use demo credentials.</p></Card>}
    {configured && user && <>
      {shopsQuery.isFetching && <p role="status">Checking your authorized businesses…</p>}
      {shopsQuery.isError && <Card className="panel"><p role="alert">Accessible businesses could not be verified.
        <Button variant="outline" onClick={() => shopsQuery.refetch()}>Retry</Button></p></Card>}
      {shopsQuery.isSuccess && !shops.length && <Card className="panel"><p role="status">You have no accessible businesses. <Link to="/account">Create a business</Link>.</p></Card>}
      {shop && <div className="rg-library-tools"><label>Business
        <select aria-label="Settings business" value={shop.id} onChange={e => selectShop(e.target.value)}>
          {shops.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}
        </select>
      </label></div>}
      {shop && <ProfileEditor key={user.id + ':' + shop.id} client={client} userId={user.id} shop={shop} />}
      <Card className="panel rg-settings-foot">
        <h2>Account &amp; subscription</h2><p>Password recovery, sign out and new business setup stay within your existing account workflows. Subscription changes are server controlled.</p>
        <div className="rg-settings-actions"><Button variant="outline" asChild><Link to="/account">Manage account</Link></Button>
          <Button variant="outline" asChild><Link to="/subscription">Plan and usage</Link></Button></div>
      </Card>
    </>}
  </div>
}
