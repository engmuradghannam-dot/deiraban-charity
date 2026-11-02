import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client.js'

const statusClass = { 'مفتوحة': 'badge-green', 'قادمة': 'badge-yellow', 'منتهية': 'badge-gray', 'ملغاة': 'badge-red' }

export default function Elections() {
  const [elections, setElections] = useState(null)

  useEffect(() => {
    api.get('/elections/').then(({ data }) => setElections(data)).catch(() => setElections([]))
  }, [])

  if (!elections) return <div className="center-screen">جارٍ التحميل...</div>

  return (
    <div>
      <h2>الانتخابات</h2>
      {elections.length === 0 && <p className="muted">لا توجد انتخابات حالياً.</p>}
      <div className="grid">
        {elections.map((e) => (
          <div className="card" key={e.id}>
            <div className="card-title-row">
              <h3>{e.title}</h3>
              <span className={`badge ${statusClass[e.status_label] || 'badge-gray'}`}>
                {e.status_label}
              </span>
            </div>
            <p className="muted small">{e.description?.slice(0, 120)}</p>
            <p className="small">
              المرشحون: {e.candidates.length} — عدد المقاعد: {e.max_choices}
            </p>
            <p className="muted small">
              {new Date(e.starts_at).toLocaleString('ar-JO')} — {new Date(e.ends_at).toLocaleString('ar-JO')}
            </p>
            {e.has_voted && <p className="badge badge-green">✓ صوّتت</p>}
            <Link className="btn btn-primary" to={`/elections/${e.id}`}>
              {e.is_open && !e.has_voted ? 'التصويت الآن' : 'التفاصيل والنتائج'}
            </Link>
          </div>
        ))}
      </div>
    </div>
  )
}
