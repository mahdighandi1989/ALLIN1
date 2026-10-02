'use client'
// v171 — «نوار دستورِ سریع» on the letter form (نامهٔ مشتری، نامهٔ عمومی، خلاصهٔ پرونده —
// all three are this one page).
//
// The owner types a short request, optionally draws ONE OR MORE boxes over the part
// of the form it is about, and presses «اجرا». Each box is recorded exactly (sheet,
// position ON the sheet, the layout boxes under it, the text under it) and travels
// with the request to the same AI the assistant uses — so the two share one set of
// operations and cannot contradict each other. With no box drawn the server-side
// model works out where the request points from the words and the form itself.
//
// This component only COLLECTS and SHOWS. Running and applying live in the page
// (it owns the letter state); this keeps a bar bug from ever touching the letter.
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Zap, Crosshair, X, Undo2 } from 'lucide-react'
import type { QuickSpot } from '../../lib/api'
import {
  headingAbove, layoutKeysUnder, rectOnSheet, rowsInRect, sheetIndexFor, textInRect, type BarSpot, type Item, type R,
} from '../../lib/quickSpot'

export type QuickResult = { applied: string[]; notes: string[]; skipped: number; error?: string }

// the API spot + what the page needs to keep drawing the box where the owner drew it
type Anchored = BarSpot & { k: number; vp: R; sx: number; sy: number }

const MAX_BOXES = 5
const MIN_PX = 12

