'use client'
// v152 — an <img> cannot carry a Bearer token.
//
// The inspection board rendered screenshots with `<img src="/api/inspection/
// shots/{id}">` and offered files with `<a href="/api/inspection/files/{id}/raw">`.
// Both are plain browser requests: no Authorization header, so the API answered
// 401 and EVERY screenshot on the board showed as a broken image. The owner saw
// it first — «اون عبارت تصویر گزارشم … انگار عکسی وجود نداره».
//
// Verified directly against production: the same URL returns 200 with a Bearer
// token and 401 without one.
//
// The app already had the answer — `downloadFile()` fetches a binary endpoint
// through the authenticated client and hands the browser a blob. These two
// components do the same for images and links, so nothing has to change about
// how the API is protected.
import React, { useEffect, useState } from 'react'
import { api } from './axios'

/** An <img> whose bytes are fetched WITH the session's token. */
export function AuthedImage({
  src, alt, className, style, onClick,
}: {
  src: string
  alt: string
  className?: string
  style?: React.CSSProperties
  onClick?: () => void
}) {
  const [url, setUrl] = useState<string | null>(null)
  const [failed, setFailed] = useState<string>('')

  useEffect(() => {
    let alive = true
    let made: string | null = null
    setUrl(null); setFailed('')
    ;(async () => {
      try {
        const { data } = await api.get(src, { responseType: 'blob' })
        if (!alive) return
        made = URL.createObjectURL(data as Blob)
        setUrl(made)
      } catch (e: any) {
        if (!alive) return
        // never a silent broken-image icon: say what went wrong
        const code = e?.response?.status
        setFailed(code === 404 ? 'تصویر پیدا نشد'
          : code === 401 ? 'برای دیدنِ تصویر باید وارد باشی'
            : 'تصویر بارگذاری نشد')
      }
    })()
    return () => {
      alive = false
      if (made) URL.revokeObjectURL(made)   // or every view leaks a blob
    }
  }, [src])

  if (failed) {
    return (
      <div dir="rtl" className={`flex items-center justify-center rounded border border-dashed
        border-gray-300 bg-gray-50 text-[11px] text-gray-500 ${className || ''}`}
        style={{ minHeight: 64, ...style }}>
        {failed}
      </div>
    )
  }
  if (!url) {
    return (
      <div className={`animate-pulse rounded bg-gray-100 ${className || ''}`}
        style={{ minHeight: 64, ...style }} />
    )
  }
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt={alt} className={className} style={style} onClick={onClick} />
}

/** A link that downloads a protected file through the authenticated client. */
export function AuthedDownload({
  href, filename, children, className, inline = false,
}: {
  href: string
  filename: string
  children: React.ReactNode
  className?: string
  /** open it in a tab (images, PDFs) instead of saving it */
  inline?: boolean
}) {
  const [busy, setBusy] = useState(false)
  const go = async () => {
    setBusy(true)
    try {
      const { data } = await api.get(href, { responseType: 'blob' })
      const url = URL.createObjectURL(data as Blob)
      if (inline) {
        window.open(url, '_blank', 'noopener')
        // the tab needs the url to survive; a minute is plenty and still frees it
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
      } else {
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      }
    } catch {
      // the caller's page shows its own errors; a dead link that says nothing is
      // the thing being fixed here, so at least tell the user
      alert('فایل گرفته نشد — شاید دیگر در دسترس نیست')
    } finally { setBusy(false) }
  }
  return (
    <button type="button" onClick={go} disabled={busy} className={className}>
      {busy ? '…' : children}
    </button>
  )
}
