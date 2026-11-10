import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { loginWithMember } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ full_name: '', membership_number: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      await loginWithMember(form)
      const destination = location.state?.from
      navigate(destination ? `${destination.pathname}${destination.search || ''}` : '/account', { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(detail || 'تعذر تسجيل الدخول. تأكد من الاسم ورقم العضوية.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <span className="eyebrow">بوابة الأعضاء</span>
        <h1>دخول الأعضاء</h1>
        <p className="muted">اكتب اسمك كما هو مسجل لدى الجمعية، واستخدم رقم العضوية ككلمة مرور.</p>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        <label>اسم العضو الكامل
          <input required autoComplete="name" value={form.full_name} onChange={set('full_name')} placeholder="مثال: محمد أحمد" />
        </label>
        <label>رقم العضوية
          <input required autoComplete="current-password" value={form.membership_number} onChange={set('membership_number')} placeholder="رقم العضوية" />
        </label>
        <button className="button button-primary button-wide" disabled={saving}>
          {saving ? 'جارٍ التحقق…' : 'تسجيل الدخول'}
        </button>
        <p className="login-footnote">إذا لم يكن لديك رقم عضوية، تواصل مع الإدارة لتسجيلك أولاً.</p>
      </form>
    </section>
  )
}
