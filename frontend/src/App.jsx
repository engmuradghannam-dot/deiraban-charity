import { BrowserRouter, Link, NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CompleteProfile from './pages/CompleteProfile.jsx'
import Donations from './pages/Donations.jsx'
import ElectionDetail from './pages/ElectionDetail.jsx'
import Elections from './pages/Elections.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'

export default function App() {
  const application = (
    <AuthProvider>
      <BrowserRouter>
        <ApplicationShell />
      </BrowserRouter>
    </AuthProvider>
  )

  return application
}

function ApplicationShell() {
  const { user, member, loading, logout } = useAuth()

  return (
    <div className="site-shell" dir="rtl">
      <header className="site-header">
        <Link className="brand-lockup" to="/" aria-label="جمعية ديرابان الخيرية — الصفحة الرئيسية">
          <span className="brand-mark" aria-hidden="true">د</span>
          <span>
            <strong>جمعية ديرابان الخيرية</strong>
            <small>خدمة المجتمع بالثقة والمشاركة</small>
          </span>
        </Link>
        <nav className="site-nav" aria-label="القائمة الرئيسية">
          <NavLink to="/elections" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>الانتخابات</NavLink>
          <NavLink to="/donations" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>التبرعات</NavLink>
          {user && <NavLink to="/account" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>عضويتي</NavLink>}
          {!loading && (user
            ? <button className="nav-button" onClick={logout}>تسجيل الخروج</button>
            : <NavLink className="nav-login" to="/login">دخول الأعضاء</NavLink>)}
        </nav>
      </header>

      <main className="page-content">
        <Routes>
          <Route path="/" element={<Home user={user} member={member} />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<RequireAuth><CompleteProfile /></RequireAuth>} />
          <Route path="/account" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/elections" element={<RequireAuth><Elections /></RequireAuth>} />
          <Route path="/elections/:id" element={<RequireAuth><ElectionDetail /></RequireAuth>} />
          <Route path="/donations" element={<Donations />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <footer className="site-footer">
        <span>جمعية ديرابان الخيرية</span>
        <span>التصويت للأعضاء المعتمدين — والتبرعات قيد التحقق حتى تأكيد استلامها</span>
      </footer>
    </div>
  )
}

function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="loading-state" role="status">جارٍ التحقق من الجلسة…</div>
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}
