import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api/client.js'

export default function ElectionDetail() {
  const { id } = useParams()
  const [election, setElection] = useState(null)
  const [results, setResults] = useState(null)
  const [selected, setSelected] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    const { data } = await api.get(`/elections/${id}/`)
    setElection(data)
    try {
      const resultResponse = await api.get(`/elections/${id}/results/`)
      setResults(resultResponse.data)
    } catch {
      setResults(null)
    }
  }, [id])

  useEffect(() => {
    let active = true
    setElection(null)
    setError('')
    Promise.resolve().then(load).catch(() => { if (active) setError('تعذر تحميل بيانات الانتخابات.') })
    return () => { active = false }
  }, [load])

  const canVote = Boolean(election?.is_open && election?.eligible_to_vote && !election?.has_voted)
  const selectedCandidates = useMemo(
    () => election?.candidates.filter((candidate) => selected.includes(candidate.id)) || [],
    [election, selected],
  )

  const toggle = (candidateId) => {
    setMessage('')
    setError('')
    setConfirming(false)
    setSelected((previous) => {
      if (previous.includes(candidateId)) return previous.filter((idValue) => idValue !== candidateId)
      if (previous.length >= election.max_choices) {
        setError(`يمكنك اختيار ${election.max_choices} مرشحين كحد أقصى.`)
        return previous
      }
      return [...previous, candidateId]
    })
  }

  const submitVote = async () => {
    setSubmitting(true)
    setError('')
    try {
      await api.post(`/elections/${id}/vote/`, { candidate_ids: selected })
      setMessage('تم تسجيل صوتك بنجاح. لا يمكن تغيير الاختيار بعد إرساله.')
      setSelected([])
      setConfirming(false)
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.candidate_ids?.[0] || 'تعذر تسجيل الصوت.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!election && !error) return <div className="loading-state" role="status">جارٍ تحميل تفاصيل الانتخابات…</div>
  if (error && !election) return <div className="content-page"><div className="alert alert-error">{error}</div><Link className="text-link" to="/elections">العودة إلى قائمة الانتخابات</Link></div>

  return (
    <div className="content-page">
      <Link className="back-link" to="/elections">← العودة إلى الانتخابات</Link>
      <section className="page-intro election-intro">
        <span className="eyebrow">{election.status_label}</span>
        <h1>{election.title}</h1>
        {election.description && <p className="muted">{election.description}</p>}
        <p className="muted small">يمكن اختيار حتى {election.max_choices} مرشحين. يُسجّل صوت واحد لهذا الحساب ولا يمكن تغييره.</p>
      </section>

      {message && <div className="alert alert-success" role="status">{message}</div>}
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {election.has_voted && <div className="alert alert-success">تم تسجيل مشاركتك. شكراً لمساهمتك في قرار الجمعية.</div>}
      {election.is_open && !election.eligible_to_vote && !election.has_voted && (
        <div className="alert alert-warning">التصويت متاح للأعضاء الفاعلين المعتمدين المرتبطين بسجل الجمعية. أكمل ربط عضويتك أو تواصل مع الإدارة.</div>
      )}
      {!election.is_open && election.status_label !== 'منتهية' && <div className="alert alert-info">التصويت غير مفتوح حالياً.</div>}

      {canVote && (
        <div className="vote-toolbar panel">
          <div><strong>اختر مرشحيك</strong><span className="muted small">حدد حتى {election.max_choices} خيارات</span></div>
          <button className="button button-primary" disabled={!selected.length || submitting} onClick={() => { setError(''); setConfirming(true) }}>
            مراجعة الاختيار ({selected.length}/{election.max_choices})
          </button>
        </div>
      )}

      {confirming && canVote && (
        <section className="confirmation-panel" aria-live="polite">
          <div>
            <span className="eyebrow">مراجعة نهائية</span>
            <h2>تأكد من اختياراتك قبل الإرسال</h2>
            <p>بعد تأكيد التصويت لا يمكن تعديل الورقة أو إعادة التصويت في هذه الانتخابات.</p>
            <strong>{selectedCandidates.map((candidate) => candidate.name).join('، ')}</strong>
          </div>
          <div className="confirmation-actions">
            <button className="button button-primary" onClick={submitVote} disabled={submitting}>{submitting ? 'جارٍ التسجيل…' : 'تأكيد التصويت النهائي'}</button>
            <button className="button button-quiet" onClick={() => setConfirming(false)} disabled={submitting}>العودة للتعديل</button>
          </div>
        </section>
      )}

      <div className="candidate-grid">
        {election.candidates.map((candidate) => {
          const isSelected = selected.includes(candidate.id)
          return (
            <button
              type="button"
              key={candidate.id}
              className={`candidate-card panel ${isSelected ? 'selected' : ''} ${canVote ? 'clickable' : ''}`}
              onClick={() => canVote && toggle(candidate.id)}
              disabled={!canVote || confirming || submitting}
              aria-pressed={isSelected}
            >
              {candidate.photo ? <img src={candidate.photo} alt="" className="candidate-photo" /> : <span className="candidate-avatar" aria-hidden="true">{candidate.name?.trim().charAt(0) || 'م'}</span>}
              <span className="candidate-info"><strong>{candidate.name}</strong><small>عائلة {candidate.family_name}</small>{candidate.bio && <span className="candidate-bio">{candidate.bio}</span>}</span>
              {isSelected && <span className="selected-badge">✓ مختار</span>}
            </button>
          )
        })}
      </div>

      {results && (
        <section className="results-section">
          <div className="section-heading compact-heading">
            <div><span className="eyebrow">الفرز المعلن</span><h2>النتائج</h2></div>
            <p>{results.total_ballots} ورقة اقتراع · {results.total_selections} اختياراً</p>
          </div>
          {results.results.length ? (
            <div className="results-list panel">
              {results.results.map((result) => (
                <div className="result-row" key={result.candidate_id}>
                  <div className="result-label"><strong>{result.name}</strong><span>{result.votes} صوت · {result.percent}%</span></div>
                  <div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(Number(result.percent) || 0, 100)}%` }} /></div>
                </div>
              ))}
            </div>
          ) : <div className="empty-panel">لم تُسجّل أصوات في هذه الانتخابات بعد.</div>}
        </section>
      )}
    </div>
  )
}