export default function QuickCommandBar({ keyFa, busy, canUndo, onRun, onUndo }: {
  keyFa: Record<string, string>
  busy: boolean
  canUndo: boolean
  onRun: (instruction: string, spots: BarSpot[]) => Promise<QuickResult | void>
  onUndo: () => void
}) {
  const [text, setText] = useState('')
  const [spots, setSpots] = useState<Anchored[]>([])
  const [, setTick] = useState(0)
  const [armed, setArmed] = useState(false)
  const [rect, setRect] = useState<R | null>(null)
  const [result, setResult] = useState<QuickResult | null>(null)
  const start = useRef<{ x: number; y: number } | null>(null)

  const measure = useCallback((box: R): Anchored => {
    const sheets = Array.from(document.querySelectorAll<HTMLElement>('#ltr-edit .lsheet, #ltr-edit .psheet')).filter((s) => s.offsetWidth > 0)
    const sheetRects: R[] = sheets.map((s) => { const b = s.getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height } })
    const idx = sheetIndexFor(box, sheetRects)          // 1-based, 0 = off the sheets
    const items: Item[] = Array.from(document.querySelectorAll<HTMLElement>('#ltr-edit [data-lbox]')).map((el) => {
      const b = el.getBoundingClientRect()
      return { key: el.getAttribute('data-lbox') || '', rect: { x: b.left, y: b.top, w: b.width, h: b.height } }
    }).filter((i) => i.key)
    // only the sheet the box is on: the same box keys repeat on every page
    const onPage = idx ? items.filter((i) => sheetRects[idx - 1] && i.rect.y >= sheetRects[idx - 1].y - 1
      && i.rect.y <= sheetRects[idx - 1].y + sheetRects[idx - 1].h) : items
    const keys = layoutKeysUnder(box, onPage)
    // the sheet may be CSS-scaled to fit the screen: report sheet-layout pixels,
    // which are the units the layout itself is stored in
    let k = 1
    let rel: R = { x: Math.round(box.x), y: Math.round(box.y), w: Math.round(box.w), h: Math.round(box.h) }
    if (idx) {
      const sr = sheetRects[idx - 1]
      k = sheets[idx - 1].offsetWidth > 0 && sr.w > 0 ? sheets[idx - 1].offsetWidth / sr.w : 1
      const on = rectOnSheet(box, sr)
      rel = { x: Math.round(on.x * k), y: Math.round(on.y * k), w: Math.round(on.w * k), h: Math.round(on.h * k) }
    }
    const stack = document.elementsFromPoint(box.x + box.w / 2, box.y + box.h / 2)
      .filter((el) => !el.closest('[data-qc-layer]'))
    // v173 — WHAT IS UNDER THE BOX, BY GEOMETRY, NOT BY ANCESTRY.
    //
    // This used to climb from the centre up to the enclosing `[data-lbox]` and
    // take that element's text. The whole letter body is ONE layout box, so a
    // box drawn around the table in §3 reported the body's text — which begins
    // at §1. Every box on the body described the same paragraph, confidently and
    // wrongly: «پیش‌نمایشش جایی دیگه رو شناسایی کرده».
    //
    // The lines whose own rectangles fall inside the box are the answer, and a
    // box over empty table cells has no text of its own — so the nearest heading
    // above it is carried too, which is what names «۳- مشخصات تسهیلات…».
    const scope = (idx ? sheets[idx - 1] : null)
      || (stack.find((el) => el.closest('#ltr-edit')) as HTMLElement | undefined)
      || null
    const inside = textInRect(scope, box)
    const heading = headingAbove(scope, box)
    const covered = inside
      ? (heading && !inside.startsWith(heading) ? `${heading} ← ${inside}` : inside)
      : (heading ? `${heading} (کادر روی ناحیهٔ خالیِ زیرِ همین عنوان)` : '')
    const inBar = stack.some((el) => el.closest('.ltr-controls'))
    // v178 — the table(s) under the box, by their rows' stable ids (+ the attachment page)
    const rows = rowsInRect(scope, box)
    const attId = (idx ? sheets[idx - 1].getAttribute('data-att-id') : null) || undefined
    return {
      rows, att_id: attId,
      page: idx, rect: rel, layout_keys: keys, covered_text: covered.slice(0, 400),
      section: inBar ? 'نوار دکمه‌های بالای فرم' : (idx ? `برگهٔ ${idx} فرم` : 'بیرون از برگه'),
      k, vp: box, sx: window.scrollX, sy: window.scrollY,
    }
  }, [])

  useEffect(() => {
    if (!spots.length) return
    const bump = () => setTick((n) => n + 1)
    window.addEventListener('scroll', bump, true)
    window.addEventListener('resize', bump)
    return () => { window.removeEventListener('scroll', bump, true); window.removeEventListener('resize', bump) }
  }, [spots.length])

  // where a recorded box is on screen NOW: glued to its sheet when it was drawn on one
  const markerRect = (sp: Anchored): R => {
    if (sp.page) {
      const sheets = Array.from(document.querySelectorAll<HTMLElement>('#ltr-edit .lsheet, #ltr-edit .psheet')).filter((x) => x.offsetWidth > 0)
      const el = sheets[sp.page - 1]
      if (el) {
        const b = el.getBoundingClientRect()
        return { x: b.left + sp.rect.x / sp.k, y: b.top + sp.rect.y / sp.k, w: sp.rect.w / sp.k, h: sp.rect.h / sp.k }
      }
    }
    return { x: sp.vp.x - (window.scrollX - sp.sx), y: sp.vp.y - (window.scrollY - sp.sy), w: sp.vp.w, h: sp.vp.h }
  }

  const onDown = (e: React.PointerEvent) => {
    start.current = { x: e.clientX, y: e.clientY }
    setRect({ x: e.clientX, y: e.clientY, w: 0, h: 0 })
  }
  const onMove = (e: React.PointerEvent) => {
    const s = start.current
    if (!s) return
    setRect({ x: Math.min(s.x, e.clientX), y: Math.min(s.y, e.clientY), w: Math.abs(e.clientX - s.x), h: Math.abs(e.clientY - s.y) })
  }
  const onUp = () => {
    const r = rect
    start.current = null
    setRect(null)
    setArmed(false)
    if (!r || r.w < MIN_PX || r.h < MIN_PX) return
    setSpots((p) => (p.length >= MAX_BOXES ? p : [...p, measure(r)]))
  }

  const run = async () => {
    const t = text.trim()
    if (!t || busy) return
    setResult(null)
    const out = await onRun(t, spots.map(({ k: _k, vp: _vp, sx: _sx, sy: _sy, ...api }) => api))
    if (out) {
      setResult(out)
      // a request that went through is finished business; a failed one keeps its text
      if (!out.error) { setText(''); setSpots([]) }
    }
  }

  const label = (sp: QuickSpot, i: number) => {
    const k = sp.layout_keys.map((x) => keyFa[x] || x).join('، ')
    const r = sp.rect
    return `کادر ${i + 1} — ${sp.page ? `برگهٔ ${sp.page}` : 'بیرون از برگه'}${k ? ` · ${k}` : ''} · x=${r.x} y=${r.y} ${r.w}×${r.h}`
  }

  return (
    <>
    <div dir="rtl" data-qc-layer="1" className="no-print"
      style={{ flex: '1 1 420px', minWidth: 260, padding: '3px 8px', border: '1px solid #c7d2fe', borderRadius: 8, background: '#eef2ff' }}>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
        <Zap size={16} color="#4f46e5" />
        <b style={{ fontSize: 12, color: '#3730a3' }}>دستورِ سریع</b>
        <input
          value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void run() } }}
          disabled={busy}
          placeholder="مثلاً: لوگو را ۲۰٪ بزرگ‌تر کن · اندازهٔ فونتِ موضوع ۱۴ شود · این قسمت را رسمی‌تر بنویس"
          style={{ flex: '1 1 320px', minWidth: 220, padding: '6px 10px', border: '1px solid #a5b4fc', borderRadius: 8, fontSize: 13, background: '#fff' }}
        />
        <button type="button" onClick={() => setArmed(true)} disabled={busy || spots.length >= MAX_BOXES}
          title="یک یا چند کادر دورِ قسمتی از فرم بکش تا دستور روی همان قسمت اجرا شود (اختیاری — نکشی، خودش حدس می‌زند)"
          className="ltr-btn gray"><Crosshair size={14} /> کادر</button>
        <button type="button" onClick={() => void run()} disabled={busy || !text.trim()}
          className="ltr-btn" style={{ background: '#4f46e5', opacity: busy || !text.trim() ? 0.6 : 1 }}>
          <Zap size={14} /> {busy ? 'در حالِ اجرا…' : 'اجرا'}
        </button>
        {canUndo && (
          <button type="button" onClick={onUndo} disabled={busy} className="ltr-btn gray"
            title="برگرداندنِ آخرین دستورِ سریع (متن، اندازه‌ها، سربرگ، عنوان‌ها)">
            <Undo2 size={14} /> برگشتِ دستور
          </button>
        )}
      </div>
    </div>

    <div dir="rtl" data-qc-layer="1" className="no-print" style={{ flexBasis: '100%' }}>
      {spots.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 2 }}>
          {spots.map((sp, i) => (
            <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '2px 8px', borderRadius: 999, background: '#fff', border: '1px solid #a5b4fc', color: '#3730a3' }}
              title={sp.covered_text ? `زیرِ کادر: ${sp.covered_text}` : ''}>
              {label(sp, i)}
              <button type="button" onClick={() => setSpots((p) => p.filter((_, j) => j !== i))} title="برداشتنِ کادر"
                style={{ border: 0, background: 'transparent', cursor: 'pointer', padding: 0, lineHeight: 1 }}><X size={12} /></button>
            </span>
          ))}
        </div>
      )}
      {!spots.length && !result && (
        <div style={{ fontSize: 11, color: '#6366f1' }}>
          کادر اختیاری است؛ بدونِ کادر، هوش مصنوعی از روی دستور و ساختارِ فرم تشخیص می‌دهد کجا مقصود است. نتیجه بلافاصله روی فرم می‌نشیند و با «برگشتِ دستور» برمی‌گردد.
        </div>
      )}

      {result && (
        <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.8 }}>
          {result.error ? (
            <div style={{ color: '#b91c1c' }}>⚠ {result.error}</div>
          ) : (
            <>
              {result.applied.length > 0 && (
                <div style={{ color: '#166534' }}>
                  ✓ {result.applied.length.toLocaleString('fa-IR')} تغییر اعمال شد:
                  {result.applied.map((a, i) => <div key={i} style={{ paddingRight: 12 }}>• {a}</div>)}
                </div>
              )}
              {result.applied.length === 0 && <div style={{ color: '#92400e' }}>تغییری اعمال نشد.</div>}
              {result.skipped > 0 && (
                <div style={{ color: '#92400e' }}>{result.skipped.toLocaleString('fa-IR')} مورد در فرمِ فعلی پیدا/اجرا نشد و رد شد.</div>
              )}
            </>
          )}
          {result.notes.map((n, i) => <div key={i} style={{ color: '#475569' }}>ℹ {n}</div>)}
        </div>
      )}

    </div>

      {spots.map((sp, i) => {
        const r = markerRect(sp)
        return (
          <div key={`m${i}`} data-qc-layer="1" className="no-print pointer-events-none fixed z-[80]"
            style={{ left: r.x, top: r.y, width: r.w, height: r.h, border: '2px solid #4f46e5', background: 'rgba(99,102,241,0.12)', borderRadius: 3 }}>
            <span style={{ position: 'absolute', top: -18, right: 0, background: '#4f46e5', color: '#fff', fontSize: 10, padding: '0 6px', borderRadius: 4, whiteSpace: 'nowrap' }}>
              ✓ ثبت شد · کادر {(i + 1).toLocaleString('fa-IR')}{sp.layout_keys.length ? ` · ${sp.layout_keys.map((x) => keyFa[x] || x).join('، ')}` : ''}
            </span>
          </div>
        )
      })}

      {armed && (
        <div data-qc-layer="1" dir="rtl"
          className="fixed inset-0 z-[90]"
          style={{ cursor: 'crosshair', background: 'rgba(30,27,75,0.16)' }}
          onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}
          onKeyDown={(e) => { if (e.key === 'Escape') setArmed(false) }} tabIndex={-1}
          ref={(el) => el?.focus()}>
          {rect && rect.w > 2 && (
            <div className="pointer-events-none absolute border-2 border-indigo-500 bg-indigo-300/10"
              style={{ left: rect.x, top: rect.y, width: rect.w, height: rect.h }} />
          )}
          <div className="pointer-events-none absolute left-1/2 top-6 -translate-x-1/2 rounded-lg bg-black/85 px-4 py-2 text-sm text-indigo-100">
            دورِ قسمتِ مورد نظر کادر بکش · Esc انصراف
          </div>
        </div>
      )}
    </>
  )
}
