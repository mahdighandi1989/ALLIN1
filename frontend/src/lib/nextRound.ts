// v168 — «ناظر چند دقیقهٔ دیگر می‌رود سراغش؟»
//
// «وقتی دکمه فوری میزنم باید ناظر بگه چند دقیقه دیگه میره سراغش … هر دور دقیق
// به ساعت محلی بسنجه و پیام بده» — مالک، ۲۰۲۶‑۰۹‑۳۰.
//
// The server sends ONE thing: the instant the next fast round is due, in UTC.
// The clock is read here, in the browser, because «ساعتِ محلی» means the clock
// the owner is actually looking at — a server that formats a time has to guess a
// timezone, and a countdown that is off by four hours is worse than none.
//
// Everything below is pure so the sentence itself can be tested: it is what the
// owner reads, and it has to be right about both the number and the honesty of
// the number (see `basis`).

export type NextRound = {
  /** ISO-8601 UTC instant the next round is due */
  at: string
  in_seconds: number
  in_minutes: number
  /** the measured cadence, in minutes */
  every_minutes: number
  /** observed = we have watched it · assumed = a default, nothing watched yet ·
   *  stale = it has not come for several cycles, so it may be switched off ·
   *  due = its slot (`at`) has just passed and it has not knocked yet — late, not gone */
  basis: 'observed' | 'assumed' | 'stale' | 'due' | string
  last_seen: string | null
}

const fa = (n: number | string) => String(n).replace(/\d/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[+d])

/** The local wall clock, as «۱۰:۲۳» — the owner's own, never the server's. */
export function localClock(iso: string, now?: Date): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  const sameDay = !now || d.toDateString() === now.toDateString()
  return sameDay ? fa(`${hh}:${mm}`) : `${fa(`${hh}:${mm}`)} (فردا)`
}

/** «۱۹ دقیقهٔ دیگر» / «کمتر از یک دقیقه» / «۱ ساعت و ۵ دقیقهٔ دیگر» */
export function humanGap(minutes: number): string {
  if (!Number.isFinite(minutes) || minutes <= 0) return 'همین حالا'
  if (minutes < 1) return 'کمتر از یک دقیقهٔ دیگر'
  if (minutes < 60) return `${fa(Math.round(minutes))} دقیقهٔ دیگر`
  const h = Math.floor(minutes / 60)
  const m = Math.round(minutes % 60)
  return m ? `${fa(h)} ساعت و ${fa(m)} دقیقهٔ دیگر` : `${fa(h)} ساعتِ دیگر`
}

/** «هر ۳ ساعت» / «هر ۴۵ دقیقه» — the measured cadence in the owner's words. */
export function everyText(minutes: number): string {
  if (!Number.isFinite(minutes) || minutes <= 0) return ''
  return minutes % 60 === 0 ? `هر ${fa(minutes / 60)} ساعت` : `هر ${fa(Math.round(minutes))} دقیقه`
}

/**
 * The whole sentence the owner sees after pressing ⚡.
 *
 * `position` is where this sheet sits in the fast queue. Being second does NOT
 * mean waiting a second round — the round works through the queue one sheet at
 * a time in the same visit — so the wording says «نوبتِ دوم» rather than
 * inventing a second arrival time nobody promised.
 */
export function rushMessage(position: number, nr?: NextRound | null, now?: Date): string {
  const place = position === 1
    ? 'در صفِ فوری، نفرِ اول'
    : `در صفِ فوری، نفرِ ${fa(position)} — به ترتیبی که زدی انجام می‌شود`
  if (!nr || !nr.at) return `${place} — ناظر در بازبینیِ بعدی برمی‌داردش`
  if (nr.basis === 'stale') {
    return `${place} — ولی ناظر از ${localClock(nr.last_seen || nr.at, now)} تا حالا سر نزده؛`
      + ' ممکن است روتینش خاموش باشد. بررسی کن.'
  }
  if (nr.basis === 'due') {
    return `${place} · دورِ ناظر قرار بود ساعتِ ${localClock(nr.at, now)} باشد و هر لحظه می‌رسد`
  }
  const when = `ساعتِ ${localClock(nr.at, now)} (${humanGap(nr.in_minutes)})`
  const hedge = nr.basis === 'assumed' ? ' — تخمینی، هنوز دوری ثبت نشده' : ''
  return `${place} · ناظر ${when} می‌رود سراغش${hedge}`
}
