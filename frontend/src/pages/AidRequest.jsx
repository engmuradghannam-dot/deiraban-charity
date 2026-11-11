import { useEffect, useRef, useState } from 'react'
import api from '../api/client.js'

// فك ترميز بيانات مستخدم جوجل من id_token بدون مكتبات إضافية (JWT عادي base64)
function decodeJwt(token) {
  try {
    const base = token.split('.')[1]
    const json = decodeURIComponent(
      atob(base.replace(/-/g, '+').replace(/_/g, '/'))
        .split('')
        .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('')
    )
    return JSON.parse(json)
  } catch {
    return {}
  }
}

export default function AidRequest() {
  const buttonRef = useRef(null)
  const [idToken, setIdToken] = useState(null)
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({
    full_name: '',
    family_name: '',
    phone: '',
    national_id: '',
    address: '',
    need_description: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState('')

  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

  useEffect(() => {
    if (!clientId || !window.google || !buttonRef.current) return

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        setIdToken(response.credential)
        const payload = decodeJwt(response.credential)
        setProfile(payload)
        setForm((f) => ({ ...f, full_name: f.full_name || payload.name || '' }))
      },
    })
    window.google.accounts.id.renderButton(buttonRef.current, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      shape: 'pill',
      locale: 'ar',
    })
  }, [clientId])

  const set = (key) => (event) => setForm((previous) => ({ ...previous, [key]: event.target.value }))

  async function submit(event) {
    event.preventDefault()
    if (!idToken) {
      setError('سجّل دخولك أولاً بحساب جوجل قبل إرسال الطلب')
      return
    }
    setError('')
    setResult('')
    setSubmitting(true)
    try {
      await api.post('/aid-requests/register/', { id_token: idToken, ...form })
      setResult('تم استلام طلبك بنجاح. سيتم التواصل معك بعد المراجعة.')
    } catch (err) {
      setError(err.response?.data?.detail || 'تعذر إرسال الطلب. حاول مجدداً.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="form-page">
      <div className="panel form-panel">
        <span className="eyebrow">خدمة المحتاجين</span>
        <h1>طلب مساعدة</h1>
        <p className="muted">
          جمعية ديرابان الخيرية — سجّل بياناتك وسيتم التواصل معك بعد مراجعة الطلب
        </p>

        {!clientId && (
          <div className="alert alert-warning" role="alert">
            تسجيل الدخول بجوجل غير مُفعّل بعد على هذا الموقع (يحتاج إعداد من إدارة الجمعية).
          </div>
        )}
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {result && <div className="alert alert-success" role="status">{result}</div>}

        {!idToken ? (
          !result && (
            <div className="google-btn-wrap">
              <div ref={buttonRef}></div>
            </div>
          )
        ) : (
          !result && (
            <form onSubmit={submit}>
              <div className="alert alert-info" role="status">
                ✓ مسجّل دخول بحساب: <strong>{profile?.email}</strong>
              </div>

              <label>الاسم الكامل
                <input required autoComplete="name" value={form.full_name} onChange={set('full_name')} />
              </label>

              <div className="form-row">
                <label>اسم العائلة
                  <input value={form.family_name} onChange={set('family_name')} />
                </label>
                <label>رقم الجوال
                  <input required dir="ltr" autoComplete="tel" value={form.phone} onChange={set('phone')} />
                </label>
              </div>

              <label>الرقم الوطني <span className="optional">اختياري</span>
                <input dir="ltr" value={form.national_id} onChange={set('national_id')} />
              </label>

              <label>العنوان
                <input value={form.address} onChange={set('address')} />
              </label>

              <label>وصف الحالة / المساعدة المطلوبة
                <textarea rows={4} required value={form.need_description} onChange={set('need_description')} />
              </label>

              <button className="button button-primary button-wide" disabled={submitting}>
                {submitting ? 'جارٍ الإرسال...' : 'إرسال الطلب'}
              </button>
            </form>
          )
        )}
      </div>
    </section>
  )
}
