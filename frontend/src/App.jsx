import { Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import Login from './pages/Login.jsx'
import CompleteProfile from './pages/CompleteProfile.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Elections from './pages/Elections.jsx'
import ElectionDetail from './pages/ElectionDetail.jsx'
import Donations from './pages/Donations.jsx'

function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="center-screen">جارٍ التحميل...</div>
  if (!user) return <Navigate to="/login" replace />
  return children
}

function Navbar() {
  const { user, member, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null
  return (
    <nav className="navbar">
      <div className="navbar-brand">جمعية ديرابان الخيرية</div>
      <div className="navbar-links">
        <Link to="/">عضويتي</Link>
        <Link to="/elections">الانتخابات</Link>
        <Link to="/donations">التبرعات</Link>
        <span className="navbar-user">
          {member?.full_name || user.email}
        </span>
        <button className="btn btn-outline" onClick={() => { logout(); navigate('/login') }}>
          خروج
        </button>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<RequireAuth><CompleteProfile /></RequireAuth>} />
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/elections" element={<RequireAuth><Elections /></RequireAuth>} />
          <Route path="/elections/:id" element={<RequireAuth><ElectionDetail /></RequireAuth>} />
          <Route path="/donations" element={<RequireAuth><Donations /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  )
}
