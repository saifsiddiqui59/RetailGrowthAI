import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getRetailClient } from '../lib/supabase.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const client = useMemo(() => getRetailClient(), [])
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    async function restore() {
      try {
        if (client.configured && client.getStoredSession()) {
          const verified = await client.getUser()
          if (mounted) setUser(verified)
        }
      } catch {
        if (mounted) setError('Your session expired. Please sign in again.')
        await client.signOut()
      } finally {
        if (mounted) setLoading(false)
      }
    }
    restore()
    return () => { mounted = false }
  }, [client])

  const signIn = useCallback(async (email, password) => {
    setError('')
    await client.signIn(email, password)
    const verified = await client.getUser()
    setUser(verified)
    return verified
  }, [client])

  const signUp = useCallback(async (email, password) => {
    setError('')
    const result = await client.signUp(email, password)
    if (client.getStoredSession()) setUser(await client.getUser())
    return result
  }, [client])

  const signOut = useCallback(async () => {
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
