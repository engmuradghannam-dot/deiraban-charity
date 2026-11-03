import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import api from '../api/client.js'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [member, setMember] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadMember = useCallback(async () => {
    try {
      const { data } = await api.get('/members/me/')
      setMember(data)
    } catch {
      setMember(null)
    }
  }, [])

  const loginWithGoogle = useCallback(async (code) => {
    const { data } = await api.post('/auth/google/', { code })
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    const me = await api.get('/auth/user/')
    setUser(me.data)
    await loadMember()
  }, [loadMember])

  const logout = useCallback(() => {
    localStorage.clear()
    setUser(null)
    setMember(null)
  }, [])

  useEffect(() => {
    (async () => {
      if (localStorage.getItem('access')) {
        try {
          const me = await api.get('/auth/user/')
          setUser(me.data)
          await loadMember()
        } catch {
          localStorage.clear()
        }
      }
      setLoading(false)
    })()
  }, [loadMember])

  return (
    <AuthContext.Provider value={{ user, member, loading, loginWithGoogle, logout, loadMember }}>
      {children}
    </AuthContext.Provider>
  )
}
