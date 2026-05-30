'use client'

import React from 'react'

/**
 * Dependency-free SVG charts (the project ships no chart library and builds to a
 * static export, so we keep these self-contained and deterministic).
 */

const PALETTE = [
  '#2563eb', '#16a34a', '#f59e0b', '#dc2626',
  '#7c3aed', '#0891b2', '#db2777', '#65a30d',
]

function formatCompact(n: number): string {
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (Math.abs(n) >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(Math.round(n))
}

export interface Slice {
  label: string
  count: number
  amount?: number
}

/** A donut chart with a legend. Uses count by default. */
export function DonutChart({
  data,
  size = 160,
  valueKey = 'count',
}: {
  data: Slice[]
  size?: number
  valueKey?: 'count' | 'amount'
}) {
  const items = (data || []).filter((d) => (d[valueKey] ?? 0) > 0)
  const total = items.reduce((s, d) => s + (d[valueKey] ?? 0), 0)
  const radius = size / 2
  const stroke = size * 0.18
  const r = radius - stroke / 2
  const circumference = 2 * Math.PI * r

  if (total === 0) {
    return <p className="text-sm text-gray-400 py-8 text-center">No data</p>
  }

  let offset = 0
  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img">
        <g transform={`rotate(-90 ${radius} ${radius})`}>
          {items.map((d, i) => {
            const value = d[valueKey] ?? 0
            const frac = value / total
            const dash = frac * circumference
            const seg = (
              <circle
                key={d.label}
                cx={radius}
                cy={radius}
                r={r}
                fill="none"
                stroke={PALETTE[i % PALETTE.length]}
                strokeWidth={stroke}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-offset}
              />
            )
            offset += dash
            return seg
          })}
        </g>
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-gray-700"
          style={{ fontSize: size * 0.16, fontWeight: 700 }}
        >
          {valueKey === 'amount' ? formatCompact(total) : total}
        </text>
      </svg>
      <ul className="space-y-1 text-sm">
        {items.map((d, i) => (
          <li key={d.label} className="flex items-center gap-2">
            <span
              className="inline-block w-3 h-3 rounded-sm"
              style={{ background: PALETTE[i % PALETTE.length] }}
            />
            <span className="capitalize text-gray-700">{d.label}</span>
            <span className="text-gray-400">
              ({valueKey === 'amount' ? formatCompact(d.amount ?? 0) : d.count})
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** A horizontal bar chart (label + value bars). */
export function BarChart({
  data,
  valueKey = 'count',
}: {
  data: Slice[]
  valueKey?: 'count' | 'amount'
}) {
  const items = data || []
  const max = Math.max(1, ...items.map((d) => d[valueKey] ?? 0))
  if (items.length === 0) {
    return <p className="text-sm text-gray-400 py-8 text-center">No data</p>
  }
  return (
    <div className="space-y-2">
      {items.map((d, i) => {
        const value = d[valueKey] ?? 0
        const pct = (value / max) * 100
        return (
          <div key={d.label} className="flex items-center gap-2 text-sm">
            <span className="w-24 shrink-0 capitalize text-gray-600 truncate" title={d.label}>
              {d.label}
            </span>
            <div className="flex-1 bg-gray-100 rounded h-5 overflow-hidden">
              <div
                className="h-full rounded"
                style={{ width: `${pct}%`, background: PALETTE[i % PALETTE.length], minWidth: 2 }}
              />
            </div>
            <span className="w-16 text-right text-gray-700 tabular-nums">
              {valueKey === 'amount' ? formatCompact(value) : value}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export interface TrendPoint {
  month: string
  exposure: number
  facilities: number
}

/** A simple line/area chart for the monthly exposure trend. */
export function LineChart({
  data,
  height = 180,
}: {
  data: TrendPoint[]
  height?: number
}) {
  const points = data || []
  if (points.length < 2) {
    return <p className="text-sm text-gray-400 py-8 text-center">Not enough data</p>
  }
  const width = 480
  const padX = 36
  const padY = 20
  const maxVal = Math.max(1, ...points.map((p) => p.exposure))
  const stepX = (width - padX * 2) / (points.length - 1)

  const coords = points.map((p, i) => {
    const x = padX + i * stepX
    const y = height - padY - (p.exposure / maxVal) * (height - padY * 2)
    return [x, y] as const
  })
  const line = coords.map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x} ${y}`).join(' ')
  const area =
    `M ${coords[0][0]} ${height - padY} ` +
    coords.map(([x, y]) => `L ${x} ${y}`).join(' ') +
    ` L ${coords[coords.length - 1][0]} ${height - padY} Z`

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} role="img" className="overflow-visible">
      <path d={area} fill="#2563eb" fillOpacity={0.08} />
      <path d={line} fill="none" stroke="#2563eb" strokeWidth={2.5} />
      {coords.map(([x, y], i) => (
        <g key={i}>
          <circle cx={x} cy={y} r={3} fill="#2563eb" />
          <text
            x={x}
            y={height - 4}
            textAnchor="middle"
            className="fill-gray-400"
            style={{ fontSize: 10 }}
          >
            {points[i].month.slice(2)}
          </text>
        </g>
      ))}
    </svg>
  )
}
