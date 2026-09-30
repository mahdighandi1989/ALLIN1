'use client'
// v150 — «همون‌جایی که کادر کشیدم … یه هایلایت مانند همون ابعاد در همون مختصات
// باشه که بتونم ببینم کجاها گزارش ثبت شده و چی نوشته شده».
//
// THE CONSTRAINT THAT SHAPES EVERYTHING HERE
// ------------------------------------------
// The owner asked for two things that normally exclude each other:
//
//   «وقتی روشون میایم باید متنِ گزارش ظاهر بشه با موس»         → needs hover
//   «نباید مانع بشه که کلیک‌های زیر … قابلِ کلیک کردن نباشن»    → needs no hover
//
// An element that receives `mouseenter` also receives `click`. So the overlay is
// `pointer-events: none` throughout — the browser never gives it a single event,
// and everything underneath behaves exactly as if it were not there — and the
// hover is done by hit-testing a document-level `mousemove` against the stored
// rectangles ourselves. Nothing is intercepted, and the tooltip still appears.
//
// WHERE THE RECTANGLES COME FROM
// ------------------------------
// `placeSpot` re-measures the anchor element and applies the stored fractions, so
// a highlight follows its content when the layout moves. When the anchor is gone
// it falls back to the stored document pixels AND SAYS SO — the tooltip shows
// «تقریبی»,  because a highlight that has silently drifted points the owner at
// the wrong control with full confidence.
//
// WHEN THEY DISAPPEAR
// -------------------
// A sheet is drawn while it is open / answered / approved, and stops being drawn
// once it is `filed`. Filing happens when the supervisor runs its round — EVERY
// round, the periodic one and the urgent one — and moves every sheet the OWNER
// has ticked (the blue ones) into a binder. So: tick it, and it is gone from the
// page at the next round, still readable in the archive.
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { inspectionApi, type InspectionReport } from './api'
import { placeSpot, samePage, type Placement } from './inspectionSpot'

/** Per-viewer display preferences. A preference, not a permission — so it lives
 *  in the browser and never needs the server's opinion. */
export const HL_ENABLED_KEY = 'allin1.inspection.highlights'
export const HL_OPACITY_KEY = 'allin1.inspection.highlightOpacity'
export const HL_DEFAULT_OPACITY = 0.22

export function readHighlightsEnabled(): boolean {
  try {
    // DEFAULT ON, as asked — an absent key means «not set», not «off».
    return localStorage.getItem(HL_ENABLED_KEY) !== '0'
  } catch {
    return true            // private mode / blocked storage: still on
  }
}

export function readHighlightOpacity(): number {
  try {
    const raw = localStorage.getItem(HL_OPACITY_KEY)
    const n = raw === null ? NaN : Number(raw)
    return Number.isFinite(n) ? clampOpacity(n) : HL_DEFAULT_OPACITY
  } catch {
    return HL_DEFAULT_OPACITY
  }
}

export const clampOpacity = (n: number) => Math.min(0.9, Math.max(0.04, n))

export function writeHighlightsEnabled(on: boolean): void {
  try { localStorage.setItem(HL_ENABLED_KEY, on ? '1' : '0') } catch { /* blocked */ }
  notify()
}

export function writeHighlightOpacity(v: number): void {
  try { localStorage.setItem(HL_OPACITY_KEY, String(clampOpacity(v))) } catch { /* blocked */ }
  notify()
}

// Settings live on another page, so the overlay is told rather than polling.
const EVT = 'allin1:inspection-highlights'
const notify = () => {
  try { window.dispatchEvent(new CustomEvent(EVT)) } catch { /* SSR */ }
}

/** The sheets changed — a new one was filed, or one was answered or ticked. */
export const SHEETS_EVT = 'allin1:inspection-sheets'
export const notifySheetsChanged = () => {
  try { window.dispatchEvent(new CustomEvent(SHEETS_EVT)) } catch { /* SSR */ }
}

// v166 — THE HIGHLIGHT IS THE CONVERSATION, NOT THE VERDICT.
//
// «وقتی مثلا جواب میده باید هایلایت تبدیل به رنگ سبز بشه و اگر دوباره اون گزارش
// موجود گزارش و پیامی ثبت کردم دوباره نارنجی بشه و اگر تایید زدم کلا باید ابی
// بشه و ناظر گزارش هایی که رنگ ابی دارن در هر دور بررسی میره بایگانی میکنه».
//
// Four states, one meaning each — whose TURN is it:
//
//   نارنجی  open      من منتظرم            ← also where a follow-up note sends it back
//   سبز     answered  ناظر جواب داده
//   آبی     approved  من تیک زدم           ← ناظر دورِ بعد بایگانی‌اش می‌کند
//   —       filed     تمام                 ← هایلایت برداشته می‌شود
//
// Until v166 this drew the OUTCOME instead (fixed / partial / not-done /
// needs-owner), so an answered sheet came back amber or grey depending on what
// the supervisor claimed, and an approved sheet came out GREEN while its own
// badge on the board said blue — the two palettes disagreed with each other.
// The outcome is not lost: it is what the badge and the tooltip say, which is
// where a word belongs. The colour on the page answers one question only.
export const TONE_COLOR: Record<string, string> = {
  // the lifecycle — this is what a highlight is painted with
  open: '245, 158, 11',          // amber — waiting for the supervisor (or asked again)
  answered: '16, 185, 129',      // emerald — the supervisor has replied
  approved: '59, 130, 246',      // blue — the owner ticked it; filed next round
  filed: '107, 114, 128',        // grey — never drawn, kept so nothing resolves to undefined
  // the outcome — no longer painted, kept because other surfaces read this map
  // and because losing a colour is losing a capability
  fixed: '16, 185, 129',
  partial: '245, 158, 11',
  'needs-owner': '139, 92, 246', // violet
  'not-done': '239, 68, 68',     // red
  stale: '107, 114, 128',        // grey
}

