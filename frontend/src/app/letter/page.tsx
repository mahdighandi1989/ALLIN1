'use client'

// Official Bank Saderat (UAE — Regional Office) LETTER (نامه), reproduced to match
// the Word source EXACTLY: an absolute A4 (210×297mm) canvas with every element at
// the coordinate / size / font / spacing read out of the .docx itself —
//   • fonts: B Nazanin (body 13pt), Titr (موضوع/subject 12pt), B Titr (signatory
//     13pt bold), B Nazanin bold 11pt (classification). These are the fonts the
//     Word file uses and that exist on the bank's machines, so it renders identically.
//   • floats at their exact anchors: emblem top-left, wordmark top-right, بسمه
//     centred, شماره/تاریخ/پیوست at the left margin, recipient at column+105mm.
//   • the body flows from a fixed Y; the closing (signatory, رونوشت, اقدام) follows.
// All coordinates live in POS below, so any nudge is a one-number change.
import { useState, useRef, useEffect } from 'react'
import Layout from '@/components/Layout'
import { Printer, Eraser } from 'lucide-react'
import { LH_LOGO, LH_NAME, LH_FOOTER } from './letterhead'

const SENDERS = ['سرپرستی منطقه خلیج فارس', 'دایره تسهیلات اعطایی']
const CLASSES = ['داخلی', 'عادی', 'محرمانه', 'خیلی محرمانه']

// Exact geometry (mm) extracted from the .docx. Tweak any single number to nudge.
const POS = {
  logo: { left: 5, top: 4, w: 28.5, h: 27.6 },
  name: { left: 138.8, top: 6, w: 65.8, h: 20.4 },
  besmele: { left: 84.9, top: 27, w: 40 },
  ref: { left: 25.4, top: 41, w: 50 },
  recipient: { left: 118, top: 44, w: 66 },
  flowTop: 75,          // where the flowing content starts (below the floats)
  margin: 25.4,
}

