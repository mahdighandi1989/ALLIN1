'use client'

// Official Bank Saderat (UAE — Regional Office) LETTER (نامه). Every element is
// absolutely positioned at the EXACT coordinate / size / font measured from the
// bank's own PDF render of the Word file (see POS, all in mm / pt):
//   • emblem top-left (4.8,4) and wordmark top-right (138.8,6.3); footer banner
//     at the bottom (22.2,277.2).
//   • شماره/تاریخ/پیوست right-aligned at right-edge 63.5mm; recipient (B Titr
//     Bold 12pt) right-aligned at 190.2mm; classification (11pt) at 61mm; موضوع
//     (Titr 12pt) full width; right-side dashed rule; سرپرستی (B Titr Bold 13pt)
//     at 90.5mm; body region; رونوشت/اقدام at the bottom right.
// Fonts are requested from the locally-installed B Nazanin / Titr / B Titr that
// the Word file uses, so it renders identically on the bank's machines.
import { useState, useRef, useEffect } from 'react'
import Layout from '@/components/Layout'
import { Printer, Eraser } from 'lucide-react'
import { LH_LOGO, LH_NAME, LH_FOOTER } from './letterhead'

const SENDERS = ['سرپرستی منطقه خلیج فارس', 'دایره تسهیلات اعطایی']
const CLASSES = ['داخلی', 'عادی', 'محرمانه', 'خیلی محرمانه']
const NAZ = "'B Nazanin','BNazanin','Nazanin',serif"
const TITR = "'Titr','B Titr','BTitr','B Nazanin',serif"
const BTITR = "'B Titr','BTitr','Titr','B Nazanin',serif"