/**
 * The colour of a sheet is the colour of its STATE — whose turn it is.
 *
 * The outcome tone is still honoured for a status this does not know about, so
 * a future state cannot silently fall through to «amber, waiting».
 */
export const toneOf = (r: InspectionReport): string =>
  LIFECYCLE[r.status] || TONE_COLOR[r.glow?.tone || ''] || TONE_COLOR.open

const LIFECYCLE: Record<string, string> = {
  open: TONE_COLOR.open,
  answered: TONE_COLOR.answered,
  approved: TONE_COLOR.approved,
  filed: TONE_COLOR.filed,
}

type Placed = {
  report: InspectionReport
  place: Placement
}

export function InspectionHighlights({ pathname }: { pathname: string }) {
  const [reports, setReports] = useState<InspectionReport[]>([])
  const [enabled, setEnabled] = useState(true)
  const [opacity, setOpacity] = useState(HL_DEFAULT_OPACITY)
  const [placed, setPlaced] = useState<Placed[]>([])
  const [hover, setHover] = useState<{ p: Placed; x: number; y: number } | null>(null)
  const raf = useRef<number | null>(null)

  useEffect(() => {
    setEnabled(readHighlightsEnabled())
    setOpacity(readHighlightOpacity())
    const onPref = () => { setEnabled(readHighlightsEnabled()); setOpacity(readHighlightOpacity()) }
    window.addEventListener(EVT, onPref)
    window.addEventListener('storage', onPref)   // another tab changed it
    return () => { window.removeEventListener(EVT, onPref); window.removeEventListener('storage', onPref) }
  }, [])

  // Only the sheets for THIS page, and only while they are still live. A filed
  // sheet is history: it belongs in the binder, not on the screen.
  //
  // FETCHED MORE THAN ONCE, ON PURPOSE. A single fetch on mount fails silently
  // and permanently in the two cases that matter: the page painted before the
  // token was in place (a 401, caught, and never retried — highlights simply
  // never appear until a full reload), and a sheet filed a moment ago, which
  // would not show until the next navigation. So it retries a bounded number of
  // times, refetches when the tab regains focus, and listens for its own app
  // telling it a sheet changed.
  useEffect(() => {
    if (!enabled) { setReports([]); return }
    let alive = true
    let attempt = 0
    let timer: number | undefined

    const load = async () => {
      try {
        const d = await inspectionApi.list({ reopen: undefined })
        if (!alive) return
        setReports((d.reports || []).filter(
          (r) => r.status !== 'filed' && samePage(r.page, pathname) && !!r.geometry))
      } catch {
        // not signed in yet, or the endpoint is briefly unavailable. Back off and
        // try again a few times rather than giving up for the life of the page.
        if (!alive || attempt >= 4) return
        attempt += 1
        timer = window.setTimeout(load, 700 * attempt)
      }
    }
    void load()

    const again = () => { attempt = 0; void load() }
    window.addEventListener('focus', again)
    window.addEventListener(SHEETS_EVT, again)
    return () => {
      alive = false
      if (timer) window.clearTimeout(timer)
      window.removeEventListener('focus', again)
      window.removeEventListener(SHEETS_EVT, again)
    }
  }, [pathname, enabled])

  // Re-measure on anything that can move the content. Cheap: it is arithmetic
  // over a handful of rects, and it is coalesced into an animation frame.
  const remeasure = useCallback(() => {
    if (raf.current !== null) return
    raf.current = requestAnimationFrame(() => {
      raf.current = null
      const lookup = (sel: string) => {
        try {
          const el = document.querySelector(sel)
          if (!el) return null
          const b = el.getBoundingClientRect()
          const sx = window.scrollX || 0
          const sy = window.scrollY || 0
          return { x: b.left + sx, y: b.top + sy, w: b.width, h: b.height }
        } catch { return null }
      }
      const out: Placed[] = []
      for (const r of reports) {
        const place = placeSpot(r.geometry, lookup)
        if (place) out.push({ report: r, place })
      }
      setPlaced(out)
    })
  }, [reports])

  useEffect(() => {
    remeasure()
    window.addEventListener('resize', remeasure)
    window.addEventListener('scroll', remeasure, true)
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(remeasure) : null
    try { ro?.observe(document.body) } catch { /* older browser */ }
    const t = window.setInterval(remeasure, 2000)   // late-loading content
    return () => {
      window.removeEventListener('resize', remeasure)
      window.removeEventListener('scroll', remeasure, true)
      ro?.disconnect()
      window.clearInterval(t)
      if (raf.current !== null) cancelAnimationFrame(raf.current)
    }
  }, [remeasure])

  // THE HOVER, without ever taking an event from the page. Hit-testing a
  // mousemove is what lets the overlay stay `pointer-events: none`.
  useEffect(() => {
    if (!enabled || !placed.length) { setHover(null); return }
    const onMove = (e: MouseEvent) => {
      const x = e.pageX
      const y = e.pageY
      // topmost = the SMALLEST rect under the cursor, so a small box inside a big
      // one is still reachable
      let best: Placed | null = null
      let bestArea = Infinity
      for (const p of placed) {
        const r = p.place.rect
        if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) {
          const area = r.w * r.h
          if (area < bestArea) { best = p; bestArea = area }
        }
      }
      setHover(best ? { p: best, x: e.clientX, y: e.clientY } : null)
    }
    window.addEventListener('mousemove', onMove, { passive: true })
    return () => window.removeEventListener('mousemove', onMove)
  }, [placed, enabled])

  const tip = useMemo(() => {
    if (!hover) return null
    const r = hover.p.report
    const last = [...(r.notes || [])].reverse().find((n) => n.by === 'reviewer')
    return {
      number: r.number,
      title: r.title || '',
      label: r.glow?.label || r.status,
      first: (r.notes || [])[0]?.text || '',
      answer: last?.text || '',
      approximate: hover.p.place.approximate,
      tone: toneOf(r),
    }
  }, [hover])

  // Rendered into <body> on purpose: `position: absolute` resolves against the
  // nearest POSITIONED ancestor, so a `relative` wrapper anywhere up the layout
  // would silently re-base every coordinate. Portalling removes that dependency
  // entirely — document pixels stay document pixels.
  const [host, setHost] = useState<HTMLElement | null>(null)
  useEffect(() => { setHost(document.body) }, [])

  if (!enabled || !placed.length || !host) return null

  return createPortal(
    (<>
      {/* pointer-events:none on the layer AND on every child — the page below
          must behave exactly as though this did not exist. */}
      <div
        data-inspection-layer="1"
        data-testid="inspection-highlight-layer"
        aria-hidden="true"
        className="no-print"
        style={{
          position: 'absolute', top: 0, left: 0, width: 0, height: 0,
          pointerEvents: 'none', zIndex: 60,
        }}
      >
        {placed.map(({ report, place }) => {
          const tone = toneOf(report)
          return (
            <div
              key={report.id}
              data-inspection-highlight={report.number}
              style={{
                position: 'absolute',
                left: place.rect.x, top: place.rect.y,
                width: place.rect.w, height: place.rect.h,
                pointerEvents: 'none',
                background: `rgba(${tone}, ${opacity})`,
                border: `1.5px ${place.approximate ? 'dashed' : 'solid'} rgba(${tone}, ${Math.min(1, opacity + 0.45)})`,
                borderRadius: 4,
                boxShadow: `0 0 0 1px rgba(255,255,255,0.25) inset`,
                transition: 'background 120ms linear',
              }}
            />
          )
        })}
      </div>

      {tip && hover && (
        <div
          dir="rtl"
          className="no-print"
          style={{
            position: 'fixed',
            left: Math.min(hover.x + 14, (typeof window !== 'undefined' ? window.innerWidth : 1200) - 330),
            top: Math.min(hover.y + 14, (typeof window !== 'undefined' ? window.innerHeight : 800) - 190),
            width: 310, pointerEvents: 'none', zIndex: 61,
            background: 'rgba(17,17,17,0.94)', color: '#fff',
            borderRadius: 10, padding: '9px 11px', fontSize: 12, lineHeight: 1.8,
            boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
            borderRight: `4px solid rgb(${tip.tone})`,
          }}
        >
          <div style={{ fontWeight: 700 }}>
            گزارشِ {tip.number}{tip.title ? ` — ${tip.title}` : ''}
          </div>
          <div style={{ opacity: 0.85 }}>وضعیت: {tip.label}</div>
          {!!tip.first && (
            <div style={{ marginTop: 4, opacity: 0.95 }}>
              {tip.first.length > 160 ? `${tip.first.slice(0, 160)}…` : tip.first}
            </div>
          )}
          {!!tip.answer && (
            <div style={{ marginTop: 4, opacity: 0.8 }}>
              پاسخِ ناظر: {tip.answer.length > 120 ? `${tip.answer.slice(0, 120)}…` : tip.answer}
            </div>
          )}
          {tip.approximate && (
            <div style={{ marginTop: 4, color: '#fbbf24' }}>
              ⚠ جای تقریبی — عنصرِ اصلی پیدا نشد، از مختصاتِ ذخیره‌شده استفاده شد
            </div>
          )}
        </div>
      )}
    </>),
    host,
  )
}
