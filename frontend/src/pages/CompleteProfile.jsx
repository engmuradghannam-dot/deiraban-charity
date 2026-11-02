import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function CompleteProfile() {
  const { loadMember } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '', family_name: '', national_id: '', phone: '',
    membership_type: 'active', notes: '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.post('/members/register/', form)
      await loadMember()
      navigate('/')
    } catch (err) {
      const d = err.response?.data
      setError(d?.detail || JSON.stringify(d) || 'حدث خطأ')
    } finally {
      setSaving(false)
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="center-screen">
      <form className="card form-card" onSubmit={submit}>
        <h2>إكمال بيانات العضوية</h2>
        <p className="muted">أدخل بياناتك كما وردت في سجلات الجمعية</p>
        {error && <div className="alert alert-error">{error}</div>}
        <label>الاسم الرباعي
          <input required value={form.full_name} onChange={set('full_name')} />
        </label>
        <label>اسم العائلة
          <input required value={form.family_name} onChange={set('family_name')} />
        </label>
        <div className="row">
          <label>الرقم الوطني
            <input value={form.national_id} onChange={set('national_id')} />
          </label>
          <label>رقم الهاتف
            <input value={form.phone} onChange={set('phone')} />
          </label>
        </div>
        <label>صفة العضوية
          <select value={form.membership_type} onChange={set('membership_type')}>
            <option value="active">عضو فاعل</option>
            <option value="inactive">غير فاعل</option>
          </select>
        </label>
        <label>ملاحظات
          <input value={form.notes} onChange={set('notes')} placeholder="اختياري" />
        </label>
        <button className="btn btn-primary" disabled={saving}>
          {saving ? 'جارٍ الإرسال...' : 'إرسال طلب العضوية'}
        </button>
        <p className="muted small">سيتم اعتماد عضويتك من الإدارة قبل تمكّنك من التصويت.</p>
      </form>
    </div>
  )
}
