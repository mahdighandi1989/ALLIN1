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
              <span className="cmb-lbl" title={o.label}>{o.label}</span>
              {o.sub && <span className="cmb-sub" title={o.sub}>{o.sub}</span>}
            </div>
          ))}
        </div>
      )}
      <style>{`
        .cmb-in{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:7px;padding:6px 9px;font-size:13px;background:#fff;color:#0f172a}
        .cmb-in:focus{outline:none;border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.18)}
        .cmb-pop{position:absolute;z-index:90;top:calc(100% + 4px);right:0;left:0;min-width:230px;background:#fff;border:1px solid #e2e8f0;border-radius:10px;box-shadow:0 12px 30px rgba(15,23,42,.18);max-height:280px;overflow-y:auto;padding:4px}
        .cmb-pop::-webkit-scrollbar{width:8px}.cmb-pop::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:8px}
        .cmb-opt{display:flex;flex-direction:column;gap:1px;padding:6px 9px;cursor:pointer;border-radius:7px}
        .cmb-opt.hi,.cmb-opt:hover{background:#eff6ff}
        .cmb-lbl{color:#0f172a;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cmb-sub{color:#94a3b8;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      `}</style>
    </div>
  )
}
