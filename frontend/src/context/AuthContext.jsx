import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api from '../api/client.js'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function clearAuthTokens() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
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

  const loginWithGoogle = useCallback(async (accessToken) => {
    const { data } = await api.post('/auth/google/', { access_token: accessToken })
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    const me = await api.get('/auth/user/')
    setUser(me.data)
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
          const me = await api.get('/auth/user/')
          if (!mounted) return
          setUser(me.data)
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
