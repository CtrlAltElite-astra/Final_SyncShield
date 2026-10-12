import { useEffect, useState } from 'react'
import { REGIONS, pollRegion, setPairLink } from './api.js'
import RegionColumn from './RegionColumn.jsx'
import CreateReportForm from './CreateReportForm.jsx'

// CONVERGED only when every region is reachable and all report the same digests. Else UNKNOWN or DIVERGED.
function convergence(snaps) {
  if (snaps.some((s) => !s || !s.ok)) return 'UNKNOWN'
  const same = (k) => new Set(snaps.map((s) => s.status[k])).size === 1
  return same('event_digest') && same('state_hash') ? 'CONVERGED' : 'DIVERGED'
}

export default function App() {
  const [snaps, setSnaps] = useState([])
  const [busy, setBusy] = useState(false)

  const refresh = async () => setSnaps(await Promise.all(REGIONS.map(pollRegion)))
  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 1000)
    return () => clearInterval(t)
  }, [])

  const bySnap = (id) => snaps.find((s) => s.id === id)
  const linkMode = (a, b) => bySnap(a)?.status?.peers?.[b]?.link
  const pairs = REGIONS.flatMap((a, i) => REGIONS.slice(i + 1).map((b) => [a, b]))

  const toggle = async (a, b) => {
    setBusy(true)
    const down = linkMode(a.id, b.id) === 'down' || linkMode(b.id, a.id) === 'down'
    await setPairLink(a, b, down ? 'up' : 'down')
    await refresh()
    setBusy(false)
  }

  const conv = convergence(snaps)
  return (
    <div className="app">
      <header>
        <h1>Lifeboat</h1>
        <span className={`badge conv-${conv}`}>{conv}</span>
        <div className="spacer" />
        {pairs.map(([a, b]) => {
          const down = linkMode(a.id, b.id) === 'down' || linkMode(b.id, a.id) === 'down'
          return (
            <button key={a.id + b.id} disabled={busy} className={down ? 'heal' : 'cut'} onClick={() => toggle(a, b)}>
              {down ? `Heal ${a.id}↔${b.id}` : `Cut ${a.id}↔${b.id}`}
            </button>
          )
        })}
      </header>
      <CreateReportForm regions={REGIONS} onDone={refresh} />
      <main style={{ gridTemplateColumns: `repeat(${REGIONS.length}, minmax(0, 1fr))` }}>
        {REGIONS.map((r) => (
          <RegionColumn key={r.id} region={r} snap={bySnap(r.id)} onChange={refresh} />
        ))}
      </main>
    </div>
  )
}
