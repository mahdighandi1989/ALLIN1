'use client'

// Official Bank Saderat (UAE — Regional Office) LETTER (نامه) template, laid out
// to match the Word original: emblem top-LEFT, wordmark top-RIGHT, بسمه تعالی
// centred; then a two-column band — شماره/تاریخ/پیوست STACKED on the left, the
// recipient (bold) on the right; the classification (left), موضوع, a right-side
// dashed separator, the free body, and finally the closing block (signatory
// dropdown + رونوشت + اقدام کننده) which stays together on the last page. The
// letterhead + footer banner repeat on every printed page and pages are numbered.
import { useState, useRef, useEffect } from 'react'
import Layout from '@/components/Layout'
import { Printer, Eraser } from 'lucide-react'
import { LH_LOGO, LH_NAME, LH_FOOTER } from './letterhead'

const SENDERS = ['سرپرستی منطقه خلیج فارس', 'دایره تسهیلات اعطایی']
const CLASSES = ['داخلی', 'عادی', 'محرمانه', 'خیلی محرمانه']

function todayDMY() {
  const d = new Date(); const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`
}

// Single-line field: input on screen, plain text in print. `ltr` keeps reference
// numbers / dates reading left-to-right inside the RTL letter.
function Fld({ value, onChange, placeholder, w, ltr, bold }: { value: string; onChange: (e: any) => void; placeholder?: string; w?: string; ltr?: boolean; bold?: boolean }) {
  const style: React.CSSProperties = {}
  if (w) style.width = w
  if (ltr) { style.direction = 'ltr'; style.textAlign = 'right' }
  if (bold) style.fontWeight = 700
  return (
    <>
      <input className="screen-only fld" value={value} onChange={onChange} placeholder={placeholder} style={style} />
      <span className="print-only" style={{ ...(ltr ? { direction: 'ltr', unicodeBidi: 'isolate' } : {}), fontWeight: bold ? 700 : undefined }}>{value || ''}</span>
    </>
  )
}

// Multi-line field: auto-growing textarea on screen, wrapping text that flows
// across pages in print.
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

        #ltr-sheet { width:210mm; min-height:297mm; margin:0 auto; background:#fff; box-shadow:0 0 6px rgba(0,0,0,.12);
                     padding:12mm 25mm 10mm; box-sizing:border-box; color:#000;
                     font-family:Tahoma,'B Nazanin','Segoe UI',sans-serif; font-size:12pt; line-height:1.6; }

        /* Letterhead: emblem LEFT, wordmark RIGHT (LTR row so order is fixed) */
        .lh-row { display:flex; direction:ltr; justify-content:space-between; align-items:flex-start; }
        .lh-logo { height:23mm; } .lh-name { height:16mm; margin-top:1mm; }
        .bismillah { text-align:center; font-size:11pt; margin:1mm 0 4mm; }

        /* Two-column band: recipient (right) + ref block (left) */
        .top-band { display:flex; justify-content:space-between; align-items:flex-start; gap:14px; margin-top:1mm; }
        .recipient { text-align:right; font-weight:700; font-size:12pt; line-height:2; padding-top:6mm; }
        .recipient .r2 { display:flex; gap:6px; justify-content:flex-start; }
        .refblock { text-align:right; font-size:11pt; line-height:2; white-space:nowrap; }
        .refblock .lbl { display:inline-block; }

        .classification { text-align:left; font-weight:700; font-size:12pt; margin:5mm 0 3mm; }
        .subject { display:flex; gap:6px; font-size:12pt; text-align:justify; align-items:flex-start; }
        .subject .lbl { white-space:nowrap; padding-top:2px; }
        .sep { border:0; border-top:1.5px dashed #000; width:55%; margin:3mm 0 5mm auto; }

        .body { font-size:12pt; text-align:justify; line-height:1.9; min-height:55mm; }

        .bottom-block { margin-top:6mm; }
        .sender { font-weight:700; font-size:13pt; text-align:center; margin:8mm 0; }
        .closing { text-align:right; font-size:11pt; line-height:2; }
        .closing .copyto, .closing .actionby { display:flex; gap:6px; justify-content:flex-start; align-items:center; flex-wrap:wrap; }
        .lh-footer { width:100%; margin-top:8mm; }

        /* Inputs (screen only) */
        #ltr-sheet input.fld, #ltr-sheet select { border:0; border-bottom:1px dotted #93c5fd; background:#eff6ff; font:inherit; color:#000; padding:0 3px; }
        #ltr-sheet select { background:#eff6ff; border-bottom:1px solid #60a5fa; cursor:pointer; }
        #ltr-sheet textarea.area { width:100%; border:1px dashed #cbd5e1; background:#f8fafc; font:inherit; color:#000; resize:none; overflow:hidden; padding:2px 4px; box-sizing:border-box; line-height:1.9; }
        .print-only { display:none; }
        .print-text { white-space:pre-wrap; word-break:break-word; }
        .print-header, .print-footer { display:none; }

        @media print {
          @page { size:A4; margin:40mm 25mm 30mm; }
          @page { @bottom-center { content:"صفحه " counter(page) " از " counter(pages); font-family:Tahoma,sans-serif; font-size:9pt; color:#1d4ed8; } }
          html, body { margin:0 !important; padding:0 !important; background:#fff !important; }
          .no-print, .screen-only { display:none !important; }
          .print-only { display:block !important; }
          #ltr-sheet { width:auto; min-height:0; box-shadow:none; padding:0; }
          .print-header { display:block; position:fixed; top:-34mm; left:0; right:0; }
          .print-header .ph-row { display:flex; direction:ltr; justify-content:space-between; align-items:flex-start; }
          .print-header .lh-logo { height:22mm; } .print-header .lh-name { height:15mm; }
          .print-footer { display:block; position:fixed; bottom:-26mm; left:0; right:0; }
          .print-footer img { width:100%; }
          .subject .print-text, .recipient .print-only { display:inline !important; }
          .bottom-block { break-inside:avoid; page-break-inside:avoid; }
          .body { min-height:0; }
        }
        `}</style>

        <div className="ltr-controls no-print">
          <button onClick={() => window.print()} className="ltr-btn blue"><Printer size={15} /> پرینت</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={15} /> پاک‌کردنِ متغیرها</button>
          <span className="ltr-hint">خانه‌های آبی/خط‌چین قابلِ ویرایش‌اند و در پرینت پاک می‌شوند. سربرگ و فوتر در هر صفحه تکرار می‌شوند؛ نامه می‌تواند چند صفحه شود.</span>
        </div>

        <div id="ltr-sheet">
          {/* Repeating print-only letterhead + footer */}
          <div className="print-header"><div className="ph-row"><img className="lh-logo" src={LH_LOGO} alt="" /><img className="lh-name" src={LH_NAME} alt="" /></div></div>
          <div className="print-footer"><img src={LH_FOOTER} alt="" /></div>

          {/* On-screen letterhead: emblem left, wordmark right */}
          <div className="lh-row screen-only">
            <img className="lh-logo" src={LH_LOGO} alt="Regional Office" />
            <img className="lh-name" src={LH_NAME} alt="Bank Saderat Iran" />
          </div>

          <div className="bismillah">بسمه تعالی</div>

          <div className="top-band">
            {/* recipient (right) */}
            <div className="recipient">
              <div><Fld value={f.recipientName} onChange={set('recipientName')} placeholder="سرکار خانم / جناب آقای …" w="70mm" bold /></div>
              <div className="r2">
                <Fld value={f.recipientTitle} onChange={set('recipientTitle')} placeholder="رئیس محترم" w="26mm" bold />
                <Fld value={f.recipientDept} onChange={set('recipientDept')} placeholder="ادارهٔ کل خارجه" w="60mm" bold />
              </div>
            </div>
            {/* ref block (left) — stacked */}
            <div className="refblock">
              <div><span className="lbl">شماره:</span> <Fld value={f.refNo} onChange={set('refNo')} placeholder="2026/----/4/182" w="40mm" ltr /></div>
              <div><span className="lbl">تاریخ&nbsp;:</span> <Fld value={f.date} onChange={set('date')} placeholder="--/--/2026" w="30mm" ltr /></div>
              <div>
                <span className="lbl">پیوست:</span>{' '}
                <select value={f.attachment} onChange={set('attachment')} className="screen-only"><option value="دارد">دارد</option><option value="ندارد">ندارد</option></select>
                <span className="print-only" style={{ display: 'inline' }}>{f.attachment}</span>
              </div>
            </div>
          </div>

          <div className="classification">
            نوع طبقه‌بندی – {' '}
            <select value={f.classification} onChange={set('classification')} className="screen-only">{CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}</select>
            <span className="print-only" style={{ display: 'inline' }}>{f.classification}</span>
          </div>

          <div className="subject">
            <span className="lbl">موضوع :</span>
            <Area value={f.subject} onChange={set('subject')} placeholder="موضوعِ نامه…" />
          </div>
          <hr className="sep" />

          <div className="body"><Area value={f.body} onChange={set('body')} placeholder="متنِ نامه را اینجا بنویسید… (می‌تواند چند صفحه شود)" /></div>

          <div className="bottom-block">
            <div className="sender">
              <select value={f.sender} onChange={set('sender')} className="screen-only">{SENDERS.map((s) => <option key={s} value={s}>{s}</option>)}</select>
              <span className="print-only" style={{ display: 'block' }}>{f.sender}</span>
            </div>
            <div className="closing">
              <div className="copyto"><span style={{ whiteSpace: 'nowrap' }}>رونوشت :</span> <Area value={f.copyTo} onChange={set('copyTo')} placeholder="رونوشت به…" /></div>
              <div className="actionby"><span>اقدام کننده :</span> <Fld value={f.actionName} onChange={set('actionName')} placeholder="نام" w="45mm" /> <span>/ داخلی</span> <Fld value={f.actionExt} onChange={set('actionExt')} placeholder="—" w="18mm" ltr /></div>
            </div>
          </div>

          <img className="lh-footer screen-only" src={LH_FOOTER} alt="" />
        </div>
      </div>
    </Layout>
  )
}
