import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useRetailAuth } from './AuthProvider.jsx'

/** One RetailGrowthAI Auth entry for all roles; role selection is server-side. */
export default function LoginPage() {
  const { configured, signIn, signUp, loading, error: sessionError } = useRetailAuth()
  const location = useLocation()
  const [signup, setSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function submit(event) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      if (signup) {
        const result = await signUp(email.trim(), password)
        if (!result?.access_token) {
          setSignup(false)
          setPassword('')
          setMessage('Account request submitted. Confirm your email if prompted, then sign in.')
        }
      } else {
        await signIn(email.trim(), password)
      }
    } catch (cause) {
      setError(cause?.message || 'Unable to authenticate. Verify your credentials and try again.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="login-screen" aria-label="RetailGrowthAI sign-in">
    <div className="login-story">
      <div className="login-story-brand"><span className="brand-mark">R</span><strong>RetailGrowthAI</strong></div>
      <div className="login-story-copy">
        <span className="login-eyebrow">A SINGLE WORKSPACE FOR YOUR GROWTH</span>
        <h1>Build your brand. <em>Track every campaign.</em></h1>
        <p>Create campaigns, track renders, manage your plan and keep your marketing under control.</p>
        <div className="login-story-proof"><span>✦ Multi-business ready</span><span>✦ Private by default</span><span>✦ AI-assisted marketing</span></div>
      </div>
      <span className="login-story-footer">RetailGrowthAI · DEV environment</span>
    </div>
    <div className="login-form-side">
      <div className="login-card">
        <div className="login-mobile-brand"><span className="brand-mark">R</span>RetailGrowthAI</div>
        <div className="eyebrow">WELCOME TO RETAILGROWTHAI</div>
        <h2>{signup ? 'Create your account' : 'Sign in to continue'}</h2>
        <p className="login-helper">Your business dashboard and the SaaS owner's Platform Control use this same secure login.</p>
        {sessionError && <p role="alert" className="notice-error">{sessionError}</p>}
        {error && <p role="alert" className="notice-error">{error}</p>}
        {message && <p role="status" className="login-success">{message}</p>}
        {!configured && <p role="status" className="notice-error">Authentication is not configured in this build. Contact the RetailGrowthAI operator.</p>}
        <form onSubmit={submit}>
          <label>Email<input name="email" aria-label="Email" type="email" autoComplete="email" value={email}
            onChange={(event) => setEmail(event.target.value)} required /></label>
          <label>Password<input name="password" aria-label="Password" type="password" minLength={6}
            autoComplete={signup ? 'new-password' : 'current-password'} value={password}
            onChange={(event) => setPassword(event.target.value)} required /></label>
          <button type="submit" className="login-submit" disabled={busy || !configured || loading}>
            {busy ? 'Verifying…' : signup ? 'Create account' : 'Sign in'}
          </button>
        </form>
        <p className="login-switch">{signup ? 'Already registered?' : 'New to RetailGrowthAI?'}{' '}
          <button type="button" onClick={() => {
            setSignup(!signup)
            setPassword('')
            setError('')
            setMessage('')
          }}>{signup ? 'Sign in' : 'Create an account'}</button></p>
        <div className="login-security">Access is assigned after sign-in. Shop Owners see only their own businesses; verified SaaS Super Admins see platform monitoring.</div>
      </div>
    </div>
  </div>
}
