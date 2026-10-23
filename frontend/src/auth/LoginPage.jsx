import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useRetailAuth } from './AuthProvider.jsx'

/** One RetailGrowthAI Auth entry for all roles; role selection is server-side. */
export default function LoginPage() {
  const { configured, signIn, signUp, requestPasswordReset, updateRecoveredPassword,
    recoveryMode, loading, error: sessionError } = useRetailAuth()
  const location = useLocation()
  const [signup, setSignup] = useState(false)
  const [forgot, setForgot] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState('')
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
      if (recoveryMode) {
        if (password !== confirmPassword) throw new Error('Passwords do not match.')
        await updateRecoveredPassword(password)
        setPassword('')
        setConfirmPassword('')
        setMessage('Password updated. Sign in using your new password.')
      } else if (forgot) {
        await requestPasswordReset(email.trim())
        setForgot(false)
        setPassword('')
        setMessage('If this email has an account, a password reset link will be sent. Check your inbox.')
      } else if (signup) {
        const result = await signUp(email.trim(), password)
        if (!result?.access_token) {
          setSignup(false)
          setPassword('')
          setMessage('Registration submitted. If email confirmation is enabled, check your inbox before signing in. Business approval is a separate process.')
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
        <h2>{recoveryMode ? 'Set a new password' : forgot ? 'Reset your password' : signup ? 'Create your account' : 'Sign in to continue'}</h2>
        <p className="login-helper">{recoveryMode ? 'Choose a new password for the email link you opened.' : forgot
          ? 'We will send a reset link if an account exists. Never share the link.' :
          "Your business dashboard and the SaaS owner's Platform Control use this same secure login."}</p>
        {sessionError && <p role="alert" className="notice-error">{sessionError}</p>}
        {error && <p role="alert" className="notice-error">{error}</p>}
        {message && <p role="status" className="login-success">{message}</p>}
        {!configured && <p role="status" className="notice-error">Authentication is not configured in this build. Contact the RetailGrowthAI operator.</p>}
        <form onSubmit={submit}>
          {!recoveryMode && <label>Email<input name="email" aria-label="Email" type="email" autoComplete="email" value={email}
            onChange={(event) => setEmail(event.target.value)} required /></label>}
          {!forgot && <label>Password<input name="password" aria-label="Password" type="password"
            minLength={recoveryMode ? 12 : 6}
            autoComplete={signup || recoveryMode ? 'new-password' : 'current-password'} value={password}
            onChange={(event) => setPassword(event.target.value)} required /></label>}
          {recoveryMode && <label>Confirm new password<input name="confirmPassword"
            aria-label="Confirm new password" type="password" minLength={12}
            autoComplete="new-password" value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)} required /></label>}
          <button type="submit" className="login-submit" disabled={busy || !configured || loading}>
            {busy ? 'Verifying…' : recoveryMode ? 'Save new password' : forgot ? 'Email reset link' : signup ? 'Create account' : 'Sign in'}
          </button>
        </form>
        {!recoveryMode && <p className="login-switch">{forgot ? 'Remembered your password?' :
          signup ? 'Already registered?' : 'New to RetailGrowthAI?'}{' '}
          <button type="button" onClick={() => {
            if (forgot) setForgot(false)
            else setSignup(!signup)
            setPassword('')
            setError('')
            setMessage('')
          }}>{forgot || signup ? 'Sign in' : 'Create an account'}</button></p>}
        {!recoveryMode && !signup && !forgot && <p className="login-switch">
          <button type="button" onClick={() => {
            setForgot(true)
            setError('')
            setMessage('')
            setPassword('')
          }}>Forgot password?</button>
        </p>}
        <div className="login-security">Access is assigned after sign-in. Shop Owners see only their own businesses; verified SaaS Super Admins see platform monitoring.</div>
      </div>
    </div>
  </div>
}