function todayDMY() { const d = new Date(); const p = (n: number) => String(n).padStart(2, '0'); return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}` }
const mm = (v: number) => `${v}mm`
const fromRight = (rightEdge: number) => `${210 - rightEdge}mm` // page is 210mm wide

function Fld({ value, onChange, placeholder, w, ltr }: { value: string; onChange: (e: any) => void; placeholder?: string; w?: string; ltr?: boolean }) {
  const st: React.CSSProperties = {}
  if (w) st.width = w
  if (ltr) { st.direction = 'ltr'; st.textAlign = 'right' }
  return (
    <>
      <input className="screen-only fld" value={value} onChange={onChange} placeholder={placeholder} style={st} />
      <span className="print-only" style={ltr ? { direction: 'ltr', unicodeBidi: 'isolate' } : undefined}>{value || ''}</span>
    </>
  )
}
function Area({ value, onChange, placeholder }: { value: string; onChange: (e: any) => void; placeholder?: string }) {
  const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => { const el = ref.current; if (el) { el.style.height = 'auto'; el.style.height = `${el.scrollHeight}px` } }, [value])
  return (
    <>
      <textarea ref={ref} rows={1} className="screen-only area" value={value} onChange={onChange} placeholder={placeholder} />
      <div className="print-only print-text">{value || ''}</div>
    </>
  )
}

export default function LetterPage() {
  const [f, setF] = useState({
    classification: 'داخلی', refNo: `${new Date().getFullYear()}/----/4/182`, date: todayDMY(), attachment: 'دارد',
    recipientName: '', recipientTitle: 'رئیس محترم', recipientDept: '', subject: '', body: '',
    sender: SENDERS[0], copyTo: '', actionName: '', actionExt: '',
  })
  const set = (k: keyof typeof f) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const ab = (top: number, opts: { right?: number; left?: number; w?: number; font?: string; size?: number; bold?: boolean; center?: boolean } = {}): React.CSSProperties => {
    const st: React.CSSProperties = { position: 'absolute', top: mm(top), whiteSpace: 'nowrap' }
    if (opts.left != null) st.left = mm(opts.left)
    if (opts.right != null) st.right = fromRight(opts.right)
    if (opts.w != null) st.width = mm(opts.w)
    if (opts.font) st.fontFamily = opts.font
    if (opts.size) st.fontSize = `${opts.size}pt`
    if (opts.bold) st.fontWeight = 700
    if (opts.center) st.textAlign = 'center'
    else st.textAlign = 'right'
    return st
  }

  return (
    <Layout>
      <div dir="rtl">
        <style>{`
        .ltr-controls { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:14px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; }
        .ltr-btn { padding:8px 14px; border-radius:6px; font-weight:600; cursor:pointer; border:0; display:inline-flex; align-items:center; gap:6px; color:#fff; }
        .ltr-btn.blue { background:#2563eb; } .ltr-btn.gray { background:#475569; } .ltr-hint { font-size:12px; color:#64748b; }
        #ltr-page { position:relative; width:210mm; height:297mm; margin:0 auto; background:#fff; box-shadow:0 0 6px rgba(0,0,0,.12);
                    color:#000; font-family:${NAZ}; font-size:13pt; line-height:1.2; overflow:hidden; }
        #ltr-page input.fld, #ltr-page select { border:0; border-bottom:1px dotted #b6c7e6; background:transparent; font:inherit; color:#000; padding:0 2px; }
        #ltr-page input.fld::placeholder { color:#aeb8c6; } #ltr-page select { border-bottom:1px solid #9db8e6; cursor:pointer; font:inherit; }
        #ltr-page textarea.area { width:100%; border:0; background:transparent; font:inherit; color:#000; resize:none; overflow:hidden; padding:0; box-sizing:border-box; line-height:1.7; }
        .sep-line { position:absolute; border-top:1px dashed #000; }
        .print-only { display:none; } .print-text { white-space:pre-wrap; word-break:break-word; }
        @media print {
          @page { size:A4; margin:0; }
          html, body { margin:0 !important; padding:0 !important; background:#fff !important; }
          .no-print, .screen-only { display:none !important; } .print-only { display:inline !important; }
          #ltr-page { box-shadow:none; margin:0; }
          #ltr-page .body-area .print-text { display:block !important; }
        }
        `}</style>

        <div className="ltr-controls no-print">
          <button onClick={() => window.print()} className="ltr-btn blue"><Printer size={15} /> پرینت</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={15} /> پاک‌کردنِ متغیرها</button>
          <span className="ltr-hint">مختصات/اندازه/فونت‌ها مستقیماً از PDF خودِ نامه استخراج شده‌اند. فونت‌ها از B Nazanin / Titr نصب‌شدهٔ سیستم خوانده می‌شوند.</span>
        </div>

        <div id="ltr-page">
          {/* Letterhead images (exact bbox) */}
          <img src={LH_LOGO} alt="" style={{ position: 'absolute', left: mm(4.8), top: mm(4), width: mm(28.5), height: mm(27.6) }} />
          <img src={LH_NAME} alt="" style={{ position: 'absolute', left: mm(138.8), top: mm(6.3), width: mm(65.8), height: mm(20.4) }} />
          <img src={LH_FOOTER} alt="" style={{ position: 'absolute', left: mm(22.2), top: mm(277.2), width: mm(167.4), height: mm(17.7) }} />

          {/* بسمه تعالی — centred */}
          <div style={ab(29, { left: 85, w: 40, center: true, size: 13 })}>بسمه تعالی</div>

          {/* شماره / تاریخ / پیوست — right edge 63.5mm */}
          <div style={ab(44.8, { right: 63.5, size: 12 })}>شماره : <Fld value={f.refNo} onChange={set('refNo')} placeholder="2026/----/4/182" w="34mm" ltr /></div>
          <div style={ab(51, { right: 63.5, size: 12 })}>تاریخ&nbsp;: <Fld value={f.date} onChange={set('date')} placeholder="--/--/2026" w="28mm" ltr /></div>
          <div style={ab(57.3, { right: 63.5, size: 12 })}>پیوست :{' '}
            <select value={f.attachment} onChange={set('attachment')} className="screen-only"><option value="دارد">دارد</option><option value="ندارد">ندارد</option></select>
            <span className="print-only">{f.attachment}</span>
          </div>

          {/* recipient — B Titr Bold 12pt, right edge 190.2mm */}
          <div style={ab(57.6, { right: 190.2, font: BTITR, size: 12, bold: true })}><Fld value={f.recipientName} onChange={set('recipientName')} placeholder="سرکار خانم / جناب آقای …" w="62mm" /></div>
          <div style={ab(65, { right: 190.2, font: BTITR, size: 12, bold: true })}><Fld value={f.recipientTitle} onChange={set('recipientTitle')} placeholder="رئیس محترم" w="22mm" /> <Fld value={f.recipientDept} onChange={set('recipientDept')} placeholder="اداره کل خارجه" w="40mm" /></div>

          {/* classification — right edge 61mm, 11pt */}
          <div style={ab(66.8, { right: 61, size: 11, bold: true })}>
            نوع طبقه بندی – {' '}
            <select value={f.classification} onChange={set('classification')} className="screen-only">{CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}</select>
            <span className="print-only">{f.classification}</span>
          </div>

          {/* موضوع — Titr 12pt, full width (right edge 190.5, left ~28) */}
          <div style={{ position: 'absolute', top: mm(78), right: fromRight(190.5), left: mm(28), fontFamily: TITR, fontSize: '12pt', textAlign: 'justify', lineHeight: 1.6 }}>
            <span style={{ whiteSpace: 'nowrap' }}>موضوع : </span><span className="screen-only" style={{ display: 'inline-block', width: '88%', verticalAlign: 'top' }}><Area value={f.subject} onChange={set('subject')} placeholder="موضوعِ نامه…" /></span><span className="print-only">{f.subject}</span>
          </div>

          {/* separator — dashed rule on the right (x 133.8 → 190.5) at y≈106 */}
          <div className="sep-line" style={{ top: mm(107), right: fromRight(190.5), left: mm(133.8) }} />

          {/* سرپرستی — B Titr Bold 13pt, right edge 90.5mm */}
          <div style={ab(141.7, { right: 90.5, font: BTITR, size: 13, bold: true })}>
            <select value={f.sender} onChange={set('sender')} className="screen-only">{SENDERS.map((s) => <option key={s} value={s}>{s}</option>)}</select>
            <span className="print-only">{f.sender}</span>
          </div>

          {/* body — the writable region between سرپرستی and رونوشت */}
          <div className="body-area" style={{ position: 'absolute', top: mm(149), right: mm(25), left: mm(25), height: mm(95), fontFamily: NAZ, fontSize: '13pt', textAlign: 'justify' }}>
            <Area value={f.body} onChange={set('body')} placeholder="متنِ نامه را اینجا بنویسید…" />
          </div>

          {/* رونوشت / اقدام کننده — bottom right */}
          <div style={ab(250, { right: 184.7, size: 10 })}>رونوشت : <Fld value={f.copyTo} onChange={set('copyTo')} placeholder="------" w="42mm" /></div>
          <div style={ab(264, { right: 183.8, size: 10 })}>اقدام کننده : <Fld value={f.actionName} onChange={set('actionName')} placeholder="----" w="34mm" /> / داخلی <Fld value={f.actionExt} onChange={set('actionExt')} placeholder="---" w="14mm" ltr /></div>
        </div>
      </div>
    </Layout>
  )
}
