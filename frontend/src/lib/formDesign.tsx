'use client'

// Reusable drag / resize / double-click layout editor for ANY existing form —
// without rebuilding it. Wrap a field in <Movable d={d} id="...">…</Movable>:
//   • In «چیدمان» (design) mode you drag it (CSS translate — no reflow), resize it
//     with the corner handle (uniform scale), and double-click it to open a panel
//     to set exact offset X/Y, size %, font size and letter-spacing.
//   • The per-form layout is saved in the browser (localStorage) and re-applied
//     (including in print). «بازنشانی» clears it.
//   • DEFAULT IS NO CHANGE: with no saved tweak and not in design mode, Movable
//     renders its children verbatim, so a form's carefully-matched layout is left
//     exactly as-is until the user chooses to move something.
import { useState, useEffect, useRef } from 'react'

export type Boxn = { dx?: number; dy?: number; scale?: number; fontPt?: number; ls?: number }
export type DesignState = {
  layout: Record<string, Boxn>
  design: boolean
  editing: string | null
  setDesign: (b: boolean) => void
  setEditing: (s: string | null) => void
  setBox: (id: string, patch: Partial<Boxn>) => void
  // v131 — apply MANY boxes in one state update. A group drag moves every
  // field below the one being dragged, so per-field setBox calls would queue
  // dozens of updates per pointermove and stutter.
  setBoxes: (patch: Record<string, Partial<Boxn>>) => void
  save: () => void
  reset: () => void
  _ref: React.MutableRefObject<Record<string, Boxn>>
  acct: string
  // v120 — SHEET METRICS: page-level numbers a form exposes for hand-tuning
  // (e.g. slip height, gap between slips, signature offset — all in mm). They
  // are NOT per-field boxes, so they live in their own `<key>__nums` record and
  // follow the same base/account scoping, saving and reset as the layout.
  nums: Record<string, number>
  setNum: (id: string, v: number | undefined) => void
}