function todayDMY() {
  const d = new Date(); const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`
}

function Fld({ value, onChange, placeholder, w, ltr, bold, font }: { value: string; onChange: (e: any) => void; placeholder?: string; w?: string; ltr?: boolean; bold?: boolean; font?: string }) {
  const style: React.CSSProperties = {}
  if (w) style.width = w
  if (ltr) { style.direction = 'ltr'; style.textAlign = 'right' }
  if (bold) style.fontWeight = 700
  if (font) style.fontFamily = font
  return (
    <>
      <input className="screen-only fld" value={value} onChange={onChange} placeholder={placeholder} style={style} />
      <span className="print-only" style={{ ...(ltr ? { direction: 'ltr', unicodeBidi: 'isolate' } : {}), fontWeight: bold ? 700 : undefined, fontFamily: font }}>{value || ''}</span>
    </>
  )
}

function Area({ value, onChange, placeholder, font }: { value: string; onChange: (e: any) => void; placeholder?: string; font?: string }) {
  const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => { const el = ref.current; if (el) { el.style.height = 'auto'; el.style.height = `${el.scrollHeight}px` } }, [value])
  return (
    <>
      <textarea ref={ref} rows={1} className="screen-only area" value={value} onChange={onChange} placeholder={placeholder} style={font ? { fontFamily: font } : undefined} />
      <div className="print-only print-text" style={font ? { fontFamily: font } : undefined}>{value || ''}</div>
    </>
  )
}

export default function LetterPage() {
  const [f, setF] = useState({
    classification: 'داخلی',
    refNo: `${new Date().getFullYear()}/----/4/182`,
    date: todayDMY(),
    attachment: 'دارد',
    recipientName: '', recipientTitle: 'رئیس محترم', recipientDept: '',
    subject: '',
    body: '',
    sender: SENDERS[0],
    copyTo: '',
    actionName: '', actionExt: '',
  })
  const set = (k: keyof typeof f) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))

  return (
    <Layout>
      <div dir="rtl">
        <style>{`
        .ltr-controls { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:14px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; }
        .ltr-btn { padding:8px 14px; border-radius:6px; font-weight:600; cursor:pointer; border:0; display:inline-flex; align-items:center; gap:6px; color:#fff; }
        .ltr-btn.blue { background:#2563eb; } .ltr-btn.gray { background:#475569; }
        .ltr-hint { font-size:12px; color:#64748b; }

        /* A4 canvas with the document's own fonts. */
        #ltr-page { position:relative; width:210mm; min-height:297mm; margin:0 auto; background:#fff; box-shadow:0 0 6px rgba(0,0,0,.12);
                    color:#000; font-family:'B Nazanin','BNazanin','Nazanin','Times New Roman',serif; font-size:13pt; line-height:1.15; }
        .ab { position:absolute; }
        .float-img { position:absolute; }
        .besmele { text-align:center; font-size:13pt; }
        .refblock { text-align:right; font-size:13pt; line-height:1.9; white-space:nowrap; }
        .recipient { text-align:right; font-size:13pt; font-weight:700; line-height:1.6; }
        .recipient .r2 { display:flex; gap:5px; justify-content:flex-start; }

        .flow { margin:0 ${POS.margin}mm; }
        .classification { text-align:left; font-weight:700; font-size:11pt; }
        .subject { font-size:12pt; font-family:'Titr','B Titr','B Nazanin',serif; text-align:justify; display:flex; gap:5px; align-items:flex-start; margin-top:3mm; }
        .subject .lbl { white-space:nowrap; }
        .seprow { display:flex; margin:1mm 0 3mm; }
        .sep { flex:0 0 56%; border-top:1px dashed #000; height:0; }
        .sender { text-align:center; font-family:'B Titr','Titr','B Nazanin',serif; font-weight:700; font-size:13pt; margin:4mm 0; }
        .body { font-size:13pt; text-align:justify; line-height:1.55; min-height:60mm; }
        .closing { text-align:right; font-size:11pt; line-height:1.9; margin-top:4mm; }
        .closing .copyto, .closing .actionby { display:flex; gap:5px; justify-content:flex-start; align-items:center; flex-wrap:wrap; }
        .footer-img { position:absolute; left:${POS.margin}mm; right:${POS.margin}mm; bottom:8mm; }
        .footer-img img { width:100%; }

        /* Subtle field chrome */
        #ltr-page input.fld, #ltr-page select { border:0; border-bottom:1px dotted #b6c7e6; background:transparent; font:inherit; color:#000; padding:0 2px; }
        #ltr-page input.fld::placeholder { color:#aeb8c6; }
        #ltr-page select { border-bottom:1px solid #9db8e6; cursor:pointer; font:inherit; }
        #ltr-page textarea.area { width:100%; border:0; border-bottom:1px dotted #cdd8ea; background:transparent; font:inherit; color:#000; resize:none; overflow:hidden; padding:0 2px; box-sizing:border-box; }
        .print-only { display:none; } .print-text { white-space:pre-wrap; word-break:break-word; }

        @media print {
          @page { size:A4; margin:0; }
          html, body { margin:0 !important; padding:0 !important; background:#fff !important; }
          .no-print, .screen-only { display:none !important; }
          .print-only { display:block !important; }
          #ltr-page { box-shadow:none; margin:0; }
          .subject .print-text { display:inline !important; }
        }
        `}</style>

        <div className="ltr-controls no-print">
          <button onClick={() => window.print()} className="ltr-btn blue"><Printer size={15} /> پرینت</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={15} /> پاک‌کردنِ متغیرها</button>
          <span className="ltr-hint">فونت‌ها از روی فونت‌های نصب‌شدهٔ سیستم (B Nazanin / Titr) خوانده می‌شوند تا مثلِ Word دربیاید. مختصات از خودِ فایلِ Word استخراج شده؛ اگر جایی چند میلی‌متر جابه‌جا بود بگو تا دقیق کنم.</span>
        </div>

        <div id="ltr-page">
          {/* Letterhead: emblem top-left, wordmark top-right */}
          <img className="float-img" src={LH_LOGO} alt="" style={{ left: `${POS.logo.left}mm`, top: `${POS.logo.top}mm`, width: `${POS.logo.w}mm`, height: `${POS.logo.h}mm` }} />
          <img className="float-img" src={LH_NAME} alt="" style={{ left: `${POS.name.left}mm`, top: `${POS.name.top}mm`, width: `${POS.name.w}mm`, height: `${POS.name.h}mm` }} />

          <div className="ab besmele" style={{ left: `${POS.besmele.left}mm`, top: `${POS.besmele.top}mm`, width: `${POS.besmele.w}mm` }}>بسمه تعالی</div>

          {/* شماره / تاریخ / پیوست — left margin */}
          <div className="ab refblock" style={{ left: `${POS.ref.left}mm`, top: `${POS.ref.top}mm`, width: `${POS.ref.w}mm` }}>
            <div>شماره: <Fld value={f.refNo} onChange={set('refNo')} placeholder="2026/----/4/182" w="36mm" ltr /></div>
            <div>تاریخ&nbsp;: <Fld value={f.date} onChange={set('date')} placeholder="--/--/2026" w="28mm" ltr /></div>
            <div>پیوست:{' '}
              <select value={f.attachment} onChange={set('attachment')} className="screen-only"><option value="دارد">دارد</option><option value="ندارد">ندارد</option></select>
              <span className="print-only" style={{ display: 'inline' }}>{f.attachment}</span>
            </div>
          </div>

          {/* recipient — right */}
          <div className="ab recipient" style={{ left: `${POS.recipient.left}mm`, top: `${POS.recipient.top}mm`, width: `${POS.recipient.w}mm` }}>
            <div><Fld value={f.recipientName} onChange={set('recipientName')} placeholder="سرکار خانم / جناب آقای …" w="64mm" bold /></div>
            <div className="r2">
              <Fld value={f.recipientTitle} onChange={set('recipientTitle')} placeholder="رئیس محترم" w="22mm" bold />
              <Fld value={f.recipientDept} onChange={set('recipientDept')} placeholder="ادارهٔ کل خارجه" w="40mm" bold />
            </div>
          </div>

          {/* Flowing content */}
          <div className="flow" style={{ paddingTop: `${POS.flowTop}mm` }}>
            <div className="classification">
              نوع طبقه‌بندی – {' '}
              <select value={f.classification} onChange={set('classification')} className="screen-only">{CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}</select>
              <span className="print-only" style={{ display: 'inline' }}>{f.classification}</span>
            </div>

            <div className="subject"><span className="lbl">موضوع :</span><Area value={f.subject} onChange={set('subject')} placeholder="موضوعِ نامه…" font="'Titr','B Titr','B Nazanin',serif" /></div>
            <div className="seprow"><div className="sep" /></div>

            <div className="sender">
              <select value={f.sender} onChange={set('sender')} className="screen-only">{SENDERS.map((s) => <option key={s} value={s}>{s}</option>)}</select>
              <span className="print-only" style={{ display: 'block' }}>{f.sender}</span>
            </div>

            <div className="body"><Area value={f.body} onChange={set('body')} placeholder="متنِ نامه را اینجا بنویسید…" /></div>

            <div className="closing">
              <div className="copyto"><span style={{ whiteSpace: 'nowrap' }}>رونوشت :</span> <Area value={f.copyTo} onChange={set('copyTo')} placeholder="رونوشت به…" /></div>
              <div className="actionby"><span>اقدام کننده :</span> <Fld value={f.actionName} onChange={set('actionName')} placeholder="نام" w="40mm" /> <span>/ داخلی</span> <Fld value={f.actionExt} onChange={set('actionExt')} placeholder="—" w="16mm" ltr /></div>
            </div>
          </div>

          <div className="footer-img"><img src={LH_FOOTER} alt="" /></div>
        </div>
      </div>
    </Layout>
  )
}
