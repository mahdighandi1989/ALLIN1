'use client'

// Official Bank Saderat LETTER (نامه) with a built-in DRAG & RESIZE layout editor.
// In «چیدمان» (design mode): drag a field by its ✥ handle, resize with the bottom-right
// circle, and quick-tune font (A−/A＋), letter-spacing (ف−/ف＋), body line-height (خ−/خ＋).
// DOUBLE-CLICK any field to open a full properties panel (text/label, font, size, bold,
// alignment, spacing, line-height, width/height, X/Y). Every text field AUTO-SIZES to its
// content, so words sit naturally next to each other with no artificial gaps — like Word.
// Coordinates are px on a fixed A4 canvas (794×1123 px = 210×297 mm @96dpi) → prints 1:1.
// Template (positions + labels) is saved in the browser; «بازنشانی» restores defaults.
// Fonts come from the locally-installed B Nazanin / Titr / B Titr.
import { useState, useRef, useEffect } from 'react'
import Layout from '@/components/Layout'
import { Printer, Eraser, Move, Check, RotateCcw } from 'lucide-react'
import { LH_LOGO, LH_NAME, LH_FOOTER } from './letterhead'

const SENDERS = ['سرپرستی منطقه خلیج فارس', 'دایره تسهیلات اعطایی']
const CLASSES = ['داخلی', 'عادی', 'محرمانه', 'خیلی محرمانه']
const NAZ = "'B Nazanin','BNazanin','Nazanin',serif"
const TITR = "'Titr','B Titr','BTitr','B Nazanin',serif"
const BTITR = "'B Titr','BTitr','Titr','B Nazanin',serif"
const FONTS = [{ v: NAZ, n: 'B Nazanin' }, { v: TITR, n: 'Titr' }, { v: BTITR, n: 'B Titr' }]
const MM = 96 / 25.4 // px per mm at 96dpi
const m = (v: number) => Math.round(v * MM)

// An input that shrinks/grows to exactly fit its text (so adjacent words don't leave gaps).
function AutoInput({ value, onChange, placeholder = '', dir, style, cls = 'fld', readOnly = false }:
  { value: string; onChange?: (e: any) => void; placeholder?: string; dir?: 'ltr' | 'rtl'; style?: React.CSSProperties; cls?: string; readOnly?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null)
  const [w, setW] = useState(() => Math.max(12, String(value || placeholder).length * 9))
  useEffect(() => { if (ref.current) setW(Math.max(8, ref.current.offsetWidth + 3)) }, [value, placeholder])
  return (
    <span style={{ position: 'relative', display: 'inline-block', verticalAlign: 'baseline' }}>
      <span ref={ref} aria-hidden className="az-sizer">{value || placeholder || ' '}</span>
      <input className={cls} dir={dir} value={value} onChange={onChange} placeholder={placeholder} readOnly={readOnly} style={{ width: w, ...style }} />
    </span>
  )
}

