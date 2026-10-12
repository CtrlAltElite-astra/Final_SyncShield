import { patchField } from './api.js'

const STATUSES = ['open', 'assigned', 'resolved', 'closed', 'cancelled']

function StatusCard({ region, status }) {
  return (
    <div className="card">
      <div className="row">
        <h2>{region.id.toUpperCase()}</h2>
        <span className={`badge level-${status.level}`}>{status.level}</span>
      </div>
      <div className="muted">{region.url}</div>
      <div className="kv">heads <code>{JSON.stringify(status.heads)}</code></div>
      <div className="kv">events <code>{status.event_count}</code> · quarantined <code>{status.quarantined}</code></div>
      <div className="kv">digest <code>{status.event_digest.slice(0, 10)}</code> state <code>{status.state_hash.slice(0, 10)}</code></div>
      <div className="chips">
        {Object.entries(status.peers).map(([p, s]) => (
          <span key={p} className={`chip ${s.link === 'down' ? 'bad' : s.reachable ? 'good' : 'warn'}`}
                title={s.last_error || 'ok'}>
            {p}: link {s.link}{s.reachable ? '' : ' · unreachable'}
          </span>
        ))}
      </div>
    </div>
  )
}

function Row({ region, rep, onChange }) {
  const s = rep.state
  const set = async (field, value) => {
    try { await patchField(region, rep.report_id, field, value) } finally { onChange() }
  }
  return (
    <tr className={rep.conflicts.length ? 'conflict' : ''}>
      <td><code>{rep.report_id}</code></td>
      <td>{s.title}</td>
      <td>
        <select value={s.severity ?? ''} onChange={(e) => set('severity', Number(e.target.value))}>
          {[1, 2, 3, 4, 5].map((n) => <option key={n}>{n}</option>)}
        </select>
      </td>
      <td>
        <select value={s.status ?? ''} onChange={(e) => set('status', e.target.value)}>
          {STATUSES.map((v) => <option key={v}>{v}</option>)}
        </select>
      </td>
      <td>
        {rep.conflicts.map((c) => (
          <div key={c.field} className="chip warn" title={`${c.rule}: ${c.event_ids.join(', ')}`}>
            {c.field}: {c.values.join(' / ')}
          </div>
        ))}
      </td>
      <td className="muted">{rep.consistency.replication}</td>
    </tr>
  )
}

export default function RegionColumn({ region, snap, onChange }) {
  if (!snap) return <section className="col"><div className="card muted">loading {region.id}…</div></section>
  if (!snap.ok) {
    return (
      <section className="col">
        <div className="card down">
          <h2>{region.id.toUpperCase()}</h2>
          <strong>UNREACHABLE</strong>
          <div className="muted">{region.url} — {snap.error}</div>
        </div>
      </section>
    )
  }
  return (
    <section className="col">
      <StatusCard region={region} status={snap.status} />
      <table>
        <thead><tr><th>id</th><th>title</th><th>sev</th><th>status</th><th>conflicts</th><th>repl</th></tr></thead>
        <tbody>
          {snap.reports.map((r) => <Row key={r.report_id} region={region} rep={r} onChange={onChange} />)}
          {!snap.reports.length && <tr><td colSpan="6" className="muted">no reports</td></tr>}
        </tbody>
      </table>
    </section>
  )
}
