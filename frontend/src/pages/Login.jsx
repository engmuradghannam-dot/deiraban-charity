import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { baseURL } from '../api/client.js'

export default function Login() {
  const { loginWithMember } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ full_name: '', member_id: '' })
  const [suggestions, setSuggestions] = useState([])
  const [error, setError] = useState('')
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

  return (
    <section className="login-wrap">
      <div className="login-card">
        <span className="eyebrow">بوابة الأعضاء</span>
        <form onSubmit={submit}>
          <h1>دخول الأعضاء</h1>
          <p className="muted">اكتب جزءًا من اسمك، ثم اختر الاسم الصحيح من القائمة للدخول.</p>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <label>اسم العضو
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
          <p className="login-footnote">إذا لم تجد اسمك، تواصل مع إدارة الجمعية لتسجيلك أو تحديث بياناتك.</p>
          <Link className="button button-quiet button-wide" to="/register">تسجيل عضو جديد</Link>
        </form>
      </div>
    </section>
  )
}
