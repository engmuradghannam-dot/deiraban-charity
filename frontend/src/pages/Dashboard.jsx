import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import api from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function Dashboard() {
  const { member, loading, loadMember } = useAuth()
  const [form, setForm] = useState({ national_id: '', phone: '', phone_secondary: '', email: '' })
  const [profilePhoto, setProfilePhoto] = useState(null)
  const [photoUrl, setPhotoUrl] = useState('')
  const [editing, setEditing] = useState(false)
  const [idScan, setIdScan] = useState(null)
  const [familyBookScan, setFamilyBookScan] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (member) {
      setForm({
        national_id: member.national_id || '',
        phone: member.phone || '',
        phone_secondary: member.phone_secondary || '',
        email: member.email || '',
      })
      if (!member.national_id && !member.phone && !member.email && !member.has_id_scan && !member.has_profile_photo) {
        setEditing(true)
      }
    }
  }, [member])

  useEffect(() => {
    let objectUrl = ''
    if (member?.has_profile_photo) {
      api.get('/members/me/profile-photo/', { responseType: 'blob' })
        .then(({ data }) => {
          objectUrl = URL.createObjectURL(data)
          setPhotoUrl(objectUrl)
        })
        .catch(() => setPhotoUrl(''))
    } else {
      setPhotoUrl('')
    }
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [member?.has_profile_photo])

  if (loading) return <div className="loading-state" role="status">جارٍ تحميل ملف العضوية…</div>
  if (member === null) return <Navigate to="/register" replace />

  const statusBadge = {
    approved: <span className="badge badge-green">عضوية معتمدة</span>,
    pending: <span className="badge badge-yellow">بانتظار الموافقة</span>,
    rejected: <span className="badge badge-red">الطلب يحتاج مراجعة</span>,
  }[member.status] || <span className="badge badge-gray">غير محدد</span>

  const set = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }))

  const savePersonalData = async (event) => {
    event.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')
    const data = new FormData()
    Object.entries(form).forEach(([key, value]) => data.append(key, value))
    if (idScan) data.append('id_scan', idScan)
    if (familyBookScan) data.append('family_book_scan', familyBookScan)
    if (profilePhoto) data.append('profile_photo', profilePhoto)
    try {
      await api.patch('/members/me/personal/', data)
      await loadMember()
      setIdScan(null)
      setFamilyBookScan(null)
      setProfilePhoto(null)
      setEditing(false)
      event.target.reset()
      setMessage('تم حفظ بياناتك الشخصية ورفع الوثائق الخاصة بنجاح.')
    } catch (err) {
      setError(err.response?.data?.detail || 'تعذر حفظ البيانات. تأكد من الملفات وحاول مرة أخرى.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="content-page">
      <section className="page-intro">
        <span className="eyebrow">حساب العضو</span>
        <h1>ملف عضويتي</h1>
        <p className="muted">بياناتك المرتبطة بسجل الجمعية.</p>
      </section>

      {member.status === 'pending' && <div className="alert alert-warning">استلمنا طلب ربط العضوية. سيظهر التصويت بعد مطابقة الإدارة لبيانات السجل واعتماد الحساب.</div>}
      {member.status === 'rejected' && <div className="alert alert-error">تعذر اعتماد طلب العضوية حالياً. يرجى التواصل مع إدارة الجمعية لتصحيح بيانات السجل.</div>}

      <section className="panel member-panel">
        <div className="member-avatar profile-avatar">
          {photoUrl ? <img src={photoUrl} alt={`الصورة الشخصية لـ ${member.full_name}`} /> : (member.full_name?.trim().charAt(0) || 'م')}
        </div>
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

      <section className="section-heading compact-heading"><div><span className="eyebrow">البيانات الشخصية</span><h2>تحديث ملفي</h2></div></section>
      {message && <div className="alert alert-success" role="status">{message}</div>}
      {!editing ? <section className="panel personal-summary">
        <div className="summary-grid">
          <span><small>الرقم الوطني</small><strong>{member.national_id || 'غير مضاف'}</strong></span>
          <span><small>البريد الإلكتروني</small><strong>{member.email || 'غير مضاف'}</strong></span>
          <span><small>رقم التواصل</small><strong>{member.phone || 'غير مضاف'}</strong></span>
          <span><small>الوثائق</small><strong>{member.has_id_scan || member.has_family_book_scan ? 'مرفوعة' : 'غير مرفوعة'}</strong></span>
        </div>
        <button type="button" className="button button-secondary" onClick={() => setEditing(true)}>تحديث البيانات</button>
      </section> : <form className="panel form-panel personal-data-form" onSubmit={savePersonalData}>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        <div className="form-row">
          <label>الرقم الوطني
            <input value={form.national_id} onChange={set('national_id')} inputMode="numeric" autoComplete="off" />
          </label>
          <label>البريد الإلكتروني
            <input type="email" value={form.email} onChange={set('email')} autoComplete="email" />
          </label>
        </div>
        <div className="form-row">
          <label>رقم التواصل الأساسي
            <input type="tel" value={form.phone} onChange={set('phone')} autoComplete="tel" />
          </label>
          <label>رقم تواصل إضافي <span className="optional">اختياري</span>
            <input type="tel" value={form.phone_secondary} onChange={set('phone_secondary')} />
          </label>
        </div>
        <div className="form-row">
          <label>صورة الهوية <span className="optional">JPG أو PNG أو PDF</span>
            <input type="file" accept="image/*,.pdf" onChange={(event) => setIdScan(event.target.files?.[0] || null)} />
            {member.has_id_scan && <small className="muted">تم رفع صورة هوية سابقًا.</small>}
          </label>
          <label>صورة دفتر العائلة <span className="optional">JPG أو PNG أو PDF</span>
            <input type="file" accept="image/*,.pdf" onChange={(event) => setFamilyBookScan(event.target.files?.[0] || null)} />
            {member.has_family_book_scan && <small className="muted">تم رفع دفتر العائلة سابقًا.</small>}
          </label>
        </div>
        <label>الصورة الشخصية <span className="optional">JPG أو PNG أو WEBP</span>
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setProfilePhoto(event.target.files?.[0] || null)} />
          {member.has_profile_photo && <small className="muted">تم رفع صورة شخصية سابقًا.</small>}
        </label>
        <p className="form-note">الوثائق خاصة ولا تظهر للأعضاء الآخرين. الحد الأقصى للملف 10 ميغابايت.</p>
        <div className="form-actions"><button className="button button-primary" disabled={saving}>{saving ? 'جارٍ الحفظ…' : 'حفظ البيانات والوثائق'}</button><button type="button" className="button button-secondary" onClick={() => setEditing(false)} disabled={saving}>إلغاء</button></div>
      </form>}

      <section className="section-heading compact-heading"><div><span className="eyebrow">الاشتراكات السنوية</span><h2>سجل الرسوم</h2></div></section>
      {member.fees?.length ? (
        <div className="table-scroll panel">
          <table className="data-table">
            <thead><tr><th>السنة</th><th>البيان المسجل</th><th>الحالة</th><th>تاريخ السداد</th></tr></thead>
            <tbody>{member.fees.map((fee) => (
              <tr key={fee.year}>
                <td>{fee.label || fee.year}</td><td>{fee.recorded_value || fee.amount || '—'}</td>
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
