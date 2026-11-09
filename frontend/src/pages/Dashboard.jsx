import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Dashboard() {
  const { member, loading } = useAuth()
  if (loading) return <div className="loading-state" role="status">جارٍ تحميل ملف العضوية…</div>
  if (member === null) return <Navigate to="/register" replace />

  const statusBadge = {
    approved: <span className="badge badge-green">عضوية معتمدة</span>,
    pending: <span className="badge badge-yellow">بانتظار الموافقة</span>,
    rejected: <span className="badge badge-red">الطلب يحتاج مراجعة</span>,
  }[member.status] || <span className="badge badge-gray">غير محدد</span>

  return (
    <div className="content-page">
      <section className="page-intro">
        <span className="eyebrow">حساب العضو</span>
        <h1>ملف عضويتي</h1>
        <p className="muted">بياناتك المرتبطة بسجل الجمعية.</p>
      </section>

      {member.status === 'pending' && (
        <div className="alert alert-warning">
          استلمنا طلب ربط العضوية. سيظهر التصويت بعد مطابقة الإدارة لبيانات السجل واعتماد الحساب.
        </div>
      )}
      {member.status === 'rejected' && (
        <div className="alert alert-error">
          تعذر اعتماد طلب العضوية حالياً. يرجى التواصل مع إدارة الجمعية لتصحيح بيانات السجل.
        </div>
      )}

      <section className="panel member-panel">
        <div className="member-avatar" aria-hidden="true">{member.full_name?.trim().charAt(0) || 'م'}</div>
        <div className="member-details">
          <div className="member-title"><h2>{member.full_name}</h2>{statusBadge}</div>
          <p className="muted">عائلة {member.family_name} <span className="dot-separator">·</span> رقم العضوية <strong>{member.membership_number || '—'}</strong></p>
          <p className="muted">{member.membership_type === 'active' ? 'عضو فاعل حسب السجل' : 'عضوية غير فاعلة حسب السجل'}{member.phone && <> <span className="dot-separator">·</span> الهاتف: {member.phone}</>}</p>
        </div>
        <div className="eligibility-card">
          <span className={`eligibility-dot ${member.is_eligible_to_vote ? 'is-eligible' : ''}`} />
          <span>{member.is_eligible_to_vote ? 'مؤهل للتصويت' : 'التصويت غير متاح حالياً'}</span>
        </div>
      </section>

      <section className="section-heading compact-heading">
        <div><span className="eyebrow">الاشتراكات السنوية</span><h2>سجل الرسوم</h2></div>
      </section>
      {member.fees?.length ? (
        <div className="table-scroll panel">
          <table className="data-table">
            <thead><tr><th>السنة</th><th>المبلغ</th><th>الحالة</th><th>تاريخ السداد</th></tr></thead>
            <tbody>{member.fees.map((fee) => (
              <tr key={fee.year}>
                <td>{fee.year}</td><td>{fee.amount} د.أ</td>
                <td><span className={`badge ${fee.paid ? 'badge-green' : 'badge-yellow'}`}>{fee.paid ? 'مسدد' : 'غير مسدد'}</span></td>
                <td>{fee.paid_at || '—'}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : <div className="empty-panel">لا توجد رسوم سنوية مسجلة في ملفك حتى الآن.</div>}
    </div>
  )
}
