'use client'

// Shared dblclick/«چیدمان» layout-override system for printable FORM pages
// (credit-file, sanction, voucher, …) — the exact pattern proven on the
// official-letter and offer-letter pages:
//  - double-click any block in the print preview → floating panel adjusts
//    font / bold / align / direction / line & letter spacing / offsets / width;
//  - a global «چیدمان» toolbar toggle: hover highlights the block under the
//    cursor and a SINGLE click opens the same panel;
//  - overrides are keyed by the element's DOM path inside its page and
//    re-applied after every render (clear-before-apply, so resets work);
//  - SCOPING (owner rule): while the form belongs to an account (loaded or
//    even just typed, saved or not), edits are stored PER ACCOUNT and the
//    base template stays untouched; only on a pristine form do edits update
//    the base template. The preview always shows template base + account
//    overrides (account wins per element).
// Storage: localStorage `dl:<docKey>` (template) / `dl:<docKey>::<account>`.

import React, { useEffect, useRef, useState } from 'react'

// dx/dy/rot = FREE move/rotate via CSS transform (Word "behind text" feel);
// wx = absolute width in px (edge-resize); txt = rewrite a leaf element's text.
export type DlBox = { fs?: number; bold?: boolean; align?: string; dir?: string; lh?: number; ls?: number; mt?: number; mis?: number; w?: number; dx?: number; dy?: number; rot?: number; wx?: number; txt?: string; hide?: boolean; font?: string; list?: string }

const DL_PROPS = ['fontSize', 'fontWeight', 'textAlign', 'direction', 'lineHeight', 'letterSpacing', 'marginTop', 'marginInlineStart', 'width', 'transform', 'transformOrigin', 'display', 'opacity', 'outline', 'outlineOffset', 'cursor', 'fontFamily'] as const
const PICK = 'span,td,th,li,p,div,h1,h2,h3,b'

