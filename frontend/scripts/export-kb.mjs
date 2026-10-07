// Exports the STATIC دانش‌نامه (the five tab files + the compare tab) to
// backend/app/data/kb_static.json so the backend's KB chat can read EXACTLY the
// text the page shows. The TypeScript files stay the single source of truth;
// this file is generated (run automatically by `npm run build`) — nobody edits
// the JSON by hand, so the chat can never lag behind the page.
import { createRequire } from 'node:module'
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const require = createRequire(import.meta.url)
const ts = require('typescript')
const here = dirname(fileURLToPath(import.meta.url))
const dir = resolve(here, '../src/app/knowledge')
const out = resolve(here, '../../backend/app/data/kb_static.json')

const cache = new Map()
function load(name) {
  if (cache.has(name)) return cache.get(name)
  const src = readFileSync(resolve(dir, name + '.ts'), 'utf8')
  const js = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 } }).outputText
  const mod = { exports: {} }
  cache.set(name, mod.exports)
  new Function('exports', 'require', 'module', js)(mod.exports, (p) => load(p.replace(/^\.\//, '')), mod)
  cache.set(name, mod.exports)
  return mod.exports
}

function blockText(b) {
  switch (b.type) {
    case 'p': case 'sub': case 'note': case 'code': return b.text
    case 'ul': return b.items.map((i) => '- ' + i).join('\n')
    case 'ol': return b.items.map((i, k) => `${k + 1}. ${i}`).join('\n')
    case 'table': return [b.headers.join(' | '), ...b.rows.map((r) => r.join(' | '))].join('\n')
    default: return ''
  }
}

const tabs = load('tabs').KB_TABS
const result = { generated_from: 'frontend/src/app/knowledge/*.ts', tabs: [] }
for (const t of tabs) {
  if (t.id === 'compare') continue
  result.tabs.push({
    id: t.id,
    label: t.label,
    sections: t.sections.map((s) => ({
      id: s.id,
      title: s.title,
      status: s.status || 'verified',
      text: s.blocks.map(blockText).filter(Boolean).join('\n\n'),
    })),
  })
}
const cmp = load('content-compare')
const labels = { saderat: 'بانک صادرات', uae: 'امارات', iran: 'ایران', intl: 'بین‌المللی', islamic: 'اسلامی' }
result.compare = cmp.COMPARE_ROWS.map((r) => ({
  topic: r.topic,
  verdict: cmp.VERDICT_LABEL[r.verdict] || r.verdict,
  text: Object.keys(labels).filter((k) => r[k]).map((k) => `${labels[k]}: ${r[k]}`).join('\n') + (r.note ? `\nیادداشت: ${r.note}` : ''),
}))

mkdirSync(dirname(out), { recursive: true })
const next = JSON.stringify(result, null, 1) + '\n'
let prev = ''
try { prev = readFileSync(out, 'utf8') } catch { /* first run */ }
if (prev !== next) writeFileSync(out, next)
const n = result.tabs.reduce((a, t) => a + t.sections.length, 0)
console.log(`export-kb: ${result.tabs.length} tabs, ${n} sections, ${result.compare.length} compare rows → ${prev === next ? 'unchanged' : 'written'}`)
