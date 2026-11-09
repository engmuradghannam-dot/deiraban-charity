import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client.js'

const statusClass = { 'مفتوحة': 'badge-green', 'قادمة': 'badge-yellow', 'منتهية': 'badge-gray', 'ملغاة': 'badge-red' }
const dateTime = (value) => new Intl.DateTimeFormat('ar-JO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))

export default function Elections() {
  const [elections, setElections] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api.get('/elections/')
      .then(({ data }) => { if (active) setElections(data) })
      .catch(() => { if (active) { setElections([]); setError('تعذر تحميل الانتخابات الآن. حاول مرة أخرى لاحقاً.') } })
    return () => { active = false }
  }, [])

  if (!elections) return <div className="loading-state" role="status">جارٍ تحميل الانتخابات…</div>

  return (
    <div className="content-page">
      <section className="page-intro">
        <span className="eyebrow">صوت الجمعية</span>
        <h1>الانتخابات</h1>
        <p className="muted">تابع مواعيد الانتخابات والمرشحين، وشارك بصوتك إذا كانت عضويتك معتمدة وفاعلة.</p>
      </section>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {elections.length === 0 && !error && <div className="empty-panel">لا توجد انتخابات منشورة حالياً. ستظهر هنا عند إعلانها من إدارة الجمعية.</div>}
      <div className="election-grid">
        {elections.map((election) => (
          <article className="panel election-card" key={election.id}>
            <div className="card-topline"><span className="eyebrow">انتخابات الجمعية</span><span className={`badge ${statusClass[election.status_label] || 'badge-gray'}`}>{election.status_label}</span></div>
            <h2>{election.title}</h2>
            <p className="muted election-description">{election.description || 'تفاصيل الانتخابات والمرشحين متاحة في صفحة التفاصيل.'}</p>
            <div className="election-meta">
              <span><strong>{election.candidates.length}</strong> مرشحاً</span>
              <span><strong>{election.max_choices}</strong> اختيارات كحد أقصى</span>
            </div>
            <div className="date-range">
              <span>تبدأ: {dateTime(election.starts_at)}</span>
              <span>تنتهي: {dateTime(election.ends_at)}</span>
            </div>
            {election.has_voted && <p className="participation-note">✓ تم تسجيل مشاركتك في هذه الانتخابات</p>}
            {!election.eligible_to_vote && !election.has_voted && <p className="muted small">التصويت متاح للأعضاء الفاعلين المعتمدين فقط.</p>}
            <Link className="button button-primary button-wide" to={`/elections/${election.id}`}>
              {election.is_open && election.eligible_to_vote && !election.has_voted ? 'مراجعة المرشحين والتصويت' : 'التفاصيل والنتائج'}
            </Link>
          </article>
        ))}
      </div>
    </div>
  )
}
