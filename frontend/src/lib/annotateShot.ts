// v153 — draw the owner's rectangle ONTO the picture.
//
// «کل صفحه رو اسکرین نشون داده … ولی اون کادر هم باید تو عکس باشه تا مشخص بشه
// تو صفحه کجا رو انتخاب کرده بودم … اگر با مختصات پیدا نکرد با عکس بتونه تطبیق
// بده یا هر دو کمکِ هم دیگه باشن»
//
// The capture is of the whole surface on purpose — context is what makes a
// screenshot worth looking at — but without a mark on it, the picture says
// «somewhere on this page». The coordinates and the picture are meant to
// corroborate each other: if the anchor element is gone and the coordinates fall
// back to «approximate», the marked picture is what still pins it down.
//
// Pure canvas work, and exported separately so it can be tested without a
// rasteriser.

export type Box = { x: number; y: number; w: number; h: number }

/** The element as both the owner and the rasteriser see it. */
export type TargetGeom = {
  /** its box in VIEWPORT coordinates — what the owner drew on */
  left: number; top: number; width: number; height: number
  /** its BORDER-BOX size (offsetWidth/offsetHeight) — what the rasteriser
   *  renders. Differs from the viewport box only when a CSS transform scales it. */
  layoutWidth?: number; layoutHeight?: number
}

/**
 * The box, moved from viewport coordinates into the captured image's own.
 *
 * Two scales are in play and they are not the same:
 *   • a CSS transform can make the element appear larger or smaller than it is
 *     laid out  →  viewport box ÷ layout box
 *   • the rasteriser can draw at more than one device pixel per CSS pixel
 *     →  picture ÷ layout box
 *
 * Deriving both from the viewport box (as this did until v165) is right only
 * while the two happen to agree, and silently wrong otherwise. Note that a
 * scroll container needs NO special case: its border box IS its visible box, and
 * the rasteriser renders that same border box, so the two already agree.
 */
export function boxInImage(
  box: Box,
  target: TargetGeom,
  image: { width: number; height: number },
): Box | null {
  const lw = target.layoutWidth || target.width
  const lh = target.layoutHeight || target.height
  if (!lw || !lh || !image.width || !image.height) return null
  const zoomX = target.width / lw || 1        // CSS transform, 1 when there is none
  const zoomY = target.height / lh || 1
  const sx = image.width / lw                 // picture per laid-out pixel
  const sy = image.height / lh
  const out = {
    x: ((box.x - target.left) / zoomX) * sx,
    y: ((box.y - target.top) / zoomY) * sy,
    w: (box.w / zoomX) * sx,
    h: (box.h / zoomY) * sy,
  }
  // a box wholly outside the captured element would draw a mark on empty space,
  // which is worse than no mark: it would point somewhere the owner never clicked
  if (out.x + out.w < 0 || out.y + out.h < 0) return null
  if (out.x > image.width || out.y > image.height) return null
  return out
}

/**
 * Return a new data-URL with the region outlined and everything else dimmed.
 *
 * Dimming rather than only outlining, because on a busy page a thin rectangle
 * disappears into the layout — the point is that the eye lands on it at once.
 */
export async function annotate(dataUrl: string, box: Box, crop?: Box | null): Promise<string> {
  const img = await loadImage(dataUrl)
  const iw = img.naturalWidth || img.width
  const ih = img.naturalHeight || img.height
  // v165 — cut the picture down to the one sheet the owner pointed at, AFTER
  // the rasteriser has drawn the whole surface. See `pickCropSheet` for why the
  // camera is not simply pointed at the sheet in the first place.
  const c = clampCrop(crop, iw, ih)
  const canvas = document.createElement('canvas')
  canvas.width = c ? c.w : iw
  canvas.height = c ? c.h : ih
  const ctx = canvas.getContext('2d')
  if (!ctx) return dataUrl               // no canvas: the plain picture is still useful
  if (c) {
    ctx.drawImage(img, c.x, c.y, c.w, c.h, 0, 0, c.w, c.h)
    box = { x: box.x - c.x, y: box.y - c.y, w: box.w, h: box.h }
  } else {
    ctx.drawImage(img, 0, 0)
  }

  // dim everything outside the box, in four rectangles around it
  ctx.fillStyle = 'rgba(17, 17, 17, 0.45)'
  ctx.fillRect(0, 0, canvas.width, Math.max(0, box.y))
  ctx.fillRect(0, box.y + box.h, canvas.width, Math.max(0, canvas.height - (box.y + box.h)))
  ctx.fillRect(0, box.y, Math.max(0, box.x), box.h)
  ctx.fillRect(box.x + box.w, box.y, Math.max(0, canvas.width - (box.x + box.w)), box.h)

  // the outline: a dark line under a bright one, so it reads on any background
  const w = Math.max(2, Math.round(canvas.width / 400))
  ctx.lineWidth = w + 2
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.75)'
  ctx.strokeRect(box.x, box.y, box.w, box.h)
  ctx.lineWidth = w
  ctx.strokeStyle = '#f59e0b'
  ctx.strokeRect(box.x, box.y, box.w, box.h)

  return canvas.toDataURL('image/jpeg', 0.85)
}

/**
 * The crop region, made safe: whole pixels, inside the picture, and dropped
 * altogether when it is degenerate or already the whole picture. Cropping to a
 * region that is partly outside the image draws transparent padding, which on a
 * JPEG comes out black — the v154 bug again, by another route.
 */
export function clampCrop(crop: Box | null | undefined, iw: number, ih: number): Box | null {
  if (!crop || !iw || !ih) return null
  const x = Math.max(0, Math.floor(crop.x))
  const y = Math.max(0, Math.floor(crop.y))
  const w = Math.min(Math.ceil(crop.w), iw - x)
  const h = Math.min(Math.ceil(crop.h), ih - y)
  if (w < 16 || h < 16) return null                  // nothing usable to show
  if (x === 0 && y === 0 && w === iw && h === ih) return null   // already the whole picture
  return { x, y, w, h }
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('image did not load'))
    img.src = src
  })
}
