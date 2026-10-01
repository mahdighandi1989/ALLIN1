'use client'
// v141 — «نظارت و سرکشی» on the client: the owner arms a box, draws it around
// what is wrong, writes a line, and the sheet is filed with the way BACK to it.
//
// Two pieces of evidence, and the difference matters:
//   • the ADDRESS — always taken, always true (see `inspectionSpot.ts`);
//   • the PICTURE — either a real screenshot the owner PASTES from their own
//     operating system (the honest one), or a render of the region taken with
//     the same rasteriser the letter page already uses. The compose box says
//     which one it is, because a near-miss render offered as «this is what I
//     saw» is worse evidence than none.
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { inspectionApi, parseApiError, type InspectionReport } from './api'
import { notifySheetsChanged } from './inspectionHighlights'
import { shrinkShot } from './shrinkShot'
import {
  CROP_MIN_PX, geometryLabel, measureSpot, pageElementsAt, pickCaptureTarget, pickCropSheet,
  resolveSpot, spotAddress, verifiedSelector,
  type Rect, type UiSpot,
} from './inspectionSpot'

type Ctx = {
  active: boolean
  setActive: (v: boolean) => void
  arm: () => void
  reports: InspectionReport[]
  refresh: () => Promise<void>
  loading: boolean
}

const InspectionCtx = createContext<Ctx | null>(null)
export const useInspection = () => useContext(InspectionCtx)

const LS_KEY = 'allin1.inspection.active'

