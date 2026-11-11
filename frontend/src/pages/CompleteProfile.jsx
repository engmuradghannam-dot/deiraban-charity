import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function CompleteProfile() {
  const { loadMember, user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', family_name: '', phone: '' })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    setMessage('')
    try {
      const { data } = await api.post('/members/register/', form)
      if (user) {
        await loadMember()
        navigate('/account', { replace: true })
      } else {
        setMessage(data.message || 'تم استلام طلب التسجيل، وستراجعه الإدارة لاحقًا.')
        setForm({ full_name: '', family_name: '', phone: '' })
      }
    } catch (err) {
      const data = err.response?.data
      const detail = data?.detail || data?.membership_number || data?.non_field_errors?.[0]
      setError(typeof detail === 'string' ? detail : 'تعذر إرسال الطلب. تأكد من البيانات وحاول مجدداً.')
    } finally {
      setSaving(false)
    }
  }

  const set = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }))

  return (
    <section className="form-page">
      <form className="panel form-panel" onSubmit={submit}>
        <span className="eyebrow">تسجيل عضو جديد</span>
        <h1>انضم إلى جمعية ديرابان</h1>
        <p className="muted">أرسل بياناتك مباشرة من الموقع. ستراجع الإدارة الطلب وتحدد رقم العضوية بعد التحقق.</p>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {message && <div className="alert alert-success" role="status">{message}</div>}
        <div className="form-row">
          <label>الاسم الكامل
            <input required autoComplete="name" value={form.full_name} onChange={set('full_name')} />
          </label>
          <label>اسم العائلة
            <input required value={form.family_name} onChange={set('family_name')} />
          </label>
        </div>
        <label>رقم الهاتف <span className="optional">اختياري</span>
          <input type="tel" autoComplete="tel" value={form.phone} onChange={set('phone')} />
        </label>
        <button className="button button-primary button-wide" disabled={saving}>
          {saving ? 'جارٍ إرسال طلب التسجيل…' : 'إرسال طلب التسجيل'}
        </button>
        {!user && <p className="form-note">بعد اعتماد الطلب من الإدارة سيُحدد لك رقم العضوية، ويمكنك استخدامه لتسجيل الدخول.</p>}
        {message && !user && <Link className="button button-quiet button-wide" to="/login">الانتقال إلى دخول الأعضاء</Link>}
      </form>
    </section>
  )
}