// Default layout (px) — measured from the bank's PDF. {x,y,w[,h],size,font,bold,align,ls,lh}
type Boxn = { x: number; y: number; w: number; h?: number; size: number; font?: string; bold?: boolean; align?: 'right' | 'center' | 'left'; ls?: number; lh?: number }
const DEFAULT_LAYOUT: Record<string, Boxn> = {
  logo: { x: m(4.8), y: m(4), w: m(28.5), h: m(27.6), size: 0 },
  name: { x: m(138.8), y: m(6.3), w: m(65.8), h: m(20.4), size: 0 },
  footer: { x: m(22.2), y: m(277.2), w: m(167.4), h: m(17.7), size: 0 },
  besmele: { x: m(85), y: m(29), w: m(40), size: 13, font: NAZ, align: 'center' },
  shomareh: { x: m(8), y: m(44.8), w: m(62), size: 12, font: NAZ, align: 'right' },
  tarikh: { x: m(8), y: m(51), w: m(62), size: 12, font: NAZ, align: 'right' },
  peyvast: { x: m(20), y: m(57.3), w: m(50), size: 12, font: NAZ, align: 'right' },
  recName: { x: m(128.2), y: m(57.6), w: m(62), size: 12, font: BTITR, bold: true, align: 'right' },
  recTitle: { x: m(118), y: m(65), w: m(72), size: 12, font: BTITR, bold: true, align: 'right' },
  classification: { x: m(16), y: m(66.8), w: m(54), size: 11, font: NAZ, bold: true, align: 'right' },
  subject: { x: m(28), y: m(78), w: m(162.5), size: 12, font: TITR, align: 'right' },
  separator: { x: m(133.8), y: m(107), w: m(56.7), h: 1, size: 0 },
  sender: { x: m(35.5), y: m(141.7), w: m(55), size: 13, font: BTITR, bold: true, align: 'center' },
  body: { x: m(25), y: m(149), w: m(160), h: m(95), size: 13, font: NAZ, align: 'right', lh: 1.7 },
  copyto: { x: m(124.7), y: m(250), w: m(60), size: 10, font: NAZ, align: 'right' },
  action: { x: m(93.8), y: m(264), w: m(90), size: 10, font: NAZ, align: 'right' },
}
// Editable label/prefix text for each field (the user can change these in the panel)
const DEFAULT_LABELS: Record<string, string> = {
  besmele: 'بسمه تعالی',
  shomareh: 'شماره : ', tarikh: 'تاریخ : ', peyvast: 'پیوست : ',
  classification: 'نوع طبقه بندی – ', subject: 'موضوع : ',
  copyto: 'رونوشت : ', action: 'اقدام کننده : ', actionExt: ' / داخلی ',
}
const LS_KEY = 'letterTemplate_v3'

function todayYMD() { const d = new Date(); const p = (n: number) => String(n).padStart(2, '0'); return `${d.getFullYear()}/${p(d.getMonth() + 1)}/${p(d.getDate())}` }

