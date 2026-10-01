// v175 — A SCREENSHOT MUST NEVER BE REFUSED FOR BEING A SCREENSHOT.
//
// «این خطایی که موقع ثبت گزارش میزنم و ریشه‌ای درست کن که محدودیتی نباشه».
//
// The owner pasted a screenshot and the report came back
// «shot: String should have at most 1400000 characters» — about a megabyte of
// base64, which is smaller than an ordinary full-screen PNG. The one thing that
// makes this system worth having, a real picture of what they saw, was the thing
// it turned away.
//
// Raising the server's number alone would only move the wall. The root is that
// the page was shipping whatever the clipboard happened to hold: a 4K PNG is
// 10-15 MB, and none of that size is evidence. A screenshot is read by a person
// and described to a text model; past a couple of thousand pixels on the long
// side it carries no more meaning, only bytes.
//
// So every picture — pasted or rendered — is re-encoded here before it is sent.
// From the owner's side there is no limit: anything they paste is accepted.
//
// WHAT IT WILL NOT DO: it never fails. If the browser cannot give us a canvas
// (private mode, a blocked API, a data URL that will not decode), the ORIGINAL
// is returned unchanged. A smaller picture is better than a big one; no picture
// at all is worse than either.

/** How long we wait for the browser to decode the picture before giving up.
 *  A decoder that never answers must not leave the owner looking at a dialog
 *  with no picture and no error — found by a test, where jsdom fires neither
 *  `onload` nor `onerror` for a data URL and the promise hung for ever. */
export const SHOT_DECODE_MS = 8000

/** Longest side we keep. Above this, a screenshot is bytes, not evidence. */
export const SHOT_MAX_PX = 2600

/** The data-URL length we aim to stay under — comfortably below the server's. */
export const SHOT_MAX_CHARS = 3_000_000

/** Qualities tried in order, before the picture is made smaller instead. */
export const SHOT_QUALITIES = [0.85, 0.7, 0.55, 0.42] as const

/**
 * The size to redraw at: the same shape, with the long side capped.
 *
 * Pure, because the arithmetic is the part that can be wrong in a way nobody
 * notices — a squashed screenshot still looks like a screenshot.
 */
export function planSize(w: number, h: number, maxPx = SHOT_MAX_PX): { w: number; h: number } {
  if (!(w > 0) || !(h > 0)) return { w: 0, h: 0 }
  const long = Math.max(w, h)
  if (long <= maxPx) return { w: Math.round(w), h: Math.round(h) }
  const k = maxPx / long
  return { w: Math.max(1, Math.round(w * k)), h: Math.max(1, Math.round(h * k)) }
}

/** Does this data URL already need nothing done to it? */
export function isSmallEnough(dataUrl: string, w: number, h: number,
                              maxChars = SHOT_MAX_CHARS, maxPx = SHOT_MAX_PX): boolean {
  return dataUrl.length <= maxChars && Math.max(w, h) <= maxPx
}

/**
 * The same picture, small enough to send. Never throws, never returns nothing.
 *
 * JPEG on a WHITE background on purpose: a PNG with transparency re-encoded as
 * JPEG without a fill comes out as a black negative — the v154 bug, which cost
 * the owner a whole round of unreadable captures.
 */
export async function shrinkShot(
  dataUrl: string,
  opts: { maxPx?: number; maxChars?: number } = {},
): Promise<string> {
  const maxPx = opts.maxPx ?? SHOT_MAX_PX
  const maxChars = opts.maxChars ?? SHOT_MAX_CHARS
  if (!dataUrl || !dataUrl.startsWith('data:image/')) return dataUrl
  try {
    const img = await loadImage(dataUrl)
    const w = img.naturalWidth || img.width
    const h = img.naturalHeight || img.height
    if (isSmallEnough(dataUrl, w, h, maxChars, maxPx)) return dataUrl

    let size = planSize(w, h, maxPx)
    for (let pass = 0; pass < 4; pass++) {
      const canvas = document.createElement('canvas')
      canvas.width = size.w
      canvas.height = size.h
      const ctx = canvas.getContext('2d')
      if (!ctx) return dataUrl                     // no canvas: keep the evidence
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, size.w, size.h)
      ctx.drawImage(img, 0, 0, size.w, size.h)
      for (const q of SHOT_QUALITIES) {
        const out = canvas.toDataURL('image/jpeg', q)
        if (out.length <= maxChars) return out
      }
      // still too heavy at the lowest quality — halve the picture and try again
      size = planSize(size.w, size.h, Math.round(Math.max(size.w, size.h) / 2))
      if (size.w < 200 || size.h < 200) {
        return canvas.toDataURL('image/jpeg', SHOT_QUALITIES[SHOT_QUALITIES.length - 1])
      }
    }
    return dataUrl
  } catch {
    return dataUrl                                  // never lose the picture
  }
}

function loadImage(src: string, ms = SHOT_DECODE_MS): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const t = setTimeout(() => reject(new Error('image decode timed out')), ms)
    img.onload = () => { clearTimeout(t); resolve(img) }
    img.onerror = () => { clearTimeout(t); reject(new Error('image did not load')) }
    img.src = src
  })
}
