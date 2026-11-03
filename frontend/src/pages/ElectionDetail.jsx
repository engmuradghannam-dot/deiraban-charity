import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client.js'

export default function ElectionDetail() {
  const { id } = useParams()
  const [election, setElection] = useState(null)
  const [results, setResults] = useState(null)
  const [selected, setSelected] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => {
    api.get(`/elections/${id}/`).then(({ data }) => setElection(data))
    api.get(`/elections/${id}/results/`).then(({ data }) => setResults(data)).catch(() => {})
  }
  useEffect(load, [id])

  if (!election) return <div className="center-screen">جارٍ التحميل...</div>

  const toggle = (cid) => {
    setMessage(''); setError('')
    setSelected((prev) => {
      if (prev.includes(cid)) return prev.filter((x) => x !== cid)
      if (prev.length >= election.max_choices) {
        setError(`يمكنك اختيار ${election.max_choices} مرشحين فقط`)
        return prev
      }
      return [...prev, cid]
    })
  }

  const vote = async () => {
    try {
      await api.post(`/elections/${id}/vote/`, { candidate_ids: selected })
      setMessage('تم تسجيل صوتك بنجاح. شكراً لمشاركتك! 🗳️')
      setSelected([])
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'حدث خطأ')
    }
  }

  const canVote = election.is_open && !election.has_voted

  return (
    <div>
      <h2>{election.title}</h2>
      <p className="muted">
        {election.description} — الحالة: {election.status_label} — المقاعد: {election.max_choices}
      </p>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {canVote && (
        <div className="alert alert-info">
          اختر حتى <strong>{election.max_choices}</strong> مرشحاً ثم اضغط "تسجيل الصوت"
          <div style={{ marginTop: 12 }}>
            <button className="btn btn-primary" disabled={selected.length === 0} onClick={vote}>
              تسجيل الصوت ({selected.length}/{election.max_choices})
            </button>
          </div>
        </div>
      )}
      {election.has_voted && <div className="alert alert-success">✓ لقد شاركت في هذه الانتخابات</div>}

      <div className="grid">
        {election.candidates.map((c) => (
          <div
            key={c.id}
            className={`card candidate ${selected.includes(c.id) ? 'selected' : ''}`}
            onClick={() => canVote && toggle(c.id)}
          >
            {c.photo && <img src={c.photo} alt={c.name} className="candidate-photo" />}
            <h4>{c.name}</h4>
            <p className="muted small">عائلة {c.family_name}</p>
            {c.bio && <p className="small">{c.bio}</p>}
            {selected.includes(c.id) && <span className="badge badge-green">✓ مختار</span>}
          </div>
        ))}
      </div>

      {results && !canVote && (
        <>
          <h3>النتائج ({results.total_ballots} صوتاً)</h3>
          <table className="table">
            <thead><tr><th>المرشح</th><th>الأصوات</th><th>النسبة</th></tr></thead>
            <tbody>
              {results.results.map((r) => (
                <tr key={r.candidate_id}>
                  <td>{r.name}</td>
                  <td>{r.votes}</td>
                  <td>
                    <div className="progress">
                      <div
                        className="progress-bar"
                        style={{ width: `${results.total_ballots ? (r.votes / results.total_ballots) * 100 : 0}%` }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
