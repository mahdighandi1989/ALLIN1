// v126 — repair of "custom PDF font encoding" mojibake, mirroring
// backend/app/services/mojibake.py (keep the two in step).
//
// Some PDF writers embed a SUBSET font with a non-standard internal encoding.
// The page looks perfect, but the text LAYER underneath holds different code
// points, so anything that reads that layer — an extractor, or an LLM handed the
// PDF — reproduces reversible garbage:
//
//     "Statement NO"  ->  "Í¬¿¬»³»²¬ ÒÑ"
//     "Amount (IRR)"  ->  "ß³±«²¬ (×ÎÎ)"
//
// The substitution reflects a letter's code point around 0x120, so the same
// arithmetic undoes it. Only the 52 ASCII letters are hit — digits, spaces and
// punctuation come through clean, which is why a garbled statement still shows
// correct dates and amounts.
//
//     A(0x41)..Z(0x5A) -> 0xDF..0xC6      a(0x61)..z(0x7A) -> 0xBF..0xA6
//
// The two source ranges contain characters that also occur legitimately — above
// all the Persian quotation marks « (0xAB) and » (0xBB), plus ° ± ² ³ · §. So the
// decision is made PER TEXT NODE and is deliberately conservative: a node is only
// repaired when it is overwhelmingly made of these characters AND holds no
// Persian/Arabic letter. A Persian sentence with «quotes» can never qualify.

const PIVOT = 0x120
const UP_LO = PIVOT - 'Z'.charCodeAt(0)   // 0xC6
const UP_HI = PIVOT - 'A'.charCodeAt(0)   // 0xDF
const LO_LO = PIVOT - 'z'.charCodeAt(0)   // 0xA6
const LO_HI = PIVOT - 'a'.charCodeAt(0)   // 0xBF

const PERSIAN = /[؀-ۿﭐ-﷿ﹰ-﻿]/

const isMapped = (code: number) =>
  (code >= LO_LO && code <= LO_HI) || (code >= UP_LO && code <= UP_HI)

/**
 * Cheap pre-filter: could this string possibly contain mojibake at all?
 *
 * The real check parses HTML into a DOM, which is far too expensive to run on
 * every keystroke of a long letter. Two ADJACENT characters from the affected
 * ranges is the minimum any repairable chunk can have, and ordinary Persian or
 * Latin text never produces that — so this regex skips the DOM work entirely in
 * the overwhelmingly common case.
 */
export function mightBeGarbled(s: string): boolean {
  return !!s && /[\u00A6-\u00BF\u00C6-\u00DF]{2,}/.test(s)
}

/** True when this chunk is almost certainly a garbled Latin string. */
export function looksGarbled(text: string, minChars = 2, minRatio = 0.5): boolean {
  if (!text) return false
  if (PERSIAN.test(text)) return false
  let mapped = 0, letters = 0
  for (const ch of text) {
    const c = ch.codePointAt(0) as number
    const m = isMapped(c)
    if (m) mapped++
    if (m || /\p{L}/u.test(ch)) letters++
  }
  if (mapped < minChars || letters === 0) return false
  return mapped / letters >= minRatio
}

/** Repair one chunk if it qualifies; otherwise return it untouched. */
export function repairText(text: string): string {
  if (!looksGarbled(text)) return text
  let out = ''
  for (const ch of text) {
    const c = ch.codePointAt(0) as number
    out += isMapped(c) ? String.fromCodePoint(PIVOT - c) : ch
  }
  return out
}

/** Repair a multi-line block, judging each cell/line separately. */
export function repairBlock(text: string): string {
  if (!text) return text
  return text.replace(/[^\n\r\t|]+/g, (m) => repairText(m))
}

/**
 * Repair an HTML fragment by walking its TEXT NODES only — tags, attributes,
 * styles and column widths are never touched, so a repaired table keeps exactly
 * the layout the user built. Returns the new HTML and how many nodes changed.
 */
export function repairHtml(html: string): { html: string; fixed: number } {
  if (!html || typeof document === 'undefined' || !mightBeGarbled(html)) return { html, fixed: 0 }
  const host = document.createElement('div')
  host.innerHTML = html
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT)
  let fixed = 0
  const nodes: Text[] = []
  for (let n = walker.nextNode(); n; n = walker.nextNode()) nodes.push(n as Text)
  for (const n of nodes) {
    const before = n.nodeValue || ''
    const after = repairBlock(before)
    if (after !== before) { n.nodeValue = after; fixed++ }
  }
  return { html: fixed ? host.innerHTML : html, fixed }
}

/** How many text nodes of this HTML fragment would be repaired (0 = clean). */
export function countGarbledHtml(html: string): number {
  if (!html || typeof document === 'undefined' || !mightBeGarbled(html)) return 0
  const host = document.createElement('div')
  host.innerHTML = html
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT)
  let n = 0
  for (let x = walker.nextNode(); x; x = walker.nextNode()) {
    const v = (x as Text).nodeValue || ''
    if (v !== repairBlock(v)) n++
  }
  return n
}
