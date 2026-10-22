import { useEffect, useState } from 'react'
import { useRetailAuth } from './AuthProvider.jsx'

const fieldLabels = {
  business_name: 'Business name',
  category: 'Business category',
  description: 'Description',
  brand_voice: 'Brand voice',
  city: 'City',
  website_url: 'Website URL',
  contact_email: 'Contact email',
}

export function AccountWorkspace() {
  const { client, configured, loading, error: sessionError, user, signIn, signUp, signOut } = useRetailAuth()
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [shops, setShops] = useState([])
  const [shopId, setShopId] = useState('')
  const [profile, setProfile] = useState(null)
  const [newShop, setNewShop] = useState({ name: '', slug: '' })
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [failure, setFailure] = useState('')

  useEffect(() => {
    let active = true
    if (!user) {
      setShops([])
      setShopId('')
      setProfile(null)
      return () => { active = false }
    }
    client.listShops().then((result) => {
      if (!active) return
      setShops(result)
      setShopId((current) => result.some((s) => s.id === current) ? current : (result[0]?.id || ''))
    }).catch((err) => { if (active) setFailure(err.message) })
    return () => { active = false }
  }, [client, user])

  useEffect(() => {
    let active = true
    setProfile(null)
    if (!shopId || !user) return () => { active = false }
    client.getBusinessProfile(shopId).then((result) => {
      if (active) setProfile(result)
    }).catch((err) => { if (active) setFailure(err.message) })
    return () => { active = false }
  }, [client, shopId, user])

  async function run(action, successText) {
    setBusy(true)
    setFailure('')
    setMessage('')
    try {
      await action()
      setMessage(successText)
    } catch (err) {
      setFailure(err.message || 'Request failed')
    } finally {
      setBusy(false)
    }
  }

  if (!configured) return (
    <section className="panel">
      <h2>Supabase is not configured</h2>
      <p>Set the RetailGrowthAI-only VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY.
        Do not use WineShopPOS credentials or a service-role key.</p>
    </section>
  )
  if (loading) return <p role="status">Checking your sign-in session…</p>

  const selected = shops.find((shop) => shop.id === shopId)
  const mayEdit = selected?.membership?.role === 'OWNER' || selected?.membership?.role === 'EDITOR'

  return (
    <section className="panel" aria-label="Business account">
      <h1>Business account</h1>
      {sessionError && <p role="alert">{sessionError}</p>}
      {failure && <p role="alert">{failure}</p>}
      {message && <p role="status">{message}</p>}
      {!user ? (
        <form onSubmit={(event) => {
          event.preventDefault()
          run(async () => {
            if (mode === 'signup') {
              const data = await signUp(email, password)
              if (!data?.access_token) setMode('signin')
            } else await signIn(email, password)
          }, mode === 'signup' ? 'Registration submitted. Check your email if confirmation is required.' : 'Signed in.')
        }}>
          <h2>{mode === 'signup' ? 'Create account' : 'Sign in'}</h2>
          <label>Email <input type="email" autoComplete="email" required value={email}
            onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Password <input type="password" minLength={6} required
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button type="submit" disabled={busy}>{mode === 'signup' ? 'Register' : 'Sign in'}</button>
          <button type="button" onClick={() => { setFailure(''); setMessage(''); setMode(mode === 'signup' ? 'signin' : 'signup') }}>
            {mode === 'signup' ? 'Have an account? Sign in' : 'Create an account'}
          </button>
        </form>
      ) : (
        <>
          <p>Signed in as {user.email}</p>
          <button type="button" disabled={busy} onClick={() => run(signOut, 'Signed out.')}>Sign out</button>
          <h2>Your businesses</h2>
          {shops.length ? (
            <label>Choose business
              <select value={shopId} onChange={(event) => setShopId(event.target.value)}>
                {shops.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.membership.role})</option>)}
              </select>
            </label>
          ) : <p>No businesses yet. Create one below.</p>}
          {profile && (
            <form onSubmit={(event) => {
              event.preventDefault()
              run(async () => setProfile(await client.updateBusinessProfile(shopId, profile)), 'Profile saved.')
            }}>
              <h3>Business profile</h3>
              {Object.entries(fieldLabels).map(([field, label]) => (
                <label key={field}>{label}
                  {field === 'description' || field === 'brand_voice' ? (
                    <textarea disabled={!mayEdit} value={profile[field] || ''}
                      onChange={(event) => setProfile({ ...profile, [field]: event.target.value })} />
                  ) : (
                    <input disabled={!mayEdit} value={profile[field] || ''}
                      onChange={(event) => setProfile({ ...profile, [field]: event.target.value })}
                      type={field === 'contact_email' ? 'email' : field === 'website_url' ? 'url' : 'text'} />
                  )}
                </label>
              ))}
              <button type="submit" disabled={busy || !mayEdit}>Save business profile</button>
              {!mayEdit && <p>Viewer access is read-only.</p>}
            </form>
          )}
          <form onSubmit={(event) => {
            event.preventDefault()
            run(async () => {
              const created = await client.createShop(newShop)
              const result = await client.listShops()
              setShops(result)
              setShopId(created.id)
              setNewShop({ name: '', slug: '' })
            }, 'New business created.')
          }}>
            <h3>Add a business</h3>
            <label>Business name <input required maxLength={140} value={newShop.name}
              onChange={(event) => setNewShop({ ...newShop, name: event.target.value })} /></label>
            <label>Shop slug <input required pattern="[a-z0-9]+(-[a-z0-9]+)*" minLength={3} maxLength={60}
              value={newShop.slug} onChange={(event) => setNewShop({ ...newShop, slug: event.target.value })} /></label>
            <button type="submit" disabled={busy}>Create business</button>
          </form>
        </>
      )}
    </section>
  )
}
