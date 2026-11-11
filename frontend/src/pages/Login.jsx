import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { baseURL } from '../api/client.js'

const adminWhatsApp = (import.meta.env.VITE_ADMIN_WHATSAPP || '962795018444').replace(/\D/g, '')
const adminWhatsAppLink = `https://wa.me/${adminWhatsApp}?text=${encodeURIComponent('مرحبًا، أحتاج مساعدة في استرجاع رقم العضوية في جمعية ديرابان الخيرية.')}`

export default function Login() {
  const { loginWithMember, recoverMembershipNumber } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ full_name: '', member_id: '' })
  const [suggestions, setSuggestions] = useState([])
  const [recovery, setRecovery] = useState({ full_name: '', family_name: '' })
  const [error, setError] = useState('')
  const [result, setResult] = useState('')
  const [saving, setSaving] = useState(false)

  const setName = async (event) => {
    const full_name = event.target.value
    setForm({ full_name, member_id: '' })
    setError('')
    if (full_name.trim().length < 2) {
      setSuggestions([])
      return
    }
    try {
      const response = await fetch(`${baseURL}/auth/member-search/?q=${encodeURIComponent(full_name.trim())}`)
      const data = await response.json().catch(() => ({}))
      setSuggestions(data.results || [])
    } catch {
      setSuggestions([])
    }
  }

  const chooseSuggestion = (member) => {
    setForm({ full_name: `${member.full_name} ${member.family_name}`.trim(), member_id: member.id })
    setSuggestions([])
    setError('')
  }
  const setRecoveryField = (key) => (event) => setRecovery((previous) => ({ ...previous, [key]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    if (!form.member_id) {
      setError('اكتب جزءًا من الاسم ثم اختر اسمك من القائمة.')
      return
    }
    setSaving(true)
    try {
      await loginWithMember(form)
      const destination = location.state?.from
      navigate(destination ? `${destination.pathname}${destination.search || ''}` : '/account', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'تعذر تسجيل الدخول. اختر اسمك من القائمة وحاول مرة أخرى.')
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
            <p className="muted">اكتب جزءًا من اسمك، ثم اختر الاسم الصحيح من القائمة للدخول دون إدخال رقم العضوية.</p>
            {error && <div className="alert alert-error" role="alert">{error}</div>}
            <label>اسم العضو الكامل
              <input required autoComplete="name" value={form.full_name} onChange={setName} placeholder="مثال: مراد" />
            </label>
            {suggestions.length > 0 && <div className="member-suggestions" role="listbox" aria-label="أسماء الأعضاء المطابقة">
              {suggestions.map((member) => <button type="button" className="member-suggestion" key={member.id} onClick={() => chooseSuggestion(member)}>
                <strong>{member.full_name}</strong><span>{member.family_name}</span>
              </button>)}
            </div>}
            <button className="button button-primary button-wide" disabled={saving}>
              {saving ? 'جارٍ التحقق…' : 'تسجيل الدخول'}
            </button>
            <button type="button" className="button button-link" onClick={() => { setMode('recovery'); setError(''); setResult('') }}>
              نسيت رقم العضوية؟
            </button>
            <p className="login-footnote">إذا لم تجد بياناتك، تواصل مباشرة مع إدارة الجمعية لمساعدتك.</p>
            <Link className="button button-quiet button-wide" to="/register">تسجيل عضو جديد</Link>
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
