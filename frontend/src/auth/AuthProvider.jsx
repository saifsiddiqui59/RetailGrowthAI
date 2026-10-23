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
  const sequence = useRef(0)

  useEffect(() => {
    let mounted = true
    const epoch = ++sequence.current
    async function restore() {
      try {
        if (client.configured && client.getStoredSession()) {
          const verified = await client.getUser()
          if (mounted && sequence.current === epoch) setUser(verified)
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

  const signOut = useCallback(async () => {
    ++sequence.current
    await client.signOut()
    setUser(null)
    setPlatformAdmin(false)
    setError('')
  }, [client])

  const value = useMemo(() => ({
    client, configured: client.configured, user, loading, error,
    platformAdmin, platformLoading, platformError,
    signIn, signUp, signOut,
  }), [client, user, loading, error, platformAdmin, platformLoading, platformError, signIn, signUp, signOut])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useRetailAuth() {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useRetailAuth must be inside AuthProvider')
  return auth
}
