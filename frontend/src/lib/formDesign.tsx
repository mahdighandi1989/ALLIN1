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
  save: () => void
  reset: () => void
  _ref: React.MutableRefObject<Record<string, Boxn>>
}

export function useFormDesign(storageKey: string): DesignState {
  const [layout, setLayout] = useState<Record<string, Boxn>>({})
  const [design, setDesign] = useState(false)
  const [editing, setEditing] = useState<string | null>(null)
  const _ref = useRef(layout)
  useEffect(() => { _ref.current = layout }, [layout])
  useEffect(() => { try { const r = localStorage.getItem(storageKey); if (r) setLayout(JSON.parse(r)) } catch { /* ignore */ } }, [storageKey])
  const setBox = (id: string, patch: Partial<Boxn>) => setLayout((p) => ({ ...p, [id]: { ...p[id], ...patch } }))
  const save = () => { try { localStorage.setItem(storageKey, JSON.stringify(layout)); alert('چیدمان ذخیره شد') } catch { /* ignore */ } }
  const reset = () => { if (confirm('بازگشت به چیدمانِ پیش‌فرض؟ همهٔ جابه‌جایی‌ها پاک می‌شوند.')) { setLayout({}); setEditing(null); localStorage.removeItem(storageKey) } }
  return { layout, design, editing, setDesign, setEditing, setBox, save, reset, _ref }
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
  const startDrag = (e: React.PointerEvent) => {
    if (!d.design) return
    if ((e.target as HTMLElement).closest('.mv-rs')) return
    e.preventDefault(); e.stopPropagation(); d.setEditing(id)
    const sxp = e.clientX, syp = e.clientY, o = d._ref.current[id] || {}
    const ox = o.dx || 0, oy = o.dy || 0
    const mv = (ev: PointerEvent) => d.setBox(id, { dx: Math.round(ox + (ev.clientX - sxp)), dy: Math.round(oy + (ev.clientY - syp)) })
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
    <span className={`mv-wrap${d.design ? ' mv-dz' : ''}${d.editing === id ? ' mv-sel' : ''} ${className || ''}`} style={sx}
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
      {d.design && <button type="button" onClick={d.save} className="mv-btn blue">ذخیرهٔ چیدمان</button>}
      {d.design && <button type="button" onClick={d.reset} className="mv-btn gray">↺ بازنشانی</button>}
      {onPrint && <button type="button" onClick={onPrint} className="mv-btn blue">🖨 پرینت</button>}
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
        .mv-wrap.mv-dz{outline:1px dashed #93c5fd;cursor:move}
        .mv-wrap.mv-sel{outline:2px solid #2563eb;background:rgba(37,99,235,.06)}
        .mv-tag{position:absolute;top:-13px;right:0;font-size:8px;line-height:1;color:#2563eb;background:#eff6ff;padding:1px 3px;border-radius:3px;white-space:nowrap;font-family:sans-serif;pointer-events:none;z-index:5}
        .mv-rs{position:absolute;left:-5px;bottom:-5px;width:12px;height:12px;background:#2563eb;border:2px solid #fff;border-radius:50%;cursor:nesw-resize;z-index:6}
        .mv-pp{position:fixed;top:90px;right:14px;z-index:80;width:230px;background:#fff;border:1px solid #cbd5e1;border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.18);padding:12px;font-family:sans-serif}
        .mv-pp h4{font-size:13px;font-weight:700;margin:0 0 8px;color:#1e3a8a;display:flex;justify-content:space-between;align-items:center}
        .mv-pp .r{display:flex;align-items:center;gap:6px;margin-bottom:7px;font-size:12px;color:#334155}
        .mv-pp .r>label{width:70px;flex:none;color:#64748b}
        .mv-pp input{flex:1;border:1px solid #cbd5e1;border-radius:5px;padding:3px 6px;font-size:12px;min-width:0}
        .mv-pp .x{border:0;background:#ef4444;color:#fff;border-radius:6px;width:24px;height:24px;cursor:pointer;font-size:14px}
        .mv-pp .two{display:flex;gap:6px}.mv-pp .two .r{flex:1}
        .mv-pp .rm{width:100%;border:1px solid #cbd5e1;background:#f8fafc;border-radius:6px;padding:5px;cursor:pointer;font-size:12px;margin-top:2px;color:#334155}
        @media print { .mv-controls,.mv-pp,.mv-tag,.mv-rs{display:none!important} .mv-wrap{outline:0!important;background:transparent!important} }
      `}</style>
      {id && (
        <div className="mv-pp no-print" dir="rtl">
          <h4>تنظیمِ فیلد <button className="x" onClick={() => d.setEditing(null)}>×</button></h4>
          <div className="two">
            <div className="r"><label>افقی X</label><input type="number" value={b.dx || 0} onChange={(e) => d.setBox(id, { dx: +e.target.value || 0 })} /></div>
            <div className="r"><label>عمودی Y</label><input type="number" value={b.dy || 0} onChange={(e) => d.setBox(id, { dy: +e.target.value || 0 })} /></div>
          </div>
          <div className="r"><label>اندازه ٪</label><input type="number" step="5" value={Math.round((b.scale || 1) * 100)} onChange={(e) => d.setBox(id, { scale: Math.max(0.4, (+e.target.value || 100) / 100) })} /></div>
          <div className="two">
            <div className="r"><label>فونت (pt)</label><input type="number" step="0.5" value={b.fontPt || ''} placeholder="—" onChange={(e) => d.setBox(id, { fontPt: +e.target.value || undefined })} /></div>
            <div className="r"><label>فاصلهٔ حروف</label><input type="number" step="0.5" value={b.ls ?? ''} placeholder="—" onChange={(e) => d.setBox(id, { ls: e.target.value === '' ? undefined : +e.target.value })} /></div>
          </div>
          <button className="rm" onClick={() => { d.setBox(id, { dx: 0, dy: 0, scale: 1, fontPt: undefined, ls: undefined }); }}>پاک‌کردنِ تنظیمِ این فیلد</button>
        </div>
      )}
    </>
  )
}
