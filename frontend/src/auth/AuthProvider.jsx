import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { getRetailClient } from '../lib/supabase.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const client = useMemo(() => getRetailClient(), [])
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
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
    setError('')
  }, [client])

  const value = useMemo(() => ({
    client, configured: client.configured, user, loading, error,
    signIn, signUp, signOut,
  }), [client, user, loading, error, signIn, signUp, signOut])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useRetailAuth() {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useRetailAuth must be inside AuthProvider')
  return auth
}
