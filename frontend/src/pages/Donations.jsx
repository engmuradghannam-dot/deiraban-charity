import { useEffect, useState } from 'react'
import api from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function Donations() {
  const { user, member } = useAuth()
  const [campaigns, setCampaigns] = useState([])
  const [mine, setMine] = useState([])
  const [form, setForm] = useState({
    campaign: '', amount: '', method: 'cash',
    donor_name: '', donor_phone: '', notes: '',
  })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => {
    api.get('/donations/campaigns/').then(({ data }) => setCampaigns(data))
    if (user) api.get('/donations/mine/').then(({ data }) => setMine(data)).catch(() => {})
  }
  useEffect(load, [user])

  const submit = async (e) => {
    e.preventDefault()
    setMessage(''); setError('')
    try {
      const payload = { ...form, campaign: form.campaign || null }
      await api.post('/donations/', payload)
      setMessage('شكراً لتبرعك! تم تسجيل مساهمتك 💚')
      setForm({ ...form, amount: '', notes: '' })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'حدث خطأ')
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div>
      <h2>التبرعات</h2>
      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <div className="grid">
        {campaigns.map((c) => (
          <div className="card" key={c.id}>
            <h3>{c.title}</h3>
            <p className="muted small">{c.description}</p>
            {c.goal_amount && (
              <>
                <div className="progress">
                  <div className="progress-bar" style={{ width: `${Math.min(c.percent, 100)}%` }} />
                </div>
                <p className="small">
                  جُمع {c.collected} من {c.goal_amount} د.أ ({c.percent}%)
                </p>
              </>
            )}
          </div>
        ))}
      </div>

      <div className="card form-card">
        <h3>تبرع الآن</h3>
        <form onSubmit={submit}>
          <div className="row">
            <label>الحملة
              <select value={form.campaign} onChange={set('campaign')}>
                <option value="">تبرع عام</option>
                {campaigns.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
              </select>
            </label>
            <label>المبلغ (د.أ) *
              <input required type="number" min="1" step="0.5" value={form.amount} onChange={set('amount')} />
            </label>
          </div>
          <div className="row">
            <label>طريقة الدفع
              <select value={form.method} onChange={set('method')}>
                <option value="cash">نقدي (يسجّله أمين الصندوق)</option>
                <option value="bank">حوالة بنكية</option>
                <option value="online">دفع إلكتروني (قريباً)</option>
              </select>
            </label>
            {!member && (
              <label>اسمك (للزوار) *
                <input required={!user} value={form.donor_name} onChange={set('donor_name')} />
              </label>
            )}
          </div>
          <label>ملاحظات
            <input value={form.notes} onChange={set('notes')} placeholder="اختياري" />
          </label>
          <button className="btn btn-primary">تبرع</button>
        </form>
      </div>

      {mine.length > 0 && (
        <>
          <h3>تبرعاتي</h3>
          <table className="table">
            <thead><tr><th>التاريخ</th><th>الحملة</th><th>المبلغ</th><th>الحالة</th></tr></thead>
            <tbody>
              {mine.map((d) => (
                <tr key={d.id}>
                  <td>{new Date(d.created_at).toLocaleDateString('ar-JO')}</td>
                  <td>{d.campaign_title}</td>
                  <td>{d.amount} {d.currency}</td>
                  <td>{d.status === 'completed' ? '✓ مكتمل' : d.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