export function useDocLayout(opts: {
  docKey: string                                   // unique per form/template, e.g. 'credit-file-retail'
  account?: string                                 // non-empty ⇒ account scope
  printRef: React.RefObject<HTMLDivElement | null> // the printable root
  pageSel: string                                  // page element selector inside the root, e.g. '.sn-page' | '#cf-sheet'
  onApplied?: () => void                           // e.g. re-fit pages after styles land
}) {
  const { docKey, printRef, pageSel } = opts
  const account = (opts.account || '').trim()
  const KEY = (scoped: boolean) => `dl:${docKey}${scoped && account ? `::${account}` : ''}`
  const [lay, setLay] = useState<Record<string, DlBox>>({})
  const [base, setBase] = useState<Record<string, DlBox>>({})
  const [sel, setSel] = useState<{ key: string; label: string; x: number; y: number } | null>(null)
  const [design, setDesign] = useState(false)
  const prev = useRef<string[]>([])
  const hover = useRef<HTMLElement | null>(null)

  // ---- DOM-path keys (pageIndex|childIndexChain), like the offer letter ----
  // single-sheet forms pass the root itself as the page (root matches pageSel)
  const pagesOf = (root: HTMLElement): Element[] =>
    root.matches(pageSel) ? [root] : Array.from(root.querySelectorAll(pageSel))
  const elPath = (el: HTMLElement): string | null => {
    const root = printRef.current
    if (!root) return null
    const page = el.closest(pageSel) as HTMLElement | null
    if (!page) return null
    const pages = pagesOf(root)
    const chain: number[] = []
    let cur: HTMLElement = el
    while (cur !== page) {
      const par = cur.parentElement
      if (!par) return null
      chain.unshift(Array.from(par.children).indexOf(cur))
      cur = par
    }
    return `${pages.indexOf(page)}|${chain.join('.')}`
  }
  const elFromPath = (key: string): HTMLElement | null => {
    const [pi, chain] = key.split('|')
    const root = printRef.current
    let cur: Element | null | undefined = root ? pagesOf(root)[Number(pi)] : null
    if (!cur) return null
    for (const i of chain ? chain.split('.') : []) {
      cur = cur.children[Number(i)]
      if (!cur) return null
    }
    return cur as HTMLElement
  }

  // effective = template base under the account's own overrides
  const eff: Record<string, DlBox> = account ? { ...base, ...lay } : lay

  // re-apply after EVERY render; clear previously-touched elements first
  useEffect(() => {
    for (const k of prev.current) {
      const el = elFromPath(k)
      if (el) DL_PROPS.forEach((p) => { (el.style as any)[p] = '' })
    }
    for (const [k, b] of Object.entries(eff)) {
      const el = elFromPath(k)
      if (!el) continue
      if (b.txt != null && el.children.length === 0) el.textContent = b.txt
      if (b.list && el.children.length === 0) {
        // Word-style list markers: prefix every non-empty LINE of this block
        let n = 0
        el.textContent = (el.textContent || '').split('\n').map((ln) => {
          if (!ln.trim()) return ln
          n++
          const pre = b.list === 'num' ? `${n}. ` : b.list === 'check' ? '\u2713 ' : b.list === 'dash' ? '\u2013 ' : '\u2022 '
          return ln.replace(/^\s*/, (m) => m + pre)
        }).join('\n')
      }
      if (b.font) el.style.fontFamily = b.font
      if (b.fs) el.style.fontSize = `${b.fs}pt`
      if (b.bold != null) el.style.fontWeight = b.bold ? '700' : '400'
      if (b.align) el.style.textAlign = b.align
      if (b.dir) el.style.direction = b.dir
      if (b.lh) el.style.lineHeight = String(b.lh)
      if (b.ls) el.style.letterSpacing = `${b.ls}px`
      if (b.mt) el.style.marginTop = `${b.mt}px`
      if (b.mis) el.style.marginInlineStart = `${b.mis}px`
      if (b.wx) el.style.width = `${b.wx}px`
      else if (b.w) el.style.width = `${b.w}%`
      if (b.dx || b.dy || b.rot) {
        // free float: siblings keep their place, the element glides/rotates
        el.style.transform = `translate(${b.dx || 0}px, ${b.dy || 0}px) rotate(${b.rot || 0}deg)`
        el.style.transformOrigin = 'center center'
        if (getComputedStyle(el).display === 'inline') el.style.display = 'inline-block'
      }
      if (b.hide) {
        // removed from the sheet; in layout mode it stays as a clickable ghost
        if (design) { el.style.opacity = '0.3'; el.style.outline = '1.5px dashed #dc2626'; el.style.outlineOffset = '1px' }
        else el.style.display = 'none'
      }
    }
    // the panel's target stays selected and draggable even outside layout mode
    if (sel) {
      const el = elFromPath(sel.key)
      if (el && !(eff[sel.key] || {}).hide) {
        el.style.outline = '2px solid #2563eb'
        el.style.outlineOffset = '1px'
        el.style.cursor = 'move'
      }
    }
    prev.current = [...Object.keys(eff), ...(sel ? [sel.key] : [])]
    opts.onApplied?.()
  })

  // load stores when the doc/scope changes
  useEffect(() => {
    try { setLay(JSON.parse(localStorage.getItem(KEY(true)) || '{}')) } catch { setLay({}) }
    if (account) {
      try { setBase(JSON.parse(localStorage.getItem(KEY(false)) || '{}')) } catch { setBase({}) }
    } else setBase({})
    setSel(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docKey, account])
  // write-back; an empty store removes its key (no junk keys while typing an account no)
  useEffect(() => {
    try {
      const s = JSON.stringify(lay)
      if (s === '{}') localStorage.removeItem(KEY(true))
      else localStorage.setItem(KEY(true), s)
    } catch { /* quota — stays in-memory */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lay])

  const skipClick = useRef(false)
  const panelPos = useRef<{ x: number; y: number } | null>(null)
  const clickOpen = (e: React.MouseEvent) => {
    if (skipClick.current) { skipClick.current = false; return }  // it was a drag
    openAt(e)
  }
  const openAt = (e: React.MouseEvent) => {
    const t = e.target as HTMLElement
    if (!t || t.closest('.dlp-panel')) return
    const el = (t.closest(PICK) as HTMLElement) || t
    const key = elPath(el)
    if (!key) return
    e.preventDefault()
    // open OUT OF THE WAY (screen edge, or wherever the user last dragged it)
    const pos = panelPos.current || {
      x: Math.max(8, (typeof window !== 'undefined' ? window.innerWidth : 1200) - 300),
      y: 90,
    }
    setSel({
      key,
      label: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 44) || 'عنصر',
      ...pos,
    })
  }
  // design-mode DRAG: press a block and pull — moves via the same mt/mis
  // offsets the panel edits; a real drag suppresses the click-opens-panel.
  const onDragStart = (e: React.PointerEvent) => {
    skipClick.current = false   // new gesture — a stale flag must not eat it
    if ((!design && !sel) || e.button !== 0) return
    const t = e.target as HTMLElement
    if (!t || t.closest('.dlp-panel')) return
    const el = (t.closest(PICK) as HTMLElement) || null
    if (!el || !printRef.current?.contains(el)) return
    const key = elPath(el)
    if (!key) return
    // outside layout mode only the dblclicked (selected) element is draggable
    if (!design && key !== sel?.key) return
    const b = eff[key] || {}
    const r = el.getBoundingClientRect()
    // press near a side edge => resize that side; anywhere else => FREE move
    const EDGE = 8
    const mode: 'move' | 'r' | 'l' = e.clientX > r.right - EDGE ? 'r' : e.clientX < r.left + EDGE ? 'l' : 'move'
    const drag = {
      key, sx: e.clientX, sy: e.clientY, mode,
      dx0: b.dx || 0, dy0: b.dy || 0, w0: b.wx || r.width,
      moved: false,
    }
    const mv = (ev: PointerEvent) => {
      const dx = ev.clientX - drag.sx, dy = ev.clientY - drag.sy
      if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 3) return
      drag.moved = true
      setLay((s) => {
        const cur: DlBox = { ...(s[drag.key] || {}) }
        if (drag.mode === 'move') { cur.dx = Math.round(drag.dx0 + dx); cur.dy = Math.round(drag.dy0 + dy) }
        else if (drag.mode === 'r') cur.wx = Math.max(24, Math.round(drag.w0 + dx))
        else { cur.wx = Math.max(24, Math.round(drag.w0 - dx)); cur.dx = Math.round(drag.dx0 + dx) }
        return { ...s, [drag.key]: cur }
      })
    }
    const up = () => {
      document.removeEventListener('pointermove', mv)
      document.removeEventListener('pointerup', up)
      if (drag.moved) skipClick.current = true
    }
    document.addEventListener('pointermove', mv)
    document.addEventListener('pointerup', up)
    e.preventDefault()
  }
  const startPanelDrag = (e: React.PointerEvent) => {
    const s0 = sel
    if (!s0) return
    const ox = e.clientX - s0.x, oy = e.clientY - s0.y
    const mv = (ev: PointerEvent) => {
      const x = Math.max(0, ev.clientX - ox), y = Math.max(0, ev.clientY - oy)
      panelPos.current = { x, y }
      setSel((s) => (s ? { ...s, x, y } : s))
    }
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv)
    document.addEventListener('pointerup', up)
    e.preventDefault()
  }
  const clearHover = () => {
    const el = hover.current
    if (el) { el.style.outline = ''; el.style.outlineOffset = ''; hover.current = null }
  }
  const onHover = (e: React.MouseEvent) => {
    const t = e.target as HTMLElement
    const el = (t?.closest(PICK) as HTMLElement) || null
    if (!el || !printRef.current?.contains(el) || el.closest('.dlp-panel')) { clearHover(); return }
    if (hover.current !== el) {
      clearHover()
      hover.current = el
      el.style.outline = '2px dashed #f59e0b'
      el.style.outlineOffset = '1px'
    }
  }
  useEffect(() => { if (!design) clearHover() }, [design])

  // spread onto the printable root
  const containerProps = {
    onDoubleClick: openAt,
    onClick: design ? clickOpen : undefined,
    onPointerDown: design || sel ? onDragStart : undefined,
    onMouseOver: design ? onHover : undefined,
    onMouseLeave: design ? clearHover : undefined,
    style: design ? ({ cursor: 'move' } as React.CSSProperties) : undefined,
  }

  const update = (patch: DlBox) => {
    if (!sel) return
    setLay((s) => ({ ...s, [sel.key]: { ...(s[sel.key] || {}), ...patch } }))
  }

  const designButton = (
    <button type="button" onClick={() => { setDesign((d) => !d); setSel(null); clearHover() }}
      className={`flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium text-white ${design ? 'bg-green-600 hover:bg-green-700' : 'bg-amber-500 hover:bg-amber-600'}`}>
      {design ? '✓ پایانِ چیدمان' : 'چیدمان'}
    </button>
  )

  const scopeHint = (
    <span className="text-[11px] text-gray-500 self-center" dir="rtl">
      {account
        ? <>چینش فقط برای حسابِ <b dir="ltr">{account}</b> ذخیره می‌شود — قالبِ اصلی دست‌نخورده می‌ماند</>
        : 'فرم خالی است — تغییرِ چینش، قالبِ اصلی (پیش‌فرضِ همۀ حساب‌ها) را به‌روز می‌کند'}
    </span>
  )

  const panel = sel ? (() => {
    const b = eff[sel.key] || {}
    return (
      <div className="dlp-panel" style={{ left: sel.x, top: sel.y }} dir="rtl">
        <div className="dlp-h" onPointerDown={startPanelDrag} title="برای جابه‌جاییِ پنل بکشید" style={{ cursor: 'move', touchAction: 'none' }}>
          <span title={sel.label}>چینش — {sel.label}</span>
          <button className="dlp-x" onPointerDown={(e) => e.stopPropagation()} onClick={() => setSel(null)}>×</button>
        </div>
        <div className="dlp-row">
          <label>اندازۀ فونت (pt)</label>
          <input type="number" step="0.5" value={b.fs ?? ''} placeholder="—"
            onChange={(e) => update({ fs: +e.target.value || undefined })} />
          <button className={b.bold ? 'on' : ''} onClick={() => update({ bold: !b.bold })}>بولد</button>
        </div>
        <div className="dlp-seg" title="چینش">
          {([['right', '≡راست'], ['center', 'وسط'], ['left', 'چپ≡'], ['justify', 'تراز']] as const).map(([a, t]) => (
            <button key={a} className={b.align === a ? 'on' : ''} onClick={() => update({ align: a })}>{t}</button>
          ))}
        </div>
        <div className="dlp-seg" title="جهتِ نوشتار">
          <button className={b.dir === 'rtl' ? 'on' : ''} onClick={() => update({ dir: 'rtl' })}>راست‑چپ</button>
          <button className={b.dir === 'ltr' ? 'on' : ''} onClick={() => update({ dir: 'ltr' })}>چپ‑راست</button>
        </div>
        <div className="dlp-row">
          <label>فونت</label>
          <select className="dlp-font" value={b.font ?? ''} onChange={(e) => update({ font: e.target.value || undefined })}>
            <option value="">پیش‌فرض</option>
            <option value='"B Nazanin", "Times New Roman", serif'>B Nazanin</option>
            <option value='"Times New Roman", "B Nazanin", serif'>Times New Roman</option>
            <option value='Arial, "B Nazanin", sans-serif'>Arial</option>
            <option value='"Traditional Arabic", "Times New Roman", serif'>Traditional Arabic</option>
            <option value='Georgia, "B Nazanin", serif'>Georgia</option>
            <option value='Tahoma, "B Nazanin", sans-serif'>Tahoma</option>
          </select>
        </div>
        <div className="dlp-seg" title="نشانۀ ابتدای هر خطِ این بلوک (مثل Word)">
          <button className={!b.list ? 'on' : ''} onClick={() => update({ list: undefined })}>بدون</button>
          <button className={b.list === 'num' ? 'on' : ''} onClick={() => update({ list: 'num' })}>1.2.3</button>
          <button className={b.list === 'bullet' ? 'on' : ''} onClick={() => update({ list: 'bullet' })}>•</button>
          <button className={b.list === 'check' ? 'on' : ''} onClick={() => update({ list: 'check' })}>✓</button>
          <button className={b.list === 'dash' ? 'on' : ''} onClick={() => update({ list: 'dash' })}>–</button>
        </div>
        <div className="dlp-grid">
          <label>فاصلۀ خط<input type="number" step="0.1" value={b.lh ?? ''} placeholder="—" onChange={(e) => update({ lh: +e.target.value || undefined })} /></label>
          <label>فاصلۀ حروف<input type="number" step="0.5" value={b.ls ?? ''} placeholder="—" onChange={(e) => update({ ls: +e.target.value || undefined })} /></label>
          <label>جابه‌جایی عمودی<input type="number" value={b.mt ?? ''} placeholder="px" onChange={(e) => update({ mt: +e.target.value || undefined })} /></label>
          <label>جابه‌جایی افقی<input type="number" value={b.mis ?? ''} placeholder="px" onChange={(e) => update({ mis: +e.target.value || undefined })} /></label>
          <label>عرض ٪<input type="number" value={b.w ?? ''} placeholder="—" onChange={(e) => update({ w: +e.target.value || undefined })} /></label>
          <label>X آزاد (px)<input type="number" value={b.dx ?? ''} placeholder="—" onChange={(e) => update({ dx: e.target.value === '' ? undefined : +e.target.value })} /></label>
          <label>Y آزاد (px)<input type="number" value={b.dy ?? ''} placeholder="—" onChange={(e) => update({ dy: e.target.value === '' ? undefined : +e.target.value })} /></label>
          <label>چرخش (درجه)<input type="number" step="1" value={b.rot ?? ''} placeholder="0" onChange={(e) => update({ rot: e.target.value === '' ? undefined : +e.target.value })} /></label>
          <label>عرض (px)<input type="number" value={b.wx ?? ''} placeholder="—" onChange={(e) => update({ wx: +e.target.value || undefined })} /></label>
        </div>
        <label className="dlp-txt">متنِ این عنصر (بازنویسی — فقط بلوکِ متنِ ساده)
          <textarea value={b.txt ?? ''} placeholder="— متنِ اصلی —" dir="auto"
            onChange={(e) => update({ txt: e.target.value === '' ? undefined : e.target.value })} />
        </label>
        <div className="dlp-actions">
          <button style={b.hide ? undefined : { color: '#dc2626' }}
            onClick={() => update({ hide: !b.hide || undefined })}>
            {b.hide ? 'نمایشِ دوباره' : 'حذف از برگه'}
          </button>
          <button onClick={() => setLay((s) => { const n = { ...s }; delete n[sel.key]; return n })}>بازنشانیِ این عنصر</button>
          <button onClick={() => { if (confirm(account ? `همۀ چینشِ سفارشیِ حسابِ ${account} پاک شود؟ (قالبِ اصلی دست نمی‌خورد)` : 'همۀ چینشِ سفارشیِ قالبِ اصلی پاک شود؟')) { setLay({}); setSel(null) } }}>بازنشانیِ همه</button>
        </div>
        <div className="dlp-hint">
          {account
            ? <>تغییرها فقط برای حسابِ <b dir="ltr">{account}</b> اعمال و ذخیره می‌شوند؛ قالبِ اصلی تغییری نمی‌کند.</>
            : 'فرم به حسابی تعلق ندارد — این تغییرها قالبِ اصلی (پیش‌فرضِ همۀ حساب‌ها) را به‌روز می‌کنند.'}
        </div>
      </div>
    )
  })() : null

  return { design, designButton, scopeHint, containerProps, panel }
}

