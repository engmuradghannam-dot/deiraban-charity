import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api, { baseURL } from '../api/client.js'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function clearAuthTokens() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
  localStorage.removeItem('user_email')
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [member, setMember] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadMember = useCallback(async () => {
    try {
      const { data } = await api.get('/members/me/')
      setMember(data)
      return data
    } catch (error) {
      if (error.response?.status === 404) {
        setMember(null)
        return null
      }
      throw error
    }
  }, [])

  const loginWithGoogle = useCallback(async (googleToken) => {
    const response = await fetch(`${baseURL}/auth/google/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(googleToken),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const error = new Error(data.detail || 'Google login failed')
      error.response = { status: response.status, data }
      throw error
    }
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    if (data.user) {
      localStorage.setItem('user_email', data.user.email || '')
      setUser(data.user)
    }
    await loadMember().catch(() => null)
  }, [loadMember])

  const logout = useCallback(() => {
    clearAuthTokens()
    setUser(null)
    setMember(null)
  }, [])

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        if (localStorage.getItem('access')) {
          if (!mounted) return
          setUser({ email: localStorage.getItem('user_email') || '' })
          await loadMember().catch(() => null)
        }
      } catch {
        clearAuthTokens()
        if (mounted) {
          setUser(null)
          setMember(null)
        }
      } finally {
        if (mounted) setLoading(false)
      }
    })()
    return () => { mounted = false }
  }, [loadMember])

  return (
    <AuthContext.Provider value={{ user, member, loading, loginWithGoogle, logout, loadMember }}>
      {children}
    </AuthContext.Provider>
  )
}
