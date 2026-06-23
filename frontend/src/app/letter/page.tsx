'use client'

// Official Bank Saderat (UAE — Regional Office) LETTER (نامه) template. Faithful
// to the Word original: letterhead (logo + wordmark) on top, بسمه تعالی, the
// شماره/تاریخ/پیوست block, the recipient, classification, subject, a separator,
// the free body, then the signatory (a dropdown: سرپرستی منطقه خلیج فارس OR
// دایره تسهیلات اعطایی) with رونوشت / اقدام کننده, and the address footer banner.
// Unlike the one-page forms, a letter may run to several pages; the letterhead +
// footer repeat on every page, the closing block stays together on the last page,
// and pages are numbered just above the footer.
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

// Single-line field: an input on screen, plain text in print (so nothing is clipped).
function Fld({ value, onChange, placeholder, w }: { value: string; onChange: (e: any) => void; placeholder?: string; w?: string }) {
  return (
    <>
      <input className="screen-only fld" value={value} onChange={onChange} placeholder={placeholder} style={w ? { width: w } : undefined} />
      <span className="print-only">{value || ''}</span>
    </>
  )
}

// Multi-line field: an auto-growing textarea on screen, wrapping text that FLOWS
// across pages in print.
function Area({ value, onChange, placeholder, cls }: { value: string; onChange: (e: any) => void; placeholder?: string; cls?: string }) {
  const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => { const el = ref.current; if (el) { el.style.height = 'auto'; el.style.height = `${el.scrollHeight}px` } }, [value])
  return (
    <>
      <textarea ref={ref} rows={1} className={`screen-only area ${cls || ''}`} value={value} onChange={onChange} placeholder={placeholder} />
      <div className={`print-only print-text ${cls || ''}`}>{value || ''}</div>
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
                     padding:14mm 25mm 12mm; box-sizing:border-box; color:#000;
                     font-family:Tahoma,'B Nazanin','Segoe UI',sans-serif; font-size:12pt; line-height:1.9; }
        /* Letterhead */
        .lh-row { display:flex; justify-content:space-between; align-items:center; gap:10px; }
        .lh-logo { height:24mm; } .lh-name { height:15mm; }
        .bismillah { text-align:center; font-size:11pt; margin:3mm 0 5mm; }
        /* Number / date / attachment */
        .ref-row { display:flex; justify-content:space-between; gap:12px; font-size:11pt; }
        .attach { font-size:11pt; margin-top:1mm; }
        /* Recipient */
        .recipient { margin:7mm 0 4mm; font-size:12pt; line-height:1.8; }
        .recipient .r2 { display:flex; gap:6px; }
        /* Classification + subject */
        .classification { text-align:center; font-weight:700; font-size:12pt; margin:4mm 0 2mm; }
        .subject { font-size:12pt; text-align:justify; display:flex; gap:6px; }
        .subject .lbl { white-space:nowrap; }
        .sep { border:0; border-top:1.5px solid #000; margin:3mm 0 5mm; }
        /* Body */
        .body { font-size:12pt; text-align:justify; min-height:40mm; }
        /* Closing block (keeps together on the last page) */
        .bottom-block { margin-top:8mm; }
        .sender { text-align:center; font-weight:700; font-size:13pt; margin:6mm 0; }
        .copyto { font-size:11pt; display:flex; gap:6px; }
        .actionby { font-size:11pt; display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-top:1mm; }
        .lh-footer { width:100%; margin-top:8mm; }
        /* Inputs (screen) */
        #ltr-sheet input.fld, #ltr-sheet select { border:0; border-bottom:1px dotted #93c5fd; background:#eff6ff; font:inherit; color:#000; padding:0 3px; }
        #ltr-sheet select { background:#eff6ff; border-bottom:1px solid #60a5fa; cursor:pointer; }
        #ltr-sheet textarea.area { width:100%; border:1px dashed #cbd5e1; background:#f8fafc; font:inherit; color:#000; resize:none; overflow:hidden; padding:2px 4px; box-sizing:border-box; line-height:1.9; }
        .print-only { display:none; }
        .print-text { white-space:pre-wrap; word-break:break-word; }
        .print-header, .print-footer { display:none; }

        @media print {
          @page { size:A4; margin:38mm 22mm 30mm; }
          @page { @bottom-center { content:"صفحه " counter(page) " از " counter(pages); font-family:Tahoma,sans-serif; font-size:9pt; color:#1d4ed8; } }
          html, body { margin:0 !important; padding:0 !important; background:#fff !important; }
          .no-print { display:none !important; }
          .screen-only { display:none !important; }
          .print-only { display:block !important; }
          #ltr-sheet { width:auto; min-height:0; box-shadow:none; padding:0; font-size:12pt; }
          /* Letterhead + footer repeat on EVERY printed page, sitting in the page margins. */
          .print-header { display:block; position:fixed; top:-32mm; left:0; right:0; }
          .print-header .ph-row { display:flex; justify-content:space-between; align-items:center; }
          .print-header .lh-logo { height:22mm; } .print-header .lh-name { height:14mm; }
          .print-footer { display:block; position:fixed; bottom:-26mm; left:0; right:0; text-align:center; }
          .print-footer img { width:100%; }
          .bottom-block { break-inside:avoid; page-break-inside:avoid; }
          .body { min-height:0; }
        }
        `}</style>

        {/* Controls (not printed) */}
        <div className="ltr-controls no-print">
          <button onClick={() => window.print()} className="ltr-btn blue"><Printer size={15} /> پرینت</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={15} /> پاک‌کردنِ متغیرها</button>
          <span className="ltr-hint">خانه‌های آبی/خط‌چین قابلِ ویرایش‌اند و در پرینت پاک می‌شوند. سربرگ و فوتر در هر صفحه تکرار می‌شوند؛ نامه می‌تواند چند صفحه شود.</span>
        </div>

        <div id="ltr-sheet">
          {/* Repeating print-only letterhead + footer (one per page) */}
          <div className="print-header">
            <div className="ph-row"><img className="lh-logo" src={LH_LOGO} alt="" /><img className="lh-name" src={LH_NAME} alt="" /></div>
          </div>
          <div className="print-footer"><img src={LH_FOOTER} alt="" /></div>

          {/* On-screen letterhead */}
          <div className="lh-row screen-only">
            <img className="lh-logo" src={LH_LOGO} alt="Regional Office" />
            <img className="lh-name" src={LH_NAME} alt="Bank Saderat Iran" />
          </div>

          <div className="bismillah">بسمه تعالی</div>

          <div className="ref-row">
            <div>شماره: <Fld value={f.refNo} onChange={set('refNo')} w="42mm" /></div>
            <div>تاریخ: <Fld value={f.date} onChange={set('date')} w="32mm" /></div>
          </div>
          <div className="attach">
            پیوست: {' '}
            <select value={f.attachment} onChange={set('attachment')} className="screen-only">
              <option value="دارد">دارد</option><option value="ندارد">ندارد</option>
            </select>
            <span className="print-only" style={{ display: 'inline' }}>{f.attachment}</span>
          </div>

          <div className="recipient">
            <div><Fld value={f.recipientName} onChange={set('recipientName')} placeholder="سرکار خانم / جناب آقای …" w="80mm" /></div>
            <div className="r2">
              <Fld value={f.recipientTitle} onChange={set('recipientTitle')} placeholder="رئیس محترم" w="28mm" />
              <Fld value={f.recipientDept} onChange={set('recipientDept')} placeholder="ادارهٔ کل خارجه" w="90mm" />
            </div>
          </div>

          <div className="classification">
            نوع طبقه‌بندی – {' '}
            <select value={f.classification} onChange={set('classification')} className="screen-only">
              {CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <span className="print-only" style={{ display: 'inline' }}>{f.classification}</span>
          </div>

          <div className="subject">
            <span className="lbl">موضوع :</span>
            <Area value={f.subject} onChange={set('subject')} placeholder="موضوعِ نامه…" />
          </div>
          <hr className="sep" />

          <div className="body">
            <Area value={f.body} onChange={set('body')} placeholder="متنِ نامه را اینجا بنویسید… (می‌تواند چند صفحه شود)" cls="body-text" />
          </div>

          <div className="bottom-block">
            <div className="sender">
              <select value={f.sender} onChange={set('sender')} className="screen-only">
                {SENDERS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <span className="print-only" style={{ display: 'block' }}>{f.sender}</span>
            </div>
            <div className="copyto">
              <span style={{ whiteSpace: 'nowrap' }}>رونوشت :</span>
              <Area value={f.copyTo} onChange={set('copyTo')} placeholder="رونوشت به…" />
            </div>
            <div className="actionby">
              <span>اقدام کننده :</span>
              <Fld value={f.actionName} onChange={set('actionName')} placeholder="نام" w="45mm" />
              <span>/ داخلی</span>
              <Fld value={f.actionExt} onChange={set('actionExt')} placeholder="—" w="20mm" />
            </div>
          </div>

          {/* On-screen footer banner */}
          <img className="lh-footer screen-only" src={LH_FOOTER} alt="" />
        </div>
      </div>
    </Layout>
  )
}