// page-agnostic styles for the floating panel (+ print safety)
export const DocLayoutStyles = () => (
  <style>{`
    .dlp-panel { position:fixed; z-index:60; width:270px; background:#fff; border:1px solid #cbd5e1; border-radius:12px;
                 box-shadow:0 10px 30px rgba(0,0,0,.18); padding:10px; font-size:12px; font-family:inherit; }
    .dlp-h { display:flex; justify-content:space-between; align-items:center; font-weight:700; margin-bottom:8px; gap:6px; }
    .dlp-h span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .dlp-x { border:0; background:transparent; font-size:16px; cursor:pointer; color:#64748b; }
    .dlp-row { display:flex; align-items:center; gap:6px; margin-bottom:6px; }
    .dlp-row label { flex:1; color:#475569; }
    .dlp-row input { width:64px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 6px; }
    .dlp-row button, .dlp-seg button, .dlp-actions button { border:1px solid #cbd5e1; background:#f8fafc; border-radius:6px; padding:2px 8px; cursor:pointer; }
    .dlp-row button.on, .dlp-seg button.on { background:#2563eb; color:#fff; border-color:#2563eb; }
    .dlp-seg { display:flex; gap:4px; margin-bottom:6px; }
    .dlp-seg button { flex:1; }
    .dlp-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:6px; }
    .dlp-grid label { display:flex; flex-direction:column; gap:2px; color:#475569; }
    .dlp-grid input { border:1px solid #cbd5e1; border-radius:6px; padding:2px 6px; width:100%; }
    .dlp-font { flex:1; border:1px solid #cbd5e1; border-radius:6px; padding:2px 6px; max-width:170px; }
    .dlp-txt { display:block; color:#475569; margin-bottom:6px; }
    .dlp-txt textarea { display:block; width:100%; height:56px; margin-top:2px; border:1px solid #cbd5e1; border-radius:6px; padding:4px 6px; font-size:11px; resize:vertical; }
    .dlp-actions { display:flex; gap:6px; margin-bottom:6px; }
    .dlp-actions button { flex:1; }
    .dlp-hint { color:#64748b; font-size:11px; line-height:1.6; }
    @media print {
      .dlp-panel { display:none !important; }
      /* design-mode hover outline must never reach paper */
      * { outline:none !important; }
    }
  `}</style>
)
