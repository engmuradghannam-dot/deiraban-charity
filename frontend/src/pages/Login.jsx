import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

const adminWhatsApp = (import.meta.env.VITE_ADMIN_WHATSAPP || '962795018444').replace(/\D/g, '')
const adminWhatsAppLink = `https://wa.me/${adminWhatsApp}?text=${encodeURIComponent('مرحبًا، أحتاج مساعدة في استرجاع رقم العضوية في جمعية ديرابان الخيرية.')}`

export default function Login() {
  const { loginWithMember, recoverMembershipNumber } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ full_name: '', membership_number: '' })
  const [recovery, setRecovery] = useState({ full_name: '', family_name: '' })
  const [error, setError] = useState('')
  const [result, setResult] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }))
  const setRecoveryField = (key) => (event) => setRecovery((previous) => ({ ...previous, [key]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      await loginWithMember(form)
      const destination = location.state?.from
      navigate(destination ? `${destination.pathname}${destination.search || ''}` : '/account', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'تعذر تسجيل الدخول. تأكد من الاسم ورقم العضوية.')
    } finally {
      setSaving(false)
    }
  }

  const recover = async (event) => {
    event.preventDefault()
    setError('')
    setResult('')
    setSaving(true)
    try {
      const data = await recoverMembershipNumber(recovery)
      setResult(`رقم عضويتك هو: ${data.membership_number}. استخدمه ككلمة مرور عند الدخول.`)
    } catch (err) {
      setError(err.response?.data?.detail || 'لم نجد سجلًا مطابقًا. تواصل مع الإدارة.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="login-wrap">
      <div className="login-card">
        <span className="eyebrow">بوابة الأعضاء</span>
        {mode === 'login' ? (
          <form onSubmit={submit}>
            <h1>دخول الأعضاء</h1>
            <p className="muted">اكتب اسمك كما هو مسجل لدى الجمعية، واستخدم رقم العضوية ككلمة مرور.</p>
            {error && <div className="alert alert-error" role="alert">{error}</div>}
            <label>اسم العضو الكامل
              <input required autoComplete="name" value={form.full_name} onChange={set('full_name')} placeholder="مثال: محمد احمد" />
            </label>
            <label>رقم العضوية
              <input required autoComplete="current-password" value={form.membership_number} onChange={set('membership_number')} placeholder="رقم العضوية" />
            </label>
            <button className="button button-primary button-wide" disabled={saving}>
              {saving ? 'جارٍ التحقق…' : 'تسجيل الدخول'}
            </button>
            <button type="button" className="button button-link" onClick={() => { setMode('recovery'); setError(''); setResult('') }}>
              نسيت رقم العضوية؟
            </button>
            <p className="login-footnote">إذا لم تجد بياناتك، تواصل مباشرة مع إدارة الجمعية لمساعدتك.</p>
          </form>
        ) : (
          <form onSubmit={recover}>
            <h1>استرجاع رقم العضوية</h1>
            <p className="muted">اكتب الاسم واسم العائلة كما هما في سجل الجمعية للتحقق من هويتك.</p>
            {error && <div className="alert alert-error" role="alert">{error}</div>}
            {result && <div className="alert alert-success" role="status">{result}</div>}
            <label>الاسم الكامل
              <input required autoComplete="name" value={recovery.full_name} onChange={setRecoveryField('full_name')} />
            </label>
            <label>اسم العائلة
              <input required value={recovery.family_name} onChange={setRecoveryField('family_name')} />
            </label>
            <button className="button button-primary button-wide" disabled={saving}>
              {saving ? 'جارٍ البحث…' : 'استرجاع رقم العضوية'}
            </button>
            <button type="button" className="button button-link" onClick={() => { setMode('login'); setError(''); setResult('') }}>
              العودة إلى تسجيل الدخول
            </button>
            {error && <a className="button button-quiet button-wide" href={adminWhatsAppLink} target="_blank" rel="noreferrer">
              تواصل مع الإدارة عبر WhatsApp
            </a>}
            <p className="login-footnote">إذا لم تتطابق البيانات، راجع الإدارة مباشرة لتأكيد رقم العضوية.</p>
          </form>
        )}
      </div>
    </section>
  )
}