export default function LetterPage() {
  const [f, setF] = useState({
    classification: 'داخلی', serial: '----', year: String(new Date().getFullYear()),
    date: todayYMD(), attachment: 'دارد',
    recipientName: '', recipientTitle: 'رئیس محترم', recipientDept: '', subject: '', body: '',
    sender: SENDERS[0], copyTo: '', actionName: '', actionExt: '',
  })
  const set = (k: keyof typeof f) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const [L, setL] = useState<Record<string, Boxn>>(DEFAULT_LAYOUT)
  const [labels, setLabels] = useState<Record<string, string>>(DEFAULT_LABELS)
  const [design, setDesign] = useState(false)
  const [sel, setSel] = useState<string | null>(null)
  const [editing, setEditing] = useState<string | null>(null) // field whose properties panel is open
  const LRef = useRef(L); useEffect(() => { LRef.current = L }, [L]) // always-fresh layout for drag/resize

  useEffect(() => {
    try { const raw = localStorage.getItem(LS_KEY); if (raw) { const o = JSON.parse(raw); if (o.L) setL({ ...DEFAULT_LAYOUT, ...o.L }); if (o.labels) setLabels({ ...DEFAULT_LABELS, ...o.labels }) } } catch { /* ignore */ }
  }, [])
  const saveTemplate = () => { try { localStorage.setItem(LS_KEY, JSON.stringify({ L, labels })); alert('چیدمان ذخیره شد') } catch { /* ignore */ } }
  const resetTemplate = () => { if (confirm('بازگشت به چیدمانِ پیش‌فرض؟')) { setL(DEFAULT_LAYOUT); setLabels(DEFAULT_LABELS); setEditing(null); localStorage.removeItem(LS_KEY) } }
  const setBox = (k: string, patch: Partial<Boxn>) => setL((p) => ({ ...p, [k]: { ...p[k], ...patch } }))
  const bump = (k: string, d: number) => setBox(k, { size: Math.max(6, (L[k].size || 12) + d) })
  const spc = (k: string, d: number) => setBox(k, { ls: Math.max(0, Math.round(((L[k].ls || 0) + d) * 10) / 10) })
  const lnh = (k: string, d: number) => setBox(k, { lh: Math.max(1, Math.round(((L[k].lh || 1.7) + d) * 10) / 10) })

  // drag (via ✥ handle) — read the live position from LRef so there is no stale capture.
  const startDrag = (k: string) => (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation(); setSel(k)
    const sx = e.clientX, sy = e.clientY, o = { x: LRef.current[k].x, y: LRef.current[k].y }
    const mv = (ev: PointerEvent) => setL((p) => ({ ...p, [k]: { ...p[k], x: Math.round(o.x + (ev.clientX - sx)), y: Math.round(o.y + (ev.clientY - sy)) } }))
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  // resize (bottom-right handle) — drag right/down to grow (natural direction).
  const startResize = (k: string) => (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation(); setSel(k)
    const sx = e.clientX, sy = e.clientY, o = { ...LRef.current[k] }
    const mv = (ev: PointerEvent) => setL((p) => ({ ...p, [k]: { ...p[k], w: Math.max(20, Math.round(o.w + (ev.clientX - sx))), ...(o.h != null ? { h: Math.max(8, Math.round((o.h || 0) + (ev.clientY - sy))) } : {}) } }))
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  const openPanel = (k: string) => { setSel(k); setEditing(k); setDesign(true) }
  const exitEditing = () => { setEditing(null); setDesign(false); setSel(null) } // dbl-click empty area → back to normal

  const boxStyle = (k: string): React.CSSProperties => {
    const b = L[k]
    return {
      position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h,
      fontFamily: b.font, fontSize: b.size ? `${b.size}pt` : undefined, fontWeight: b.bold ? 700 : undefined,
      textAlign: b.align, letterSpacing: b.ls ? `${b.ls}px` : undefined, lineHeight: b.lh || undefined,
      whiteSpace: k === 'subject' || k === 'body' ? 'normal' : 'nowrap',
    }
  }

  // editable label/prefix: real auto-sized text on screen & print, editable only in design mode
  const Lbl = ({ k }: { k: string }) => (<>
    <AutoInput cls="lbl-in" value={labels[k] ?? ''} readOnly={!design} onChange={(e) => setLabels((p) => ({ ...p, [k]: e.target.value }))} />
    <span className="print-val">{labels[k]}</span>
  </>)

  const Box = ({ k, children }: { k: string; children?: React.ReactNode }) => {
    const b = L[k]
    return (
      <div className={`lbox${design ? ' dz' : ''}${sel === k && design ? ' seld' : ''}`} style={boxStyle(k)}
        onPointerDown={() => design && setSel(k)} onDoubleClick={(e) => { e.stopPropagation(); openPanel(k) }}>
        <div className="field-content">{children}</div>
        {design && <>
          <span className="bk-label">{k}</span>
          <span className="mv" onPointerDown={startDrag(k)} title="جابه‌جایی"><Move size={11} /></span>
          <span className="rs" onPointerDown={startResize(k)} title="تغییر اندازه" />
          {sel === k && b.size > 0 && <span className="fs-btns" onPointerDown={(e) => e.stopPropagation()}>
            <button className="fs-btn" onClick={() => bump(k, -1)}>A−</button>
            <button className="fs-btn" onClick={() => bump(k, +1)}>A＋</button>
            <button className="fs-btn" onClick={() => spc(k, -0.5)}>ف−</button>
            <button className="fs-btn" onClick={() => spc(k, +0.5)}>ف＋</button>
            {k === 'body' && <><button className="fs-btn" onClick={() => lnh(k, -0.1)}>خ−</button><button className="fs-btn" onClick={() => lnh(k, +0.1)}>خ＋</button></>}
          </span>}
        </>}
      </div>
    )
  }

  const txt = (v: string, ltr = false) => <span className="print-val" dir={ltr ? 'ltr' : undefined}>{v}</span>
  const eb = editing ? L[editing] : null

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
        /* no underlines/borders on any field — clean like Word; fields auto-size to text */
        #ltr-page input.fld, #ltr-page select, #ltr-page .lbl-in { border:0; background:transparent; font:inherit; color:#000; padding:0; }
        #ltr-page .lbl-in,#ltr-page input.fld{text-align:inherit;letter-spacing:inherit}
        #ltr-page select{cursor:pointer;width:auto}
        #ltr-page input.fld::placeholder{color:#c7cfdb}
        #ltr-page input.fld:focus, #ltr-page textarea.area:focus, #ltr-page .lbl-in:focus{background:rgba(37,99,235,.08);border-radius:2px;outline:none}
        #ltr-page textarea.area{width:100%;height:100%;border:0;background:transparent;font:inherit;color:#000;resize:none;overflow:hidden;padding:0;box-sizing:border-box;line-height:inherit}
        .az-sizer{position:absolute;visibility:hidden;white-space:pre;top:0;right:0;font:inherit;letter-spacing:inherit;pointer-events:none}
        .sep-line{width:100%;border-top:1px dashed #000}
        .print-val{display:none}
        /* design mode */
        .lbox.dz{outline:1px dashed #93c5fd}
        .lbox.seld{outline:2px solid #2563eb;background:rgba(37,99,235,.05)}
        .bk-label{position:absolute;top:-15px;right:0;font-size:9px;color:#2563eb;background:#eff6ff;padding:0 3px;border-radius:3px;white-space:nowrap;font-family:sans-serif}
        .mv{position:absolute;top:-9px;left:-9px;width:18px;height:18px;background:#2563eb;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:move;z-index:6}
        .rs{position:absolute;right:-5px;bottom:-5px;width:13px;height:13px;background:#2563eb;border:2px solid #fff;border-radius:50%;cursor:nwse-resize;z-index:6}
        .fs-btns{position:absolute;bottom:-17px;left:0;display:flex;gap:2px;z-index:7}
        .fs-btn{font-size:9px;font-family:sans-serif;border:0;background:#2563eb;color:#fff;border-radius:3px;cursor:pointer;padding:1px 4px}
        /* properties panel (double-click) */
        .pp{position:fixed;top:118px;right:16px;z-index:60;width:250px;background:#fff;border:1px solid #cbd5e1;border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.18);padding:12px;font-family:sans-serif}
        .pp h4{font-size:13px;font-weight:700;margin:0 0 8px;color:#1e3a8a;display:flex;justify-content:space-between;align-items:center}
        .pp .row{display:flex;align-items:center;gap:6px;margin-bottom:7px;font-size:12px;color:#334155}
        .pp .row>label{width:62px;flex:none;color:#64748b}
        .pp input,.pp select{flex:1;border:1px solid #cbd5e1;border-radius:5px;padding:3px 5px;font-size:12px;min-width:0;background:#fff;color:#0f172a}
        .pp input[type=checkbox]{flex:none;width:16px;height:16px}
        .pp .seg{display:flex;gap:3px;flex:1}
        .pp .seg button{flex:1;border:1px solid #cbd5e1;background:#f8fafc;border-radius:5px;padding:3px;cursor:pointer;font-size:11px;color:#334155}
        .pp .seg button.on{background:#2563eb;color:#fff;border-color:#2563eb}
        .pp .x{border:0;background:#ef4444;color:#fff;border-radius:6px;width:24px;height:24px;cursor:pointer;font-size:15px;line-height:1}
        .pp .two{display:flex;gap:8px}.pp .two .row{flex:1}
        @media print {
          @page { size:A4; margin:0; }
          html,body{margin:0!important;padding:0!important;background:#fff!important}
          .no-print,.bk-label,.mv,.rs,.fs-btns,.pp{display:none!important}
          .canvas-wrap{overflow:visible}
          #ltr-page{box-shadow:none;margin:0}
          .lbox.dz,.lbox.seld{outline:0;background:transparent}
          /* show typed values as text, hide the editor inputs, in print */
          #ltr-page input,#ltr-page select,#ltr-page textarea{display:none!important}
          .print-val{display:inline!important;white-space:pre-wrap}
          #ltr-page .body .print-val{display:block!important}
        }
        `}</style>

        <div className="ltr-controls no-print">
          {!design
            ? <button onClick={() => setDesign(true)} className="ltr-btn amber"><Move size={15} /> چیدمان (جابه‌جایی فیلدها)</button>
            : <button onClick={() => { setDesign(false); setEditing(null) }} className="ltr-btn green"><Check size={15} /> پایانِ چیدمان</button>}
          {design && <button onClick={saveTemplate} className="ltr-btn blue">ذخیرهٔ چیدمان</button>}
          {design && <button onClick={resetTemplate} className="ltr-btn gray"><RotateCcw size={14} /> بازنشانی</button>}
          <button onClick={() => window.print()} className="ltr-btn blue"><Printer size={15} /> پرینت</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={14} /> پاک‌کردن</button>
          <span className="ltr-hint">{design
            ? 'دستهٔ ✥ = جابه‌جایی · دایرهٔ گوشه = عرض/ارتفاع · A/ف/خ = فونت/فاصلهٔ حروف/فاصلهٔ خط · دبل‌کلیک روی هر فیلد = تنظیمِ کاملِ آن فیلد · بعد «ذخیرهٔ چیدمان».'
            : 'برای جابه‌جایی/تنظیم روی «چیدمان» بزن، یا روی هر فیلد دبل‌کلیک کن. فونت‌ها از B Nazanin/Titr سیستم خوانده می‌شوند.'}</span>
        </div>

        {editing && eb && (
          <div className="pp no-print">
            <h4>تنظیمِ فیلد: {editing} <button className="x" onClick={() => setEditing(null)}>×</button></h4>
            {labels[editing] !== undefined && (
              <div className="row"><label>متن/برچسب</label><input value={labels[editing]} onChange={(e) => setLabels((p) => ({ ...p, [editing]: e.target.value }))} /></div>
            )}
            {eb.size > 0 && <>
              <div className="row"><label>فونت</label><select value={eb.font || NAZ} onChange={(e) => setBox(editing, { font: e.target.value })}>{FONTS.map((ft) => <option key={ft.n} value={ft.v}>{ft.n}</option>)}</select></div>
              <div className="two">
                <div className="row"><label>اندازه</label><input type="number" value={eb.size} onChange={(e) => setBox(editing, { size: +e.target.value || 0 })} /></div>
                <div className="row"><label style={{ width: 'auto' }}>توپُر</label><input type="checkbox" checked={!!eb.bold} onChange={(e) => setBox(editing, { bold: e.target.checked })} /></div>
              </div>
              <div className="row"><label>چینش</label><div className="seg">{(['right', 'center', 'left'] as const).map((a) => <button key={a} className={eb.align === a ? 'on' : ''} onClick={() => setBox(editing, { align: a })}>{a === 'right' ? 'راست' : a === 'center' ? 'وسط' : 'چپ'}</button>)}</div></div>
              <div className="two">
                <div className="row"><label>فاصلهٔ حروف</label><input type="number" step="0.5" value={eb.ls || 0} onChange={(e) => setBox(editing, { ls: +e.target.value || 0 })} /></div>
                <div className="row"><label>فاصلهٔ خط</label><input type="number" step="0.1" value={eb.lh || 1.25} onChange={(e) => setBox(editing, { lh: +e.target.value || undefined })} /></div>
              </div>
            </>}
            <div className="two">
              <div className="row"><label>عرض</label><input type="number" value={eb.w} onChange={(e) => setBox(editing, { w: +e.target.value || 0 })} /></div>
              {eb.h != null && <div className="row"><label>ارتفاع</label><input type="number" value={eb.h} onChange={(e) => setBox(editing, { h: +e.target.value || 0 })} /></div>}
            </div>
            <div className="two">
              <div className="row"><label>افقی X</label><input type="number" value={eb.x} onChange={(e) => setBox(editing, { x: +e.target.value || 0 })} /></div>
              <div className="row"><label>عمودی Y</label><input type="number" value={eb.y} onChange={(e) => setBox(editing, { y: +e.target.value || 0 })} /></div>
            </div>
            <button className="ltr-btn blue" style={{ width: '100%', justifyContent: 'center', marginTop: 4 }} onClick={saveTemplate}>ذخیرهٔ چیدمان</button>
          </div>
        )}

        <div className="canvas-wrap" onDoubleClick={exitEditing}>
          <div id="ltr-page">
            <Box k="logo"><img src={LH_LOGO} alt="" style={{ width: '100%', height: '100%' }} /></Box>
            <Box k="name"><img src={LH_NAME} alt="" style={{ width: '100%', height: '100%' }} /></Box>
            <Box k="footer"><img src={LH_FOOTER} alt="" style={{ width: '100%', height: '100%' }} /></Box>

            <Box k="besmele"><Lbl k="besmele" /></Box>

            <Box k="shomareh"><Lbl k="shomareh" /><span dir="ltr" style={{ direction: 'ltr', unicodeBidi: 'isolate' }}>182 / 4 / <AutoInput dir="ltr" value={f.serial} onChange={set('serial')} placeholder="----" style={{ textAlign: 'center' }} /> / <AutoInput dir="ltr" value={f.year} onChange={set('year')} placeholder="2026" style={{ textAlign: 'center' }} /></span>{txt(`182 / 4 / ${f.serial} / ${f.year}`, true)}</Box>
            <Box k="tarikh"><Lbl k="tarikh" /><AutoInput dir="ltr" value={f.date} onChange={set('date')} placeholder="2026/--/--" style={{ textAlign: 'right' }} />{txt(f.date, true)}</Box>
            <Box k="peyvast"><Lbl k="peyvast" /><select className="fld" value={f.attachment} onChange={set('attachment')}><option>دارد</option><option>ندارد</option></select>{txt(f.attachment)}</Box>

            <Box k="recName"><AutoInput value={f.recipientName} onChange={set('recipientName')} placeholder="سرکار خانم / جناب آقای …" />{txt(f.recipientName)}</Box>
            <Box k="recTitle"><AutoInput value={f.recipientTitle} onChange={set('recipientTitle')} placeholder="رئیس محترم" /> <AutoInput value={f.recipientDept} onChange={set('recipientDept')} placeholder="اداره کل خارجه" />{txt(`${f.recipientTitle} ${f.recipientDept}`)}</Box>

            <Box k="classification"><Lbl k="classification" /><select className="fld" value={f.classification} onChange={set('classification')}>{CLASSES.map((c) => <option key={c}>{c}</option>)}</select>{txt(f.classification)}</Box>

            <Box k="subject"><Lbl k="subject" /><AutoInput value={f.subject} onChange={set('subject')} placeholder="موضوعِ نامه…" />{txt(f.subject)}</Box>

            <Box k="separator"><div className="sep-line" /></Box>

            <Box k="sender"><select className="fld" value={f.sender} onChange={set('sender')}>{SENDERS.map((s) => <option key={s}>{s}</option>)}</select>{txt(f.sender)}</Box>

            <div className="body" style={{ display: 'contents' }}>
              <Box k="body"><textarea className="area" value={f.body} onChange={set('body')} onDoubleClick={(e) => e.stopPropagation()} placeholder="متنِ نامه…" />{txt(f.body)}</Box>
            </div>

            <Box k="copyto"><Lbl k="copyto" /><AutoInput value={f.copyTo} onChange={set('copyTo')} placeholder="------" />{txt(f.copyTo)}</Box>
            <Box k="action"><Lbl k="action" /><AutoInput value={f.actionName} onChange={set('actionName')} placeholder="----" /><span className="print-val">{f.actionName}</span><Lbl k="actionExt" /><AutoInput dir="ltr" value={f.actionExt} onChange={set('actionExt')} placeholder="---" style={{ textAlign: 'right' }} /><span className="print-val" dir="ltr">{f.actionExt}</span></Box>
          </div>
        </div>
      </div>
    </Layout>
  )
}
