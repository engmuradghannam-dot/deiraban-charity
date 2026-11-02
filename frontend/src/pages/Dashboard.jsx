import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Dashboard() {
  const { member } = useAuth()

  if (member === null) return <Navigate to="/register" replace />

  if (member.status === 'pending') {
    return (
      <div className="center-screen">
        <div className="card form-card center-text">
          <h2>طلبك قيد المراجعة ⏳</h2>
          <p className="muted">
            شكراً {member.full_name}! تم استلام طلب عضويتك وسيتم اعتماده
            من الإدارة قريباً.
          </p>
        </div>
      </div>
    )
  }

  const statusBadge = {
    approved: <span className="badge badge-green">عضو معتمد</span>,
    pending: <span className="badge badge-yellow">بانتظار الموافقة</span>,
    rejected: <span className="badge badge-red">مرفوض</span>,
  }[member.status]

  return (
    <div>
      <h2>عضويتي</h2>
      <div className="card">
        <div className="member-header">
          <div>
            <h3>{member.full_name} {statusBadge}</h3>
            <p className="muted">
              عائلة {member.family_name} — رقم العضوية:{' '}
              <strong>{member.membership_number || '—'}</strong>
            </p>
            <p className="muted small">
              {member.membership_type === 'active' ? 'عضو فاعل' : 'غير فاعل'}
              {member.phone && <> — هاتف: {member.phone}</>}
            </p>
          </div>
        </div>
      </div>

      <h3>سجل الاشتراكات السنوية</h3>
      {member.fees?.length ? (
        <table className="table">
          <thead>
            <tr><th>السنة</th><th>المبلغ</th><th>الحالة</th><th>تاريخ الدفع</th></tr>
          </thead>
          <tbody>
            {member.fees.map((f) => (
              <tr key={f.year}>
                <td>{f.year}</td>
                <td>{f.amount} د.أ</td>
                <td>{f.paid ? <span className="badge badge-green">مسدد</span> : <span className="badge badge-yellow">غير مسدد</span>}</td>
                <td>{f.paid_at || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted">لا توجد اشتراكات مسجلة بعد.</p>
      )}
    </div>
  )
}
