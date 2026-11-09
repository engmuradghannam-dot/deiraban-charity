import { useEffect, useState } from 'react'
import api from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

const statusText = { pending: 'بانتظار التحقق', completed: 'تم تأكيد الاستلام', failed: 'غير مكتمل', refunded: 'مسترجع' }
const amountFormat = (amount) => new Intl.NumberFormat('ar-JO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(amount) || 0)

export default function Donations() {
  const { user, member } = useAuth()
  const [campaigns, setCampaigns] = useState(null)
  const [mine, setMine] = useState([])
  const [form, setForm] = useState({ campaign: '', amount: '', method: 'bank', donor_name: '', donor_phone: '', notes: '' })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/donations/campaigns/')
      setCampaigns(data)
      if (user) {
        try {
          const donations = await api.get('/donations/mine/')
          setMine(donations.data)
        } catch {
          setMine([])
        }
      } else {
        setMine([])
      }
    } catch {
      setCampaigns([])
      setError('تعذر تحميل حملات التبرع الآن.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [user])

  const set = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    setSubmitting(true)
    try {
      const payload = {
        ...form,
        campaign: form.campaign ? Number(form.campaign) : null,
        donor_name: member?.full_name || form.donor_name.trim(),
      }
      await api.post('/donations/', payload)
      setMessage('استلمنا طلب التبرع. سيبقى قيد التحقق حتى تؤكد الإدارة استلام المبلغ؛ لم يتم خصم أي مبلغ إلكترونياً.')
      setForm((previous) => ({ ...previous, amount: '', notes: '' }))
      await load()
    } catch (err) {
      const data = err.response?.data
      const detail = data?.detail || data?.amount?.[0] || data?.method?.[0] || data?.campaign?.[0] || data?.donor_name?.[0]
      setError(typeof detail === 'string' ? detail : 'تعذر تسجيل الطلب. راجع البيانات وحاول مجدداً.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="content-page">
      <section className="page-intro donations-intro">
        <span className="eyebrow">باب الخير مفتوح</span>
        <h1>حملات التبرع</h1>
        <p className="muted">اختر الحملة وطريقة المساهمة. تُراجع الطلبات من أمين الصندوق قبل احتسابها ضمن إجمالي التبرعات.</p>
      </section>
      {message && <div className="alert alert-success" role="status">{message}</div>}
      {error && <div className="alert alert-error" role="alert">{error}</div>}

      {loading && !campaigns ? <div className="loading-state">جارٍ تحميل الحملات…</div> : (
        <>
          {!campaigns?.length && <div className="empty-panel">لا توجد حملات مفعّلة حالياً، ويمكنك تقديم طلب تبرع عام.</div>}
          <div className="campaign-grid">
            {campaigns?.map((campaign) => (
              <article className="panel campaign-card" key={campaign.id}>
                <div className="campaign-symbol" aria-hidden="true">ع</div>
                <span className="eyebrow">حملة نشطة</span>
                <h2>{campaign.title}</h2>
                <p className="muted">{campaign.description || 'ساهم في دعم أعمال الجمعية ومبادراتها.'}</p>
                {campaign.goal_amount && (
                  <div className="campaign-progress">
                    <div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(Number(campaign.percent) || 0, 100)}%` }} /></div>
                    <div className="campaign-total"><span>تم تأكيد {amountFormat(campaign.collected)} د.أ</span><span>الهدف {amountFormat(campaign.goal_amount)} د.أ</span></div>
                  </div>
                )}
                <button className="text-link button-link" onClick={() => setForm((previous) => ({ ...previous, campaign: String(campaign.id) }))}>اختيار هذه الحملة <span aria-hidden="true">←</span></button>
              </article>
            ))}
          </div>

          <section className="panel donation-form-panel" id="donate">
            <div className="form-heading">
              <span className="eyebrow">طلب مساهمة</span>
              <h2>ساهم الآن</h2>
              <p className="muted">طرق المساهمة الحالية: نقداً أو حوالة بنكية. لا توجد بوابة دفع إلكتروني مفعّلة.</p>
            </div>
            <form onSubmit={submit}>
              <div className="form-row">
                <label>الحملة
                  <select value={form.campaign} onChange={set('campaign')}>
                    <option value="">تبرع عام</option>
                    {campaigns?.map((campaign) => <option key={campaign.id} value={campaign.id}>{campaign.title}</option>)}
                  </select>
                </label>
                <label>المبلغ (دينار أردني) *
                  <input required type="number" min="0.01" step="0.01" inputMode="decimal" value={form.amount} onChange={set('amount')} />
                </label>
              </div>
              <div className="form-row">
                <label>طريقة المساهمة
                  <select value={form.method} onChange={set('method')}>
                    <option value="bank">حوالة بنكية — بانتظار المطابقة</option>
                    <option value="cash">نقداً لدى أمين الصندوق — بانتظار التأكيد</option>
                  </select>
                </label>
                {!member && <label>اسم المتبرع *
                  <input required maxLength="255" value={form.donor_name} onChange={set('donor_name')} />
                </label>}
              </div>
              <div className="form-row">
                <label>رقم الهاتف <span className="optional">اختياري</span>
                  <input type="tel" maxLength="20" value={form.donor_phone} onChange={set('donor_phone')} />
                </label>
                <label>مرجع الحوالة أو ملاحظات <span className="optional">اختياري</span>
                  <input maxLength="255" value={form.notes} onChange={set('notes')} placeholder="مثال: رقم العملية البنكية" />
                </label>
              </div>
              <div className="donation-disclaimer">للحصول على بيانات التحويل أو ترتيب تسليم النقد، تواصل مع أمين الصندوق. إرسال النموذج يسجل نية التبرع فقط؛ لا يخصم أي مبلغ ولا يؤكد استلامه.</div>
              <button className="button button-primary" disabled={submitting}>{submitting ? 'جارٍ تسجيل الطلب…' : 'إرسال طلب التبرع'}</button>
            </form>
          </section>

          {user && (
            <section className="history-section">
              <div className="section-heading compact-heading"><div><span className="eyebrow">لصاحب الحساب</span><h2>سجل تبرعاتي</h2></div></div>
              {mine.length ? (
                <div className="table-scroll panel">
                  <table className="data-table">
                    <thead><tr><th>التاريخ</th><th>الحملة</th><th>المبلغ</th><th>الطريقة</th><th>الحالة</th></tr></thead>
                    <tbody>{mine.map((donation) => (
                      <tr key={donation.id}>
                        <td>{new Date(donation.created_at).toLocaleDateString('ar-JO')}</td>
                        <td>{donation.campaign_title}</td>
                        <td>{amountFormat(donation.amount)} {donation.currency}</td>
                        <td>{donation.method_label}</td>
                        <td><span className={`badge ${donation.status === 'completed' ? 'badge-green' : donation.status === 'pending' ? 'badge-yellow' : 'badge-gray'}`}>{statusText[donation.status] || donation.status_label}</span></td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              ) : <div className="empty-panel">لا توجد طلبات تبرع مرتبطة بحسابك بعد.</div>}
            </section>
          )}
        </>
      )}
    </div>
  )
}
