import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { getRetailClient } from '../lib/supabase.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const client = useMemo(() => getRetailClient(), [])
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [platformAdmin, setPlatformAdmin] = useState(false)
  const [platformLoading, setPlatformLoading] = useState(false)
  const [platformError, setPlatformError] = useState('')
  const [recoveryMode, setRecoveryMode] = useState(false)
  const sequence = useRef(0)

  useEffect(() => {
    let mounted = true
    const epoch = ++sequence.current
    async function restore() {
      try {
        if (client.configured) {
          // A Supabase email link returns implicit-flow tokens in the URL fragment.
          // Remove the entire fragment before any async operation, so tokens do not
          // remain in browser history or get forwarded in navigation.
          const fragment = new URLSearchParams(window.location.hash.slice(1))
          if (window.location.pathname === '/account' &&
              (fragment.has('access_token') || fragment.has('error'))) {
            window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search)
            if (fragment.has('error')) throw new Error('This email link has expired or is invalid. Request a new link.')
            const type = fragment.get('type')
            if (!['recovery', 'signup', 'email'].includes(type)) {
              throw new Error('Unrecognized email verification link.')
            }
            const verified = await client.acceptEmailLinkSession({
              access_token: fragment.get('access_token'),
              refresh_token: fragment.get('refresh_token'),
              expires_in: Number(fragment.get('expires_in')) || 3600,
              expires_at: Number(fragment.get('expires_at')) || undefined,
            })
            if (mounted && sequence.current === epoch) {
              setUser(verified)
              setRecoveryMode(type === 'recovery')
            }
          } else if (client.getStoredSession()) {
            const verified = await client.getUser()
            if (mounted && sequence.current === epoch) setUser(verified)
          }
        }
      } catch {
        if (mounted && sequence.current === epoch) {
          setError('Your session expired. Please sign in again.')
          await client.signOut()
        }
      } finally {
        if (mounted && sequence.current === epoch) setLoading(false)
      }
    }
    restore()
    return () => { mounted = false }
  }, [client])

  // Platform privilege is checked by the database on each RPC. An unresolved
  // check never grants UI access, and ordinary shop logins continue to work.
  useEffect(() => {
    let active = true
    setPlatformAdmin(false)
    setPlatformError('')
    if (!client.configured || !user) {
      setPlatformLoading(false)
      return () => { active = false }
    }
    setPlatformLoading(true)
    client.isPlatformAdmin().then((allowed) => {
      if (active) setPlatformAdmin(allowed === true)
    }).catch(() => {
      if (active) {
        setPlatformAdmin(false)
        setPlatformError('Platform access could not be verified.')
      }
    }).finally(() => {
      if (active) setPlatformLoading(false)
    })
    return () => { active = false }
  }, [client, user?.id])

  const signIn = useCallback(async (email, password) => {
    const epoch = ++sequence.current
    setError('')
    await client.signIn(email, password)
    const verified = await client.getUser()
    if (sequence.current === epoch) setUser(verified)
    return verified
  }, [client])

  const signUp = useCallback(async (email, password) => {
    setError('')
    const result = await client.signUp(email, password)
    if (client.getStoredSession()) setUser(await client.getUser())
    return result
  }, [client])

  const requestPasswordReset = useCallback(async (email) => {
    if (!email || !/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email)) {
      throw new Error('Enter a valid email address.')
    }
    await client.requestPasswordReset(email)
    // Deliberately non-enumerating even if the address does not exist.
  }, [client])

  const updateRecoveredPassword = useCallback(async (password) => {
    if (!recoveryMode) throw new Error('Open a valid password recovery email link first.')
    await client.updatePassword(password)
    ++sequence.current
    await client.signOut()
    setUser(null)
    setPlatformAdmin(false)
    setRecoveryMode(false)
  }, [client, recoveryMode])

  const signOut = useCallback(async () => {
    ++sequence.current
    await client.signOut()
    setUser(null)
    setPlatformAdmin(false)
    setRecoveryMode(false)
    setError('')
  }, [client])

  const value = useMemo(() => ({
    client, configured: client.configured, user, loading, error, recoveryMode,
    platformAdmin, platformLoading, platformError,
    signIn, signUp, signOut, requestPasswordReset, updateRecoveredPassword,
  }), [client, user, loading, error, platformAdmin, platformLoading, platformError, recoveryMode, signIn, signUp, signOut, requestPasswordReset, updateRecoveredPassword])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useRetailAuth() {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useRetailAuth must be inside AuthProvider')
  return auth
}
