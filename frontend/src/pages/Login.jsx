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

  const googleLogin = useGoogleLogin({
    flow: 'implicit',
    onSuccess: async ({ access_token: accessToken }) => {
      setError('')
      try {
        await loginWithGoogle(accessToken)
        const destination = location.state?.from
        navigate(destination ? `${destination.pathname}${destination.search || ''}` : '/account', { replace: true })
      } catch (error) {
        const detail = error.response?.data?.detail
        setError(detail || 'تعذر إكمال تسجيل الدخول. تحقق من إعداد Google OAuth وحاول مرة أخرى.')
      }
    },
    onError: () => setError('لم يكتمل تسجيل الدخول عبر Google.'),
  })

  return (
    <div className="login-actions">
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      <button className="button button-google" onClick={() => googleLogin()}>
        المتابعة عبر Google
      </button>
    </div>
  )
}
