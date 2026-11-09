import axios from 'axios'

const configuredApi = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')
const baseURL = configuredApi
  ? (configuredApi.endsWith('/api') ? configuredApi : `${configuredApi}/api`)
  : '/api'

const api = axios.create({ baseURL, timeout: 20000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && original && !original._retry && localStorage.getItem('refresh')) {
      original._retry = true
      try {
        const { data } = await axios.post(`${baseURL}/auth/token/refresh/`, {
          refresh: localStorage.getItem('refresh'),
        })
        localStorage.setItem('access', data.access)
        original.headers = original.headers || {}
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        if (window.location.pathname !== '/login') window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  },
)

export default api
