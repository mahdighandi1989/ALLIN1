'use client'

// Official Bank Saderat LETTER (نامه) with a built-in DRAG & RESIZE layout editor.
// Toggle «چیدمان» (design mode) to drag any field, resize its width/height with the
// corner handle, and change its font size with A−/A+. Positions are in px on a
// fixed A4 canvas (794×1123 px = 210×297 mm at 96 dpi, so it prints 1:1). The
// layout is saved in the browser (localStorage) and restored next time; «بازنشانی»
// returns to the measured defaults. In «تکمیل» (fill) mode you type the values and
// print. Fonts come from the locally-installed B Nazanin / Titr / B Titr.
import { useState, useRef, useEffect, useCallback } from 'react'
import Layout from '@/components/Layout'
import { Printer, Eraser, Move, Check, RotateCcw, Type } from 'lucide-react'
import { LH_LOGO, LH_NAME, LH_FOOTER } from './letterhead'

const SENDERS = ['سرپرستی منطقه خلیج فارس', 'دایره تسهیلات اعطایی']
const CLASSES = ['داخلی', 'عادی', 'محرمانه', 'خیلی محرمانه']
const NAZ = "'B Nazanin','BNazanin','Nazanin',serif"
const TITR = "'Titr','B Titr','BTitr','B Nazanin',serif"
const BTITR = "'B Titr','BTitr','Titr','B Nazanin',serif"
const MM = 96 / 25.4 // px per mm at 96dpi
const m = (v: number) => Math.round(v * MM)

// Default layout (px) — measured from the bank's PDF. {x,y,w[,h],size,font,bold,align}
type Boxn = { x: number; y: number; w: number; h?: number; size: number; font?: string; bold?: boolean; align?: 'right' | 'center' | 'left' }
const DEFAULT_LAYOUT: Record<string, Boxn> = {
  logo: { x: m(4.8), y: m(4), w: m(28.5), h: m(27.6), size: 0 },
  name: { x: m(138.8), y: m(6.3), w: m(65.8), h: m(20.4), size: 0 },
  footer: { x: m(22.2), y: m(277.2), w: m(167.4), h: m(17.7), size: 0 },
  besmele: { x: m(85), y: m(29), w: m(40), size: 13, font: NAZ, align: 'center' },
  shomareh: { x: m(23.5), y: m(44.8), w: m(40), size: 12, font: NAZ, align: 'right' },
  tarikh: { x: m(23.5), y: m(51), w: m(40), size: 12, font: NAZ, align: 'right' },
  peyvast: { x: m(23.5), y: m(57.3), w: m(40), size: 12, font: NAZ, align: 'right' },
  recName: { x: m(128.2), y: m(57.6), w: m(62), size: 12, font: BTITR, bold: true, align: 'right' },
  recTitle: { x: m(124.2), y: m(65), w: m(66), size: 12, font: BTITR, bold: true, align: 'right' },
  classification: { x: m(21), y: m(66.8), w: m(40), size: 11, font: NAZ, bold: true, align: 'right' },
  subject: { x: m(28), y: m(78), w: m(162.5), size: 12, font: TITR, align: 'right' },
  separator: { x: m(133.8), y: m(107), w: m(56.7), h: 1, size: 0 },
  sender: { x: m(35.5), y: m(141.7), w: m(55), size: 13, font: BTITR, bold: true, align: 'center' },
  body: { x: m(25), y: m(149), w: m(160), h: m(95), size: 13, font: NAZ, align: 'right' },
  copyto: { x: m(124.7), y: m(250), w: m(60), size: 10, font: NAZ, align: 'right' },
  action: { x: m(93.8), y: m(264), w: m(90), size: 10, font: NAZ, align: 'right' },
}
const LS_KEY = 'letterLayout_v2'

