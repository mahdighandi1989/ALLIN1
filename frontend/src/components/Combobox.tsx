'use client'

// A small searchable dropdown that also accepts free text (pick existing OR add new).
import { useState, useEffect, useRef } from 'react'

export type ComboOption = { value: string; label: string; sub?: string; data?: any }

export default function Combobox({ value, onChange, onPick, fetch, placeholder, style }:
  { value: string; onChange: (v: string) => void; onPick?: (o: ComboOption) => void; fetch: (q: string) => Promise<ComboOption[]>; placeholder?: string; style?: React.CSSProperties }) {
  const [open, setOpen] = useState(false)
  const [opts, setOpts] = useState<ComboOption[]>([])
  const [hi, setHi] = useState(-1)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    let live = true
    const t = setTimeout(async () => { try { const r = await fetch(value); if (live) { setOpts(r); setHi(-1) } } catch { if (live) setOpts([]) } }, 180)
    return () => { live = false; clearTimeout(t) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, open])

  useEffect(() => {
    const onDoc = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', onDoc); return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const choose = (o: ComboOption) => { onChange(o.value); onPick?.(o); setOpen(false) }

  return (
    <div ref={ref} className="cmb" style={{ position: 'relative', ...style }}>
      <input value={value} placeholder={placeholder} className="cmb-in" onFocus={() => setOpen(true)}
        onChange={(e) => { onChange(e.target.value); setOpen(true) }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setHi((h) => Math.min(h + 1, opts.length - 1)) }
          else if (e.key === 'ArrowUp') { e.preventDefault(); setHi((h) => Math.max(h - 1, 0)) }
          else if (e.key === 'Enter' && open && hi >= 0 && opts[hi]) { e.preventDefault(); choose(opts[hi]) }
          else if (e.key === 'Escape') setOpen(false)
        }} />
      {open && opts.length > 0 && (
        <div className="cmb-pop">
          {opts.map((o, i) => (
            <div key={o.value + ':' + i} className={`cmb-opt${i === hi ? ' hi' : ''}`}
              onMouseEnter={() => setHi(i)} onMouseDown={(e) => { e.preventDefault(); choose(o) }}>
              <span className="cmb-lbl">{o.label}</span>{o.sub && <span className="cmb-sub">{o.sub}</span>}
            </div>
          ))}
        </div>
      )}
      <style>{`
        .cmb-in{width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:5px 8px;font-size:13px;background:#fff;color:#0f172a}
        .cmb-in:focus{outline:none;border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.18)}
        .cmb-pop{position:absolute;z-index:90;top:100%;right:0;left:0;margin-top:3px;background:#fff;border:1px solid #cbd5e1;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.15);max-height:240px;overflow:auto}
        .cmb-opt{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:6px 9px;cursor:pointer;font-size:13px}
        .cmb-opt.hi,.cmb-opt:hover{background:#eff6ff}
        .cmb-lbl{color:#0f172a}
        .cmb-sub{color:#94a3b8;font-size:11px;white-space:nowrap}
      `}</style>
    </div>
  )
}
