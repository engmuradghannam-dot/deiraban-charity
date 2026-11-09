import { useState } from 'react'
import { useGoogleLogin } from '@react-oauth/google'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login({ googleConfigured }) {
  return (
    <section className="login-wrap">
      <div className="login-card">
        <span className="eyebrow">بوابة الأعضاء</span>
        <h1>دخول آمن لحسابك</h1>
        <p className="muted">استخدم حساب Google، ثم اربط ملفك برقم العضوية المسجل لدى الجمعية.</p>
        {googleConfigured ? <GoogleSignInButton /> : (
          <div className="alert alert-warning">
            تسجيل الدخول غير مهيأ بعد. يحتاج مسؤول النظام إلى ضبط معرف Google OAuth في إعدادات الواجهة.
          </div>
        )}
        <p className="login-footnote">لن يتم تمكين التصويت إلا بعد مطابقة سجل العضوية وموافقة الإدارة.</p>
      </div>
    </section>
  )
}

function GoogleSignInButton() {
  const { loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const googleLogin = useGoogleLogin({
    flow: 'auth-code',
    onSuccess: async ({ code }) => {
      setBusy(true)
      setError('')
      try {
        await loginWithGoogle(code)
        const destination = location.state?.from
        navigate(destination ? `${destination.pathname}${destination.search || ''}` : '/account', { replace: true })
      } catch {
        setError('تعذر إكمال تسجيل الدخول. تحقق من إعداد Google OAuth وحاول مرة أخرى.')
      } finally {
        setBusy(false)
      }
    },
    onError: () => setError('لم يكتمل تسجيل الدخول عبر Google.'),
  })

  return (
    <div className="login-actions">
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      <button className="button button-google" onClick={() => googleLogin()} disabled={busy}>
        <GoogleIcon /> {busy ? 'جارٍ تسجيل الدخول…' : 'المتابعة عبر Google'}
      </button>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg width="19" height="19" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3l5.7-5.7C34 6.1 29.3 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.3-.1-2.7-.4-3.9z" />
      <path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C36.9 39.2 44 34 44 24c0-1.3-.1-2.7-.4-3.9z" />
    </svg>
  )
}