// SCOPING (owner rule): pass the current account number as `account`. While
// the form belongs to an account (loaded or just typed, saved or not), edits
// live in `<storageKey>::<account>` and the base template (`<storageKey>`)
// stays untouched; only on a pristine form do edits update the base template.
// The rendered layout is base + the account's own tweaks (account wins per
// field, merged per property so a base font tweak survives an account offset).
export function useFormDesign(storageKey: string, account?: string): DesignState {
  const acct = (account || '').trim()
  const KEY = acct ? `${storageKey}::${acct}` : storageKey
  const NKEY = `${KEY}__nums`
  const [own, setOwn] = useState<Record<string, Boxn>>({})
  const [base, setBase] = useState<Record<string, Boxn>>({})
  const [ownN, setOwnN] = useState<Record<string, number>>({})
  const [baseN, setBaseN] = useState<Record<string, number>>({})
  const [design, setDesign] = useState(false)
  const [editing, setEditing] = useState<string | null>(null)
  const layout: Record<string, Boxn> = acct
    ? (() => { const m: Record<string, Boxn> = { ...base }; for (const k in own) m[k] = { ...(base[k] || {}), ...own[k] }; return m })()
    : own
  const nums: Record<string, number> = acct ? { ...baseN, ...ownN } : ownN
  const _ref = useRef(layout)
  useEffect(() => { _ref.current = layout })
  useEffect(() => {
    try { const r = localStorage.getItem(KEY); setOwn(r ? JSON.parse(r) : {}) } catch { setOwn({}) }
    try { const r = localStorage.getItem(NKEY); setOwnN(r ? JSON.parse(r) : {}) } catch { setOwnN({}) }
    if (acct) {
      try { const r = localStorage.getItem(storageKey); setBase(r ? JSON.parse(r) : {}) } catch { setBase({}) }
      try { const r = localStorage.getItem(`${storageKey}__nums`); setBaseN(r ? JSON.parse(r) : {}) } catch { setBaseN({}) }
    } else { setBase({}); setBaseN({}) }
    setEditing(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey, acct])
  const setBox = (id: string, patch: Partial<Boxn>) => setOwn((p) => ({ ...p, [id]: { ...p[id], ...patch } }))
  const setBoxes = (patch: Record<string, Partial<Boxn>>) => setOwn((p) => {
    const n = { ...p }
    for (const k in patch) n[k] = { ...n[k], ...patch[k] }
    return n
  })
  // undefined / NaN clears the override so the form's built-in default returns
  const setNum = (id: string, v: number | undefined) => setOwnN((p) => {
    const n = { ...p }
    if (v === undefined || !Number.isFinite(v)) delete n[id]; else n[id] = v
    return n
  })
  const save = () => {
    try {
      localStorage.setItem(KEY, JSON.stringify(own))
      if (Object.keys(ownN).length) localStorage.setItem(NKEY, JSON.stringify(ownN))
      else localStorage.removeItem(NKEY)
      alert(acct ? `چیدمان فقط برای حسابِ ${acct} ذخیره شد — قالبِ اصلی دست‌نخورده ماند` : 'چیدمانِ قالبِ اصلی ذخیره شد')
    } catch { /* ignore */ }
  }
  const reset = () => {
    if (confirm(acct ? `چیدمانِ سفارشیِ حسابِ ${acct} پاک شود؟ (قالبِ اصلی دست نمی‌خورد)` : 'بازگشت به چیدمانِ پیش‌فرض؟ همۀ جابه‌جایی‌ها پاک می‌شوند.')) {
      setOwn({}); setOwnN({}); setEditing(null)
      try { localStorage.removeItem(KEY); localStorage.removeItem(NKEY) } catch { /* ignore */ }
    }
  }
  return { layout, design, editing, setDesign, setEditing, setBox, setBoxes, save, reset, _ref, acct, nums, setNum }
}

function hasTweak(b?: Boxn) { return !!b && !!(b.dx || b.dy || (b.scale && b.scale !== 1) || b.fontPt || b.ls) }

export function Movable({ d, id, children, block = false, label, style, className }:
  { d: DesignState; id: string; children: React.ReactNode; block?: boolean; label?: string; style?: React.CSSProperties; className?: string }) {
  const b = d.layout[id]
  // Transparent by default — zero layout impact until the user tweaks/designs.
  if (!d.design && !hasTweak(b)) {
    if (!style && !className) return <>{children}</>
    return <span className={className} style={{ ...style, display: block ? 'block' : 'inline-block' }}>{children}</span>
  }
  const sx: React.CSSProperties = {
    ...style,
    display: block ? 'block' : 'inline-block',
    position: 'relative',
    transform: `translate(${b?.dx || 0}px, ${b?.dy || 0}px) scale(${b?.scale || 1})`,
    transformOrigin: 'top right',
    fontSize: b?.fontPt ? `${b.fontPt}pt` : style?.fontSize,
    letterSpacing: b?.ls != null ? `${b.ls}px` : style?.letterSpacing,
    zIndex: d.editing === id ? 30 : undefined,
  }
  // v131 — GROUP DRAG (owner: «اگر جایی از سند را کشیدم، بقیهٔ فیلدها خودکار با آن
  // تنظیم شوند»). Movable positions with `transform`, which does NOT reflow, so
  // dragging one field used to slide it straight over its neighbours. Now a
  // VERTICAL drag carries every field that comes after it inside the same group
  // (`.mv-group`, i.e. one slip) — the document opens up or closes like text,
  // instead of overlapping. Horizontal movement stays local to the dragged field:
  // nudging one value sideways must not shove the whole column.
  // Hold ALT to move the single field on its own.
  const startDrag = (e: React.PointerEvent) => {
    if (!d.design) return
    if ((e.target as HTMLElement).closest('.mv-rs')) return
    e.preventDefault(); e.stopPropagation(); d.setEditing(id)
    const sxp = e.clientX, syp = e.clientY, o = d._ref.current[id] || {}
    const ox = o.dx || 0, oy = o.dy || 0

    // Followers = every Movable AFTER this one in document order, within the
    // nearest `.mv-group` (falls back to the whole page when a form marks none).
    const self = e.currentTarget as HTMLElement
    const scope = (self.closest('.mv-group') as HTMLElement | null) || document.body
    const all = Array.from(scope.querySelectorAll<HTMLElement>('[data-mvid]'))
    const at = all.indexOf(self)
    const followers = e.altKey || at < 0 ? [] : all.slice(at + 1)
      .map((n) => n.dataset.mvid || '').filter(Boolean)
    const origin: Record<string, number> = {}
    for (const fid of followers) origin[fid] = d._ref.current[fid]?.dy || 0

    const mv = (ev: PointerEvent) => {
      const ddx = Math.round(ev.clientX - sxp), ddy = Math.round(ev.clientY - syp)
      if (!followers.length) { d.setBox(id, { dx: ox + ddx, dy: oy + ddy }); return }
      const patch: Record<string, Partial<Boxn>> = { [id]: { dx: ox + ddx, dy: oy + ddy } }
      for (const fid of followers) patch[fid] = { dy: origin[fid] + ddy }
      d.setBoxes(patch)
    }
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  const startResize = (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation(); d.setEditing(id)
    const sxp = e.clientX, o = d._ref.current[id] || {}, os = o.scale || 1
    const mv = (ev: PointerEvent) => d.setBox(id, { scale: Math.max(0.4, Math.round((os + (ev.clientX - sxp) / 160) * 100) / 100) })
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  return (
    <span data-mvid={id} className={`mv-wrap${d.design ? ' mv-dz' : ''}${d.editing === id ? ' mv-sel' : ''} ${className || ''}`} style={sx}
      onPointerDown={startDrag} onDoubleClick={(e) => { e.stopPropagation(); d.setEditing(id) }}>
      {children}
      {d.design && <>
        <span className="mv-tag">{label || id}</span>
        <span className="mv-rs" onPointerDown={startResize} title="تغییر اندازه" />
      </>}
    </span>
  )
}

// Toolbar buttons — drop into a page's no-print controls area.
export function DesignControls({ d, onPrint }: { d: DesignState; onPrint?: () => void }) {
  return (
    <span className="mv-controls no-print">
      {!d.design
        ? <button type="button" onClick={() => d.setDesign(true)} className="mv-btn amber">✥ چیدمان</button>
        : <button type="button" onClick={() => { d.setDesign(false); d.setEditing(null) }} className="mv-btn green">✓ پایانِ چیدمان</button>}
      {d.design && <button type="button" onClick={d.save} className="mv-btn blue">ذخیرۀ چیدمان</button>}
      {d.design && <button type="button" onClick={d.reset} className="mv-btn gray">↺ بازنشانی</button>}
      {onPrint && <button type="button" onClick={onPrint} className="mv-btn blue">🖨 پرینت</button>}
      {d.design && (
        <span className="mv-scope" dir="rtl">
          {d.acct
            ? <>چینش فقط برای حسابِ <b dir="ltr">{d.acct}</b> — قالبِ اصلی دست‌نخورده می‌ماند</>
            : 'فرم خالی است — تغییرِ چینش، قالبِ اصلی را به‌روز می‌کند'}
        </span>
      )}
    </span>
  )
}

// Floating per-field panel + the shared styles. Render ONCE per page.
export function DesignPanel({ d }: { d: DesignState }) {
  const id = d.editing
  const b: Boxn = (id && d.layout[id]) || {}
  return (
    <>
      <style>{`
        .mv-controls{display:inline-flex;gap:6px;align-items:center;flex-wrap:wrap}
        .mv-btn{padding:6px 10px;border-radius:6px;font-weight:600;cursor:pointer;border:0;color:#fff;font-size:13px}
        .mv-btn.amber{background:#d97706}.mv-btn.green{background:#16a34a}.mv-btn.blue{background:#2563eb}.mv-btn.gray{background:#475569}
        .mv-scope{font-size:11px;color:#64748b}
        .mv-wrap.mv-dz{outline:1px dashed #93c5fd;cursor:move}
        .mv-wrap.mv-sel{outline:2px solid #2563eb;background:rgba(37,99,235,.06)}
        .mv-tag{position:absolute;top:-13px;right:0;font-size:8px;line-height:1;color:#2563eb;background:#eff6ff;padding:1px 3px;border-radius:3px;white-space:nowrap;font-family:sans-serif;pointer-events:none;z-index:5}
        .mv-rs{position:absolute;left:-5px;bottom:-5px;width:12px;height:12px;background:#2563eb;border:2px solid #fff;border-radius:50%;cursor:nesw-resize;z-index:6}
        /* v131 — the two-column rows used to burst OUT of the panel (measured in a
           real browser: each .r stayed ~240px inside a 206px box, so the second
           column rendered off the left edge). A flex item's automatic minimum is
           its content's min-content size, and an <input> carries a large intrinsic
           width — a min-width of 0 on the input alone does not release the ROW, so
           every level in the chain needs it. The panel also caps to the viewport
           and scrolls, so it can never spill off-screen on a short window. */
        .mv-pp{position:fixed;top:90px;right:14px;z-index:80;box-sizing:border-box;
               width:min(268px,calc(100vw - 28px));max-height:calc(100vh - 110px);overflow:auto;
               background:#fff;border:1px solid #cbd5e1;border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.18);padding:12px;font-family:sans-serif}
        .mv-pp h4{font-size:13px;font-weight:700;margin:0 0 8px;color:#1e3a8a;display:flex;justify-content:space-between;align-items:center}
        .mv-pp .r{display:flex;align-items:center;gap:6px;margin-bottom:7px;font-size:12px;color:#334155;min-width:0}
        .mv-pp .r>label{flex:0 1 auto;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .mv-pp input{flex:1 1 0;width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:5px;padding:3px 6px;font-size:12px;min-width:0}
        .mv-pp .x{border:0;background:#ef4444;color:#fff;border-radius:6px;width:24px;height:24px;cursor:pointer;font-size:14px;flex:none}
        .mv-pp .hint{font-size:10.5px;line-height:1.5;color:#64748b;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:5px 6px;margin:2px 0 7px}
        .mv-pp .two{display:flex;gap:6px;min-width:0}.mv-pp .two .r{flex:1 1 0;min-width:0}
        .mv-pp .rm{width:100%;border:1px solid #cbd5e1;background:#f8fafc;border-radius:6px;padding:5px;cursor:pointer;font-size:12px;margin-top:2px;color:#334155}
        @media print { .mv-controls,.mv-pp,.mv-tag,.mv-rs{display:none!important} .mv-wrap{outline:0!important;background:transparent!important} }
      `}</style>
      {id && (
        <div className="mv-pp no-print" dir="rtl">
          <h4>تنظیمِ فیلد <button className="x" onClick={() => d.setEditing(null)}>×</button></h4>
          <div className="hint">با ماوس بکش تا جابه‌جا شود؛ جابه‌جاییِ عمودی، همهٔ قسمت‌های پایین‌تر را هم با خودش می‌برد. برای جابه‌جاییِ فقط همین یکی، کلیدِ Alt را نگه دار. گوشهٔ آبی = تغییرِ اندازه.</div>
          <div className="two">
            <div className="r"><label>افقی X</label><input type="number" value={b.dx || 0} onChange={(e) => d.setBox(id, { dx: +e.target.value || 0 })} /></div>
            <div className="r"><label>عمودی Y</label><input type="number" value={b.dy || 0} onChange={(e) => d.setBox(id, { dy: +e.target.value || 0 })} /></div>
          </div>
          <div className="r"><label>اندازه ٪</label><input type="number" step="5" value={Math.round((b.scale || 1) * 100)} onChange={(e) => d.setBox(id, { scale: Math.max(0.4, (+e.target.value || 100) / 100) })} /></div>
          <div className="two">
            <div className="r"><label>فونت (pt)</label><input type="number" step="0.5" value={b.fontPt || ''} placeholder="—" onChange={(e) => d.setBox(id, { fontPt: +e.target.value || undefined })} /></div>
            <div className="r"><label>فاصلۀ حروف</label><input type="number" step="0.5" value={b.ls ?? ''} placeholder="—" onChange={(e) => d.setBox(id, { ls: e.target.value === '' ? undefined : +e.target.value })} /></div>
          </div>
          <button className="rm" onClick={() => { d.setBox(id, { dx: 0, dy: 0, scale: 1, fontPt: undefined, ls: undefined }); }}>پاک‌کردنِ تنظیمِ این فیلد</button>
        </div>
      )}
    </>
  )
}
