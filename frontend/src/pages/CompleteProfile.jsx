import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function CompleteProfile() {
  const { loadMember } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ membership_number: '', full_name: '', family_name: '', phone: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.post('/members/register/', form)
      await loadMember()
      navigate('/account', { replace: true })
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
        <span className="eyebrow">التحقق من العضوية</span>
        <h1>اربط حسابك بسجل الجمعية</h1>
        <p className="muted">أدخل رقم العضوية واسمك كما يظهران في السجل الرسمي. لن تُتاح الانتخابات قبل مطابقة البيانات واعتماد الإدارة.</p>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        <label>رقم العضوية
          <input required autoComplete="off" value={form.membership_number} onChange={set('membership_number')} />
        </label>
        <div className="form-row">
          <label>الاسم الكامل كما في السجل
            <input required autoComplete="name" value={form.full_name} onChange={set('full_name')} />
          </label>
          <label>اسم العائلة كما في السجل
            <input required value={form.family_name} onChange={set('family_name')} />
          </label>
        </div>
        <label>رقم الهاتف <span className="optional">اختياري</span>
          <input type="tel" autoComplete="tel" value={form.phone} onChange={set('phone')} />
        </label>
        <button className="button button-primary button-wide" disabled={saving}>
          {saving ? 'جارٍ التحقق وإرسال الطلب…' : 'إرسال طلب ربط العضوية'}
        </button>
        <p className="form-note">إذا تعذر تطابق الاسم أو رقم العضوية، تواصل مع الإدارة لمراجعة السجل.</p>
      </form>
    </section>
  )
}
