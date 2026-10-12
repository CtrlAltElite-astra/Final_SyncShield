import { useState } from 'react'
import { createReport } from './api.js'

const CATEGORIES = ['flood', 'collapse', 'medical', 'fire', 'road_block', 'shelter', 'other']

export default function CreateReportForm({ regions, onDone }) {
  const [region, setRegion] = useState(regions[0].id)
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState('collapse')
  const [severity, setSeverity] = useState(3)
  const [msg, setMsg] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    const target = regions.find((r) => r.id === region)
    try {
      const res = await createReport(target, { title, category, severity: Number(severity) })
      setMsg(`${res.event_id} saved in ${region}`)
      setTitle('')
      onDone()
    } catch (err) {
      setMsg(`failed: ${err.message}`)
    }
  }

  return (
    <form className="create" onSubmit={submit}>
      <strong>New report in</strong>
      <select value={region} onChange={(e) => setRegion(e.target.value)}>
        {regions.map((r) => <option key={r.id}>{r.id}</option>)}
      </select>
      <input required maxLength={120} placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
      </select>
      <label>sev <input type="number" min="1" max="5" value={severity} onChange={(e) => setSeverity(e.target.value)} /></label>
      <button type="submit">Create</button>
      <span className="muted">{msg}</span>
    </form>
  )
}