export function InspectionProvider({ children }: { children: React.ReactNode }) {
  const [active, setActiveRaw] = useState(false)
  const [armed, setArmed] = useState(false)
  const [rect, setRect] = useState<Rect | null>(null)
  const [spot, setSpot] = useState<UiSpot | null>(null)
  const [shot, setShot] = useState<{ data: string; kind: 'pasted' | 'rendered' } | null>(null)
  // v154 — the capture takes seconds on a big page and used to give no sign at
  // all. The owner pressed the button, saw nothing, filed the report, and it
  // arrived with no picture (measured on production: shot_id = None). Silence
  // during a slow operation is indistinguishable from «it did nothing».
  const [shooting, setShooting] = useState(false)
  const [text, setText] = useState('')
  // v146 — samples the owner wants the supervisor to read: any type, any size up
  // to the server's ceiling. They are uploaded AFTER the sheet exists, because a
  // 100MB body cannot ride along inside the JSON that creates it.
  const [picked, setPicked] = useState<File[]>([])
  const [target, setTarget] = useState('')   // '' = a new sheet; otherwise the sheet this goes under
  const [upPct, setUpPct] = useState<{ name: string; pct: number } | null>(null)
  const [busy, setBusy] = useState(false)
  const [reports, setReports] = useState<InspectionReport[]>([])
  const [loading, setLoading] = useState(false)
  const start = useRef<{ x: number; y: number } | null>(null)

  useEffect(() => {
    try { setActiveRaw(localStorage.getItem(LS_KEY) === '1') } catch { /* private mode */ }
  }, [])
  const setActive = useCallback((v: boolean) => {
    setActiveRaw(v)
    try { localStorage.setItem(LS_KEY, v ? '1' : '0') } catch { /* private mode */ }
  }, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      setReports((await inspectionApi.list()).reports)
      // v150 — tell the highlight overlay too, so a sheet just filed appears on
      // the spot immediately instead of at the next navigation.
      notifySheetsChanged()
    } catch { /* not signed in yet */ }
    finally { setLoading(false) }
  }, [])
  useEffect(() => { if (active) void refresh() }, [active, refresh])

  const arm = useCallback(() => setArmed(true), [])

  // Alt is the other way in, so the gesture is always available without the
  // button — and Escape always gets out.
  useEffect(() => {
    if (!active) return
    const down = (e: KeyboardEvent) => {
      if (e.key === 'Alt') setArmed(true)
      if (e.key === 'Escape' && (armed || spot)) { setArmed(false); setRect(null); setSpot(null) }
    }
    const up = (e: KeyboardEvent) => { if (e.key === 'Alt' && !start.current) setArmed(false) }
    window.addEventListener('keydown', down, true)
    window.addEventListener('keyup', up, true)
    return () => {
      window.removeEventListener('keydown', down, true)
      window.removeEventListener('keyup', up, true)
    }
  }, [active, armed, spot])

  const onDown = (e: React.PointerEvent) => {
    start.current = { x: e.clientX, y: e.clientY }
    setRect({ x: e.clientX, y: e.clientY, w: 0, h: 0 })
  }
  const onMove = (e: React.PointerEvent) => {
    const s = start.current
    if (!s) return
    setRect({
      x: Math.min(s.x, e.clientX), y: Math.min(s.y, e.clientY),
      w: Math.abs(e.clientX - s.x), h: Math.abs(e.clientY - s.y),
    })
  }
  const onUp = async () => {
    const s = start.current
    start.current = null
    const r = rect
    setRect(null)
    setArmed(false)
    if (!s || !r || r.w < CROP_MIN_PX || r.h < CROP_MIN_PX) return
    // What the rectangle covers, asked of the DOM at its centre. The overlay is
    // excluded, or `elementsFromPoint` would answer «the overlay», every time.
    const cx = r.x + r.w / 2
    const cy = r.y + r.h / 2
    const stack = pageElementsAt(cx, cy)
    // v150 — measure the box precisely, by the owner's instruction. The anchor is
    // the innermost element under the box's centre; its selector is round-trip
    // verified inside `verifiedSelector`, so an unusable one is stored as empty
    // rather than as a wrong answer.
    const anchor = stack[0] ?? null
    const anchorPath = verifiedSelector(anchor)
    const ab = anchor?.getBoundingClientRect()
    const sx = window.scrollX || window.pageXOffset || 0
    const sy = window.scrollY || window.pageYOffset || 0
    const geometry = measureSpot({
      rect: r,
      viewport: { w: window.innerWidth, h: window.innerHeight },
      scroll: { x: sx, y: sy },
      doc_size: {
        w: Math.max(document.documentElement.scrollWidth, window.innerWidth),
        h: Math.max(document.documentElement.scrollHeight, window.innerHeight),
      },
      dpr: window.devicePixelRatio || 1,
      anchor,
      // the anchor's rect in DOCUMENT space, to match the box we store
      anchorRect: ab ? { x: ab.left + sx, y: ab.top + sy, w: ab.width, h: ab.height } : null,
      anchorPath,
    })
    const resolved = resolveSpot({
      rect: r, viewport: { w: window.innerWidth, h: window.innerHeight }, stack, geometry,
    })
    setSpot(resolved)
    setText('')
    setShot(null)
    // v154 — CAPTURE AT ONCE, without being asked.
    //
    // Requiring a second button press cost the owner a report: they drew the box,
    // wrote the text, filed it, and it arrived with no picture at all. A picture
    // that depends on remembering an extra step is a picture that will be missing
    // exactly when it matters. It runs while they type, so it is free, and a
    // pasted screenshot always wins over it (see the guard in `renderRegion`).
    //
    // The spot is passed in rather than read from state: `setSpot` has not
    // committed yet at this point, and reading it here would capture the PREVIOUS
    // box — a picture of the wrong place, which is worse than none.
    void renderRegion(resolved)
  }

  /** Render the covered region — clearly labelled as a render, never as a photo. */
  const renderRegion = useCallback(async (spotArg?: UiSpot) => {
    const sp = spotArg ?? spot
    if (!sp) return
    setShooting(true)
    try {
      const { toJpeg } = await import('html-to-image')
      // The dialog is already open by the time this runs, so «skip our own UI»
      // has to mean the whole layer, not just its root — see `isOurOverlay`.
      const el = pageElementsAt(
        sp.rect.x + sp.rect.w / 2, sp.rect.y + sp.rect.h / 2,
      )[0] as HTMLElement | undefined
      // The camera points at the whole reportable surface (v153), because that is
      // what the rasteriser draws faithfully; when the surface is a stack of A4
      // sheets, the finished picture is cut down to the ONE sheet the box landed
      // on — «فقط همان صفحه باید باشه». Both rules, and the browser evidence
      // behind them, live with `pickCaptureTarget` / `pickCropSheet`.
      const target = pickCaptureTarget(el)
      if (!target) return
      const sheet = pickCropSheet(el, target)
      // v154 — `backgroundColor` is not optional for JPEG. Without it the element's
      // transparent background becomes BLACK, and the capture came out as a dark
      // negative of a white page — technically a screenshot, practically unreadable.
      // Seen only by looking at the produced file; no assertion would have caught it.
      // v165 — `margin: 0` is not cosmetic, it is the difference between a mark
      // that points at the right thing and one that does not. The rasteriser
      // copies the COMPUTED style onto its clone, and a centred element
      // (`mx-auto` on the surface here) computes its `auto` margins to real
      // pixels — so the clone was drawn shifted inside its own picture by half
      // the leftover width. Measured in Chromium on a 1400px window: a constant
      // 36px to the right, zero vertical, zero scale. Every mark was off by that
      // much, on every page — «مختصاتش خیلی اشتباه و دقیق نیست». The element's
      // own margin has no business being inside a picture OF that element.
      const data = await toJpeg(target, {
        quality: 0.82, pixelRatio: 1, cacheBust: true,
        backgroundColor: '#ffffff',
        style: { margin: '0' },
      })
      // v153 — MARK THE BOX ON THE PICTURE. The capture is of the whole sheet
      // (or surface), which is what makes it worth looking at, but unmarked it
      // only says «somewhere on this page». The owner asked for both to corroborate each
      // other: «اگر با مختصات پیدا نکرد با عکس بتونه تطبیق بده». If the anchor
      // element is gone later and the coordinates fall back to «approximate»,
      // the marked picture is what still pins the spot down.
      const tr = target.getBoundingClientRect()
      let out = data
      try {
        const { annotate, boxInImage } = await import('./annotateShot')
        const probe = new Image()
        await new Promise<void>((res, rej) => {
          probe.onload = () => res(); probe.onerror = () => rej(new Error('x')); probe.src = data
        })
        // v165 — the rasteriser renders the element's BORDER BOX (offsetWidth ×
        // offsetHeight), so that is the box the picture's pixels map onto. The
        // visible rectangle can differ from it in exactly one way that matters
        // here: a CSS transform (the printable sheets are scaled to fit the
        // screen), and that ratio is what turns a viewport coordinate back into
        // a layout coordinate. Scrolling needs no compensation — a scroll
        // container's border box IS its visible box, and the rasteriser renders
        // that same border box.
        const geom = {
          left: tr.left, top: tr.top, width: tr.width, height: tr.height,
          layoutWidth: target.offsetWidth, layoutHeight: target.offsetHeight,
        }
        const image = { width: probe.naturalWidth, height: probe.naturalHeight }
        const box = boxInImage(sp.rect, geom, image)
        // the sheet, measured the very same way, so the crop and the mark can
        // never disagree about where anything is
        const sr = sheet?.getBoundingClientRect()
        const crop = sr
          ? boxInImage({ x: sr.left, y: sr.top, w: sr.width, h: sr.height }, geom, image)
          : null
        if (box) out = await annotate(data, box, crop)
      } catch {
        // marking failed — keep the plain capture rather than losing the evidence
      }
      out = await shrinkShot(out)      // v175 — a tall surface renders big too
      setShot((prev) => (prev?.kind === 'pasted' ? prev : { data: out, kind: 'rendered' }))
    } catch (e) {
      toast.error('تصویربرداری از این بخش ممکن نشد — می‌توانی اسکرین‌شاتِ خودت را بچسبانی')
    } finally { setShooting(false) }
  }, [spot])

  /** A real screenshot from the owner's own OS, pasted in. The best evidence. */
  const onPaste = useCallback((e: React.ClipboardEvent) => {
    const item = Array.from(e.clipboardData?.items || []).find((i) => i.type.startsWith('image/'))
    if (!item) return
    const file = item.getAsFile()
    if (!file) return
    e.preventDefault()
    const fr = new FileReader()
    // v175 — SHRINK BEFORE IT IS EVER HELD, let alone sent. A 4K screenshot is
    // 10-15 MB as a data URL and the server used to refuse anything over ~1.4 MB
    // («String should have at most 1400000 characters»), so the owner's own
    // screenshot — the best evidence this system can get — was the one thing it
    // turned away. `shrinkShot` never fails: if the browser cannot re-encode, the
    // original is kept, because a big picture beats no picture.
    fr.onload = () => {
      const raw = String(fr.result || '')
      setShot({ data: raw, kind: 'pasted' })
      void shrinkShot(raw).then((small) => {
        if (small !== raw) setShot((prev) => (prev?.data === raw ? { data: small, kind: 'pasted' } : prev))
      })
    }
    fr.readAsDataURL(file)
  }, [])

  // v158 — «به عنوان گزارش جدید باشه یا بره ذیل گزارشی که هنوز تایید مالک روش
  // انجام نشده و بایگانی نشده». Only sheets still in play are offered: once the
  // owner has ticked a sheet or it has been archived, that conversation is over
  // and a new observation deserves its own sheet.
  const openSheets = useMemo(
    () => reports.filter((r) => r.status === 'open' || r.status === 'answered'),
    [reports])

  const submit = async () => {
    if (!spot || !text.trim()) return
    setBusy(true)
    try {
      const under = target && openSheets.some((r) => r.id === target) ? target : ''
      // A follow-up needs a sheet to hang its files on BEFORE the note exists, so
      // the sheet is chosen first and the files are claimed by the note at the end.
      const rep = under
        ? { id: under, number: openSheets.find((r) => r.id === under)?.number }
        : await inspectionApi.create({ text: text.trim(), spot, shot: shot?.data })
      // Each sample is its own request so one failure does not lose the sheet or
      // the other files — and the owner is told exactly which one did not go up.
      const failed: string[] = []
      const uploaded: string[] = []
      for (const f of picked) {
        try {
          setUpPct({ name: f.name, pct: 0 })
          const up = await inspectionApi.upload(rep.id, f, '', (pct) => setUpPct({ name: f.name, pct }))
          if (up?.file?.id) uploaded.push(up.file.id)
        } catch (e) { failed.push(`${f.name} (${parseApiError(e)})`) }
      }
      setUpPct(null)
      if (under) {
        // The follow-up carries its OWN box and screenshot, and claims only the
        // files uploaded with it — the parent sheet's samples stay the parent's.
        await inspectionApi.note(under, {
          text: text.trim(), shot: shot?.data, spot, file_ids: uploaded,
        })
      }
      if (failed.length) {
        toast.error(`${under ? 'یادداشت' : 'گزارش'} ثبت شد ولی این فایل‌ها بالا نرفتند: ${failed.join(' · ')}`)
      } else if (under) {
        toast.success(`ذیلِ گزارشِ ${rep.number ?? ''} ثبت شد — آن برگه دوباره بازِ رسیدگی شد`)
      } else {
        toast.success(picked.length
          ? `گزارش با ${picked.length} فایلِ نمونه ثبت شد — ناظر باید کاملشان را بخواند`
          : 'گزارش ثبت شد — ناظر در دورِ بعد جواب می‌دهد')
      }
      setSpot(null); setText(''); setShot(null); setPicked([]); setTarget('')
      await refresh()
    } catch (e) { toast.error(parseApiError(e)) } finally { setBusy(false); setUpPct(null) }
  }

  const value = useMemo<Ctx>(() => ({ active, setActive, arm, reports, refresh, loading }),
    [active, setActive, arm, reports, refresh, loading])

  return (
    <InspectionCtx.Provider value={value}>
      {children}
      {active && (
        <button
          onClick={arm}
          className="no-print fixed bottom-5 left-5 z-[80] rounded-full bg-amber-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-amber-700"
          title="یک کادر دورِ همان چیزی بکش که ایراد دارد (یا کلید Alt را نگه دار)"
        >📝 ثبت گزارش</button>
      )}
      {armed && (
        <div
          dir="rtl" data-inspection-layer="1"
          className="fixed inset-0 z-[90]"
          style={{ cursor: 'crosshair', background: 'rgba(15,12,8,0.18)' }}
          onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}
        >
          {rect && rect.w > 2 && (
            <div className="pointer-events-none absolute border-2 border-amber-400 bg-amber-200/10"
              style={{ left: rect.x, top: rect.y, width: rect.w, height: rect.h }} />
          )}
          <div className="pointer-events-none absolute left-1/2 top-6 -translate-x-1/2 rounded-lg bg-black/85 px-4 py-2 text-sm text-amber-100">
            کادر بکش · Esc انصراف
          </div>
        </div>
      )}
      {spot && (
        <div dir="rtl" data-inspection-layer="1"
          className="fixed inset-0 z-[95] flex items-center justify-center bg-black/50 p-4"
          onClick={(e) => { if (e.target === e.currentTarget) { setSpot(null); setPicked([]) } }}>
          <div className="w-full max-w-lg rounded-xl bg-white p-4 shadow-2xl">
            <div className="mb-2 text-sm font-bold text-gray-900">گزارشِ نظارت و سرکشی</div>
            <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-2.5 text-[11px] text-amber-900">
              <div className="font-semibold">{spotAddress(spot)}</div>
              <div className="mt-1 text-amber-800" dir="ltr">{spot.reopen}</div>
              {!!spot.covered_text && (
                <div className="mt-1 line-clamp-3 text-amber-700">آنچه در کادر بود: {spot.covered_text}</div>
              )}
              {!!spot.geometry && (
                <div dir="rtl" className="mt-1 text-amber-800">
                  مختصات: {geometryLabel(spot.geometry)}
                  {spot.geometry.anchor.path
                    ? ' · به عنصرِ زیرش گره خورد (با تغییرِ چیدمان هم سرِ جایش می‌ماند)'
                    : ' · گره به عنصر ممکن نشد — فقط مختصاتِ سند ذخیره می‌شود'}
                </div>
              )}
            </div>
            {/* v158 — «بتونم انتخاب کنم که به عنوان گزارش جدید باشه یا بره ذیل
                گزارشی که هنوز تایید مالک روش انجام نشده و بایگانی نشده».
                The box just drawn and the screenshot travel EITHER way, so a
                follow-up still records where it was pointing. */}
            {openSheets.length > 0 && (
              <div className="mb-2">
                <label className="mb-1 block text-[11px] font-semibold text-gray-700">
                  این را کجا ثبت کنم؟
                </label>
                <select
                  value={target} onChange={(e) => setTarget(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 p-2 text-xs focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="">گزارشِ جدید</option>
                  {openSheets.map((r) => (
                    <option key={r.id} value={r.id}>
                      ذیلِ گزارشِ {r.number} — {(r.title || '').slice(0, 48)}
                      {r.status === 'answered' ? ' (پاسخ گرفته)' : ''}
                    </option>
                  ))}
                </select>
                {!!target && (
                  <div className="mt-1 text-[11px] text-amber-800">
                    ذیلِ آن برگه ثبت می‌شود، با کادر و تصویرِ خودش؛ فایل‌هایی که اینجا
                    پیوست کنی فقط مالِ همین یادداشت‌اند و با پیوست‌های قبلی قاتی نمی‌شوند.
                    آن برگه دوباره «بازِ رسیدگی» می‌شود.
                  </div>
                )}
              </div>
            )}
            <textarea
              value={text} onChange={(e) => setText(e.target.value)} onPaste={onPaste}
              rows={4} autoFocus
              placeholder="چه ایرادی دارد، یا چه می‌خواهی؟ (می‌توانی اسکرین‌شاتِ خودت را همین‌جا Ctrl+V کنی)"
              className="w-full rounded-lg border border-gray-300 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            {/* v146 — «باید بشه فایل هم اپلود کرد … هر نوع فایلی». No `accept`
                filter on purpose: a Word sample of a document format, a PDF, a
                picture pulled off the web, a spreadsheet — all are valid. */}
            <label className="mt-2 flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-gray-300 px-3 py-2 text-xs text-gray-600 hover:border-amber-400 hover:bg-amber-50/40">
              <span>📎 فایلِ نمونه پیوست کن (هر نوعی — ورد، PDF، عکس، اکسل…)</span>
              <input
                type="file" multiple className="hidden"
                onChange={(e) => {
                  const list = Array.from(e.target.files || [])
                  if (list.length) setPicked((prev) => [...prev, ...list])
                  e.target.value = ''
                }}
              />
            </label>
            {!!picked.length && (
              <div className="mt-1.5 space-y-1">
                {picked.map((f, i) => (
                  <div key={`${f.name}-${i}`} dir="rtl"
                    className="flex items-center gap-2 rounded-md bg-gray-50 px-2 py-1 text-[11px] text-gray-700">
                    <span className="truncate">{f.name}</span>
                    <span className="text-gray-400">{(f.size / (1024 * 1024)).toFixed(1)} مگابایت</span>
                    <span className="flex-1" />
                    <button type="button" title="برداشتن"
                      onClick={() => setPicked((prev) => prev.filter((_, j) => j !== i))}
                      className="text-red-600 hover:underline">×</button>
                  </div>
                ))}
                <div className="text-[11px] text-emerald-700">
                  ناظر موظف است متنِ کاملِ این فایل‌ها را بخواند — تا نخواند نمی‌تواند برگه را جواب بدهد.
                </div>
              </div>
            )}
            {upPct && (
              <div dir="rtl" className="mt-1.5 text-[11px] text-amber-800">
                در حالِ بالا رفتن: {upPct.name} — {upPct.pct}٪
              </div>
            )}
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <button onClick={() => void renderRegion()} type="button" disabled={shooting}
                className="rounded-lg border border-gray-300 px-2.5 py-1 text-xs hover:bg-gray-50 disabled:opacity-50">
                {shooting ? '… در حالِ گرفتنِ تصویر' : '📷 گرفتنِ دوبارهٔ تصویر'}
              </button>
              {shooting && !shot && (
                <span className="text-[11px] text-gray-600">
                  تصویرِ صفحه در حالِ گرفته‌شدن است… (می‌توانی هم‌زمان بنویسی)
                </span>
              )}
              {shot && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={shot.data} alt="پیش‌نمایشِ تصویر"
                  className="h-12 w-auto rounded border border-gray-300" />
              )}
              {shot && (
                <span className={`text-[11px] ${shot.kind === 'pasted' ? 'text-emerald-700' : 'text-amber-700'}`}>
                  {shot.kind === 'pasted'
                    ? '✓ اسکرین‌شاتِ واقعیِ خودت پیوست شد — کادرِ انتخابی رویش علامت نخورده'
                    : '⚠ تصویرِ بازسازی‌شده از کلِ همین صفحه، با کادرِ انتخابیِ تو علامت‌خورده (عکسِ واقعی نیست) — اگر دقیق نبود، اسکرین‌شاتِ خودت را Ctrl+V کن'}
                </span>
              )}
              <span className="flex-1" />
              <button onClick={() => { setSpot(null); setPicked([]) }} type="button"
                className="rounded-lg px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100">انصراف</button>
              {/* v154 — filing while the capture is still running is how the
                  owner's report ended up with no picture. Wait for it: the sheet
                  is worth the two seconds, and the button says why it waits. */}
              <button onClick={submit} disabled={busy || shooting || !text.trim()}
                title={shooting ? 'تا آماده‌شدنِ تصویر صبر کن' : ''}
                className="rounded-lg bg-amber-600 px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-50">
                {busy ? '...' : shooting ? 'تصویر…' : 'ثبت گزارش'}
              </button>
            </div>
          </div>
        </div>
      )}
    </InspectionCtx.Provider>
  )
}

