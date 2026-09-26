'use client'
// v138 — the «ورد» / «اکسل» buttons for the Credit File Summary pages.
//
// Both forms (Corporate and Retail) get the SAME two buttons from here, so the
// two pages can never drift apart in behaviour, and a third sheet form added
// later inherits the exports by calling this hook.
//
// Word is built in the browser with `docx` and Excel on the server with
// openpyxl — the split the voucher export established (v105): the client
// describes what it is showing, the server renders the workbook with a real
// library.
import React, { useCallback, useState } from 'react'
import toast from 'react-hot-toast'
import { creditFileApi, parseApiError } from './api'
import { readSheetSpec, sheetFileBase } from './sheetSpec'

function saveBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  // revoke on the next tick — revoking synchronously cancels the download in
  // some browsers before it has read the blob
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function useSheetExport(opts: {
  sheetRef: React.RefObject<HTMLDivElement>
  account: string
  /** run the page's print-fit first, so the measured column widths are the
   *  ones the PRINTED sheet uses, not the on-screen ones */
  fit?: () => void
}) {
  const [busy, setBusy] = useState<'' | 'word' | 'excel'>('')

  const read = useCallback(() => {
    const el = opts.sheetRef.current
    if (!el) throw new Error('فرم هنوز آماده نیست')
    opts.fit?.()
    const spec = readSheetSpec(el, opts.account)
    if (!spec.blocks.length) throw new Error('چیزی برای خروجی‌گرفتن پیدا نشد')
    return spec
  }, [opts])

  const exportWord = useCallback(async () => {
    setBusy('word')
    const id = toast.loading('در حال ساختِ فایلِ Word…')
    try {
      const spec = read()
      // loaded on demand: the docx builder is large and neither form needs it
      // until the officer actually asks for a file
      const { buildSheetDocx } = await import('./sheetWordExport')
      saveBlob(await buildSheetDocx(spec, BUILD_TAG), `${sheetFileBase(spec)}.docx`)
      toast.success('فایلِ Word دانلود شد — همهٔ خانه‌ها قابلِ ویرایش‌اند', { id })
    } catch (e: any) {
      toast.error(e?.message || parseApiError(e), { id })
    } finally { setBusy('') }
  }, [read])

  const exportExcel = useCallback(async () => {
    setBusy('excel')
    const id = toast.loading('در حال ساختِ فایلِ Excel…')
    try {
      const spec = read()
      const blob = await creditFileApi.exportExcel(spec as any)
      saveBlob(blob, `${sheetFileBase(spec)}.xlsx`)
      toast.success('فایلِ Excel دانلود شد', { id })
    } catch (e: any) {
      toast.error(e?.message || parseApiError(e), { id })
    } finally { setBusy('') }
  }, [read])

  const buttons = (
    <>
      <button onClick={exportWord} disabled={!!busy} className="cf-btn" style={{ background: '#1d4ed8' }}
        title="دانلودِ همین فرم به‌صورت Word — همان چیزی که در پرینت می‌بینی، با خانه‌های قابلِ ویرایش">
        {busy === 'word' ? '...' : '⬇ ورد'}
      </button>
      <button onClick={exportExcel} disabled={!!busy} className="cf-btn" style={{ background: '#047857' }}
        title="دانلودِ همین فرم به‌صورت Excel — همان چیزی که در پرینت می‌بینی، با خانه‌های قابلِ ویرایش">
        {busy === 'excel' ? '...' : '⬇ اکسل'}
      </button>
    </>
  )

  return { buttons, exportWord, exportExcel, busy }
}

// kept in lock-step with the pages' visible build marker by the release sed
const BUILD_TAG = 'v138'
