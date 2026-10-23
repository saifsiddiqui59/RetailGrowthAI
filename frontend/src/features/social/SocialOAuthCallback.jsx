import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { createSocialApi } from './social-api.mjs'

const PENDING = 'rgai-part2-oauth-pending'

/** Only temporary account-linking metadata is kept in session storage, not tokens. */
export function SocialOAuthCallback() {
  const { provider } = useParams()
  const { client, user, loading } = useRetailAuth()
  const [result, setResult] = useState('Validating account authorization…')
  const [failed, setFailed] = useState(false)
  const executed = useRef(false)

  useEffect(() => {
    // Always scrub one-time provider code/state from address/history first,
    // even when the release flag is OFF or the user session has expired.
    if (loading || executed.current) return
    executed.current = true
    const params = new URLSearchParams(window.location.search)
    window.history.replaceState(window.history.state, '', window.location.pathname)
    const pending = (() => {
      try { return JSON.parse(window.sessionStorage.getItem(PENDING) || 'null') } catch { return null }
    })()
    try { window.sessionStorage.removeItem(PENDING) } catch { /* unavailable */ }
    const enabled = import.meta.env?.VITE_PART2_SOCIAL_ENABLED === 'true' &&
      import.meta.env?.VITE_PART2_SOCIAL_OAUTH_ENABLED === 'true'
    if (!enabled || !user || !pending || pending.provider !== provider ||
        !pending.shopId || params.has('error') ||
        !params.get('code') || !params.get('state')) {
      setFailed(true)
      setResult('This connection could not be completed. Sign in with the same business owner account and reconnect.')
      return
    }
    let api
    try {
      api = createSocialApi({
        baseUrl: import.meta.env?.VITE_CAMPAIGN_API_BASE_URL,
        tokenProvider: () => client.accessToken(),
      })
      if (!api) throw new Error('not configured')
    } catch {
      setFailed(true)
      setResult('The social connection service is not configured.')
      return
    }
    api.completeOAuth(pending.shopId, provider, params.get('state'), params.get('code'))
      .then(() => setResult('Account connection confirmed. Return to Social publishing to see it.'))
      .catch(() => {
        setFailed(true)
        setResult('Account authorization failed or expired. Reconnect from Social publishing.')
      })
  }, [loading, user, client, provider])

  return (
    <section className="panel" aria-label="Social account authorization" style={{marginTop:16}}>
      <h1>Social account authorization</h1>
      <p role={failed ? 'alert' : 'status'}>{result}</p>
      <Link to="/social">Return to Social publishing</Link>
    </section>
  )
}

export default SocialOAuthCallback
