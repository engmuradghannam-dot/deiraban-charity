import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function CompleteProfile() {
  const { loadMember } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', family_name: '', phone: '' })
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
        <h1>أنشئ ملف عضويتك</h1>
        <p className="muted">اكتب اسمك واسم عائلتك كما هما في سجل الجمعية. سنربط حسابك تلقائياً إذا وجدنا سجلاً مطابقاً، أو ننشئ طلب عضوية جديداً لمراجعة الإدارة.</p>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
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
          {saving ? 'جارٍ حفظ بيانات العضوية…' : 'متابعة التسجيل'}
        </button>
        <p className="form-note">يمكن إضافة ودفع الاشتراكات السنوية لاحقاً من صفحة العضوية بعد اعتماد الحساب.</p>
      </form>
    </section>
  )
}