function todayDMY() { const d = new Date(); const p = (n: number) => String(n).padStart(2, '0'); return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}` }

export default function LetterPage() {
  const [f, setF] = useState({
    classification: 'داخلی', refNo: `${new Date().getFullYear()}/----/4/182`, date: todayDMY(), attachment: 'دارد',
    recipientName: '', recipientTitle: 'رئیس محترم', recipientDept: '', subject: '', body: '',
    sender: SENDERS[0], copyTo: '', actionName: '', actionExt: '',
  })
  const set = (k: keyof typeof f) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const [L, setL] = useState<Record<string, Boxn>>(DEFAULT_LAYOUT)
  const [design, setDesign] = useState(false)
  const [sel, setSel] = useState<string | null>(null)

  useEffect(() => {
    try { const raw = localStorage.getItem(LS_KEY); if (raw) setL({ ...DEFAULT_LAYOUT, ...JSON.parse(raw) }) } catch { /* ignore */ }
  }, [])
  const saveLayout = () => { try { localStorage.setItem(LS_KEY, JSON.stringify(L)); alert('چیدمان ذخیره شد') } catch { /* ignore */ } }
  const resetLayout = () => { if (confirm('بازگشت به چیدمانِ پیش‌فرض؟')) { setL(DEFAULT_LAYOUT); localStorage.removeItem(LS_KEY) } }
  const bump = (k: string, d: number) => setL((p) => ({ ...p, [k]: { ...p[k], size: Math.max(6, (p[k].size || 12) + d) } }))

  // drag / resize on the A4 canvas (1:1 px, so deltas map directly)
  const startDrag = useCallback((k: string) => (e: React.PointerEvent) => {
    if (!design) return
    if ((e.target as HTMLElement).closest('.rs,.fs-btn')) return
    e.preventDefault(); setSel(k)
    const sx = e.clientX, sy = e.clientY
    setL((p) => { const o = p[k]; (startDrag as any)._o = { x: o.x, y: o.y }; return p })
    const o = (startDrag as any)._o
    const mv = (ev: PointerEvent) => setL((p) => ({ ...p, [k]: { ...p[k], x: Math.round(o.x + ev.clientX - sx), y: Math.round(o.y + ev.clientY - sy) } }))
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }, [design])
  const startResize = (k: string) => (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation(); setSel(k)
    const sx = e.clientX, sy = e.clientY, o = { ...L[k] }
    const mv = (ev: PointerEvent) => setL((p) => ({ ...p, [k]: { ...p[k], w: Math.max(20, Math.round(o.w + ev.clientX - sx)), ...(o.h != null ? { h: Math.max(8, Math.round(o.h + ev.clientY - sy)) } : {}) } }))
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }

  const boxStyle = (k: string): React.CSSProperties => {
    const b = L[k]
    return {
      position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h,
      fontFamily: b.font, fontSize: b.size ? `${b.size}pt` : undefined, fontWeight: b.bold ? 700 : undefined,
      textAlign: b.align, whiteSpace: k === 'subject' || k === 'body' ? 'normal' : 'nowrap',
    }
  }

  const Box = ({ k, children }: { k: string; children?: React.ReactNode }) => (
    <div className={`lbox${design ? ' dz' : ''}${sel === k && design ? ' seld' : ''}`} style={boxStyle(k)} onPointerDown={startDrag(k)}>
      <div className="field-content">{children}</div>
      {design && <>
        <span className="bk-label">{k}</span>
        <span className="rs" onPointerDown={startResize(k)} />
        {L[k].size > 0 && <span className="fs-btns">
          <button className="fs-btn" onPointerDown={(e) => { e.stopPropagation() }} onClick={() => bump(k, -1)}>A−</button>
          <button className="fs-btn" onPointerDown={(e) => { e.stopPropagation() }} onClick={() => bump(k, +1)}>A＋</button>
        </span>}
      </>}
    </div>
  )

  const txt = (v: string) => <span className="print-val">{v}</span>

  return (
    <Layout>
      <div dir="rtl">
        <style>{`
        .ltr-controls { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; }
        .ltr-btn { padding:8px 12px; border-radius:6px; font-weight:600; cursor:pointer; border:0; display:inline-flex; align-items:center; gap:6px; color:#fff; }
        .ltr-btn.blue{background:#2563eb}.ltr-btn.green{background:#16a34a}.ltr-btn.gray{background:#475569}.ltr-btn.amber{background:#d97706}
        .ltr-hint{font-size:12px;color:#64748b}
        .canvas-wrap { overflow:auto; padding-bottom:20px; }
        #ltr-page { position:relative; width:794px; height:1123px; margin:0 auto; background:#fff; box-shadow:0 0 8px rgba(0,0,0,.18);
                    color:#000; font-family:${NAZ}; line-height:1.25; }
        .lbox .field-content { width:100%; height:100%; }
        #ltr-page input.fld, #ltr-page select { border:0; border-bottom:1px dotted #b6c7e6; background:transparent; font:inherit; color:#000; padding:0 2px; width:100%; }
        #ltr-page input.fld::placeholder{color:#aeb8c6}
        #ltr-page select{border-bottom:1px solid #9db8e6;cursor:pointer;font:inherit}
        #ltr-page textarea.area{width:100%;height:100%;border:0;background:transparent;font:inherit;color:#000;resize:none;overflow:hidden;padding:0;box-sizing:border-box;line-height:1.7}
        .sep-line{width:100%;border-top:1px dashed #000}
        .row2{display:flex;gap:5px;justify-content:flex-start}
        .print-val{display:none}
        /* design mode */
        .lbox.dz{outline:1px dashed #93c5fd;cursor:move}
        .lbox.dz .field-content{pointer-events:none}
        .lbox.seld{outline:2px solid #2563eb;background:rgba(37,99,235,.05)}
        .bk-label{position:absolute;top:-15px;right:0;font-size:9px;color:#2563eb;background:#eff6ff;padding:0 3px;border-radius:3px;white-space:nowrap;font-family:sans-serif}
        .rs{position:absolute;left:-4px;bottom:-4px;width:12px;height:12px;background:#2563eb;border:2px solid #fff;border-radius:50%;cursor:nesw-resize}
        .fs-btns{position:absolute;top:-15px;left:0;display:flex;gap:2px}
        .fs-btn{font-size:9px;font-family:sans-serif;border:0;background:#2563eb;color:#fff;border-radius:3px;cursor:pointer;padding:0 3px}
        @media print {
          @page { size:A4; margin:0; }
          html,body{margin:0!important;padding:0!important;background:#fff!important}
          .no-print,.lbox.dz .bk-label,.rs,.fs-btns{display:none!important}
          .canvas-wrap{overflow:visible}
          #ltr-page{box-shadow:none;margin:0}
          .lbox.dz{outline:0}
          /* show typed values as text, hide the form inputs, in print */
          #ltr-page input,#ltr-page select,#ltr-page textarea{display:none!important}
          .print-val{display:inline!important;white-space:pre-wrap}
          #ltr-page .body .print-val{display:block!important}
        }
        `}</style>

        <div className="ltr-controls no-print">
          {!design
            ? <button onClick={() => setDesign(true)} className="ltr-btn amber"><Move size={15} /> چیدمان (جابه‌جایی فیلدها)</button>
            : <button onClick={() => setDesign(false)} className="ltr-btn green"><Check size={15} /> پایانِ چیدمان</button>}
          {design && <button onClick={saveLayout} className="ltr-btn blue">ذخیرهٔ چیدمان</button>}
          {design && <button onClick={resetLayout} className="ltr-btn gray"><RotateCcw size={14} /> بازنشانی</button>}
          <button onClick={() => window.print()} className="ltr-btn blue"><Printer size={15} /> پرینت</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={14} /> پاک‌کردن</button>
          <span className="ltr-hint">{design
            ? 'فیلد را بکش تا جابه‌جا شود · دایرهٔ گوشه = تغییرِ عرض/ارتفاع · A−/A＋ = اندازهٔ فونت · بعد «ذخیرهٔ چیدمان» را بزن.'
            : 'برای جابه‌جایی و تنظیمِ اندازهٔ فیلدها روی «چیدمان» بزن. فونت‌ها از B Nazanin/Titr سیستم خوانده می‌شوند.'}</span>
        </div>

        <div className="canvas-wrap">
          <div id="ltr-page">
            <Box k="logo"><img src={LH_LOGO} alt="" style={{ width: '100%', height: '100%' }} /></Box>
            <Box k="name"><img src={LH_NAME} alt="" style={{ width: '100%', height: '100%' }} /></Box>
            <Box k="footer"><img src={LH_FOOTER} alt="" style={{ width: '100%', height: '100%' }} /></Box>

            <Box k="besmele">بسمه تعالی</Box>

            <Box k="shomareh">شماره : <input dir="ltr" style={{ textAlign: 'right', width: '60%' }} className="fld" value={f.refNo} onChange={set('refNo')} placeholder="2026/----/4/182" />{txt(f.refNo)}</Box>
            <Box k="tarikh">تاریخ&nbsp;: <input dir="ltr" style={{ textAlign: 'right', width: '60%' }} className="fld" value={f.date} onChange={set('date')} placeholder="--/--/2026" />{txt(f.date)}</Box>
            <Box k="peyvast">پیوست : <select className="fld" style={{ width: 'auto' }} value={f.attachment} onChange={set('attachment')}><option>دارد</option><option>ندارد</option></select>{txt(f.attachment)}</Box>

            <Box k="recName"><input className="fld" value={f.recipientName} onChange={set('recipientName')} placeholder="سرکار خانم / جناب آقای …" />{txt(f.recipientName)}</Box>
            <Box k="recTitle"><div className="row2"><input className="fld" style={{ width: '34%' }} value={f.recipientTitle} onChange={set('recipientTitle')} placeholder="رئیس محترم" /><input className="fld" style={{ width: '64%' }} value={f.recipientDept} onChange={set('recipientDept')} placeholder="اداره کل خارجه" /></div>{txt(`${f.recipientTitle} ${f.recipientDept}`)}</Box>

            <Box k="classification">نوع طبقه بندی – <select className="fld" style={{ width: 'auto' }} value={f.classification} onChange={set('classification')}>{CLASSES.map((c) => <option key={c}>{c}</option>)}</select>{txt(f.classification)}</Box>

            <Box k="subject"><span style={{ whiteSpace: 'nowrap' }}>موضوع : </span><input className="fld" style={{ width: '85%' }} value={f.subject} onChange={set('subject')} placeholder="موضوعِ نامه…" />{txt(f.subject)}</Box>

            <Box k="separator"><div className="sep-line" /></Box>

            <Box k="sender"><select className="fld" value={f.sender} onChange={set('sender')}>{SENDERS.map((s) => <option key={s}>{s}</option>)}</select>{txt(f.sender)}</Box>

            <div className="body" style={{ display: 'contents' }}>
              <Box k="body"><textarea className="area" value={f.body} onChange={set('body')} placeholder="متنِ نامه…" />{txt(f.body)}</Box>
            </div>

            <Box k="copyto">رونوشت : <input className="fld" style={{ width: '60%' }} value={f.copyTo} onChange={set('copyTo')} placeholder="------" />{txt(f.copyTo)}</Box>
            <Box k="action">اقدام کننده : <input className="fld" style={{ width: '34%' }} value={f.actionName} onChange={set('actionName')} placeholder="----" /> / داخلی <input dir="ltr" className="fld" style={{ width: '14%', textAlign: 'right' }} value={f.actionExt} onChange={set('actionExt')} placeholder="---" />{txt(`${f.actionName} / داخلی ${f.actionExt}`)}</Box>
          </div>
        </div>
      </div>
    </Layout>
  )
}
