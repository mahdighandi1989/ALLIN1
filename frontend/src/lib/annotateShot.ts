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

/** The box, moved from viewport coordinates into the captured image's own. */
export function boxInImage(
  box: Box,
  targetRect: { left: number; top: number; width: number; height: number },
  image: { width: number; height: number },
): Box | null {
  if (!targetRect.width || !targetRect.height || !image.width || !image.height) return null
  // the capture may be rendered at a different scale than the element on screen
  const sx = image.width / targetRect.width
  const sy = image.height / targetRect.height
  const out = {
    x: (box.x - targetRect.left) * sx,
    y: (box.y - targetRect.top) * sy,
    w: box.w * sx,
    h: box.h * sy,
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
export async function annotate(dataUrl: string, box: Box): Promise<string> {
  const img = await loadImage(dataUrl)
  const canvas = document.createElement('canvas')
  canvas.width = img.naturalWidth || img.width
  canvas.height = img.naturalHeight || img.height
  const ctx = canvas.getContext('2d')
  if (!ctx) return dataUrl               // no canvas: the plain picture is still useful
  ctx.drawImage(img, 0, 0)

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

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('image did not load'))
    img.src = src
  })
}