/**
 * THE SHEETS FILED FROM THIS VERY SECTION, AND WHAT CAME BACK.
 *
 * A sheet about a screen has nowhere to hang, so it hangs HERE — at the bottom
 * of the section it is about, where the owner is standing when they wonder what
 * happened to it. It renders nothing at all when the section has no sheets, so
 * an untouched screen is not cluttered.
 */
export function SectionReports({ reopen }: { reopen: string }) {
  const ins = useInspection()
  const mine = useMemo(
    () => (ins?.reports || []).filter((r) => r.reopen === reopen),
    [ins?.reports, reopen],
  )
  if (!ins?.active) return null
  return (
    <div dir="rtl" className="mt-3 border-t border-gray-200 pt-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] text-gray-500">
          {mine.length ? `${mine.length} گزارش برای همین بخش` : 'گزارشی برای این بخش ثبت نشده'}
        </span>
        <button type="button" onClick={ins.arm}
          className="rounded border border-amber-400 px-2 py-[3px] text-[10px] text-amber-700 hover:bg-amber-50">
          📝 گزارش از همین‌جا
        </button>
      </div>
      {mine.map((r) => (
        <div key={r.id} className="mt-1.5 rounded border border-gray-200 bg-gray-50 p-1.5 text-[11px]">
          <div className="flex items-center gap-2">
            <span className={`rounded px-1.5 py-[1px] text-[10px] text-white ${TONE[r.glow?.tone || 'open']}`}>
              {r.glow?.label}
            </span>
            <span className="text-gray-700">#{r.number} — {r.title}</span>
          </div>
          {r.notes?.filter((n) => n.by === 'reviewer').slice(-1).map((n) => (
            <div key={n.id} className="mt-1 whitespace-pre-wrap text-gray-600">{n.text}</div>
          ))}
        </div>
      ))}
    </div>
  )
}

export const TONE: Record<string, string> = {
  open: 'bg-amber-500',
  answered: 'bg-emerald-600',
  approved: 'bg-blue-600',
  filed: 'bg-gray-400',
  fixed: 'bg-emerald-600',
  partial: 'bg-yellow-600',
  'needs-owner': 'bg-purple-600',
  'not-done': 'bg-red-600',
  stale: 'bg-gray-500',
}
