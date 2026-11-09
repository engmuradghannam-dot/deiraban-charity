import { Link } from 'react-router-dom'

export default function Home({ user, member }) {
  return (
    <div className="home-page">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">أهل ديرابان · يدٌ واحدة لأثرٍ أبقى</span>
          <h1>صوتك يشارك في القرار، وعطاؤك يصنع فرقاً.</h1>
          <p>
            منصة الجمعية لخدمة الأعضاء، وتنظيم الانتخابات، ومتابعة حملات العطاء بكل وضوح.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/elections">استعرض الانتخابات</Link>
            <Link className="button button-light" to="/donations">ساهم في حملة</Link>
          </div>
          {user && (
            <p className="welcome-note">
              {member ? `مرحباً ${member.full_name} — ${member.status === 'approved' ? 'عضويتك موثّقة.' : 'طلب عضويتك قيد المراجعة.'}` : 'أكمل ربط حسابك برقم العضوية الرسمي من صفحة عضويتي.'}
            </p>
          )}
        </div>
        <div className="hero-seal" aria-hidden="true">
          <span className="seal-ring">ديرابان</span>
          <strong>أهلٌ<br />وعطاء</strong>
          <span className="seal-line" />
          <small>جمعية خيرية</small>
        </div>
      </section>

      <section className="section-heading">
        <div>
          <span className="eyebrow">خدمات الجمعية</span>
          <h2>مشاركة واضحة وخطوات موثوقة</h2>
        </div>
        <p>كل خدمة مصممة لتسهيل المشاركة مع الحفاظ على التحقق والمراجعة.</p>
      </section>

      <div className="service-grid">
        <article className="service-card service-vote">
          <span className="service-icon" aria-hidden="true">ص</span>
          <p className="service-kicker">للأعضاء المعتمدين</p>
          <h3>انتخابات الجمعية</h3>
          <p>اطّلع على المرشحين، وسجّل صوتاً واحداً في كل انتخابات مفتوحة. لا يمكن تعديل الاختيار بعد إرساله.</p>
          <Link className="text-link" to="/elections">الذهاب إلى الانتخابات <span aria-hidden="true">←</span></Link>
        </article>
        <article className="service-card service-give">
          <span className="service-icon" aria-hidden="true">ع</span>
          <p className="service-kicker">متاحة للجميع</p>
          <h3>حملات التبرع</h3>
          <p>اختر الحملة وطريقة المساهمة. يسجل الطلب بانتظار مراجعة أمين الصندوق، ولا يُعلن كمبلغ مستلم قبل التحقق.</p>
          <Link className="text-link" to="/donations">استعراض الحملات <span aria-hidden="true">←</span></Link>
        </article>
        <article className="service-card service-member">
          <span className="service-icon" aria-hidden="true">م</span>
          <p className="service-kicker">هوية مرتبطة بالسجل</p>
          <h3>ملف العضوية</h3>
          <p>اربط حسابك برقم عضويتك واسمك كما يظهران في سجل الجمعية، ثم انتظر اعتماد الإدارة.</p>
          <Link className="text-link" to={user ? '/account' : '/login'}>{user ? 'عرض عضويتي' : 'دخول الأعضاء'} <span aria-hidden="true">←</span></Link>
        </article>
      </div>

      <aside className="trust-note">
        <span className="trust-mark" aria-hidden="true">✓</span>
        <p><strong>الوضوح قبل كل شيء.</strong> التصويت محصور في عضو فاعل معتمد، والتبرع النقدي أو البنكي يبقى قيد التحقق حتى تأكيد الاستلام من الإدارة.</p>
      </aside>
    </div>
  )
}
