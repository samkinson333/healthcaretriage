import { useState } from 'react'
import { recordDeterioration } from '../services/api'

export default function PriorityQueue({ queue, onRefresh, onAdvanceClock }) {
  const [busy, setBusy] = useState(false)

  async function handleDeterioration(assessmentId) {
    setBusy(true)
    try {
      await recordDeterioration(assessmentId, crypto.randomUUID())
      onRefresh()
    } catch (e) {
      alert('Failed to escalate: ' + e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <div className="flex justify-between items-center">
        <h2>Waiting queue</h2>
        <div>
          <button onClick={() => onAdvanceClock(15)} disabled={busy} className="btn-sm">+15m</button>
          <button onClick={() => onAdvanceClock(60)} disabled={busy} className="btn-sm">+60m</button>
        </div>
      </div>

      {queue.length === 0 && <p>No patients waiting. Register a patient to start.</p>}

      {queue.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>REF</th>
              <th>LVL</th>
              <th>Wait</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {queue.map(row => (
              <tr key={row.id}>
                <td>{row.patient.reference}</td>
                <td><span className={`chip chip-${row.display_level.toLowerCase()}`}>{row.display_level}</span></td>
                <td>{row.wait_minutes}m</td>
                <td>
                  <button onClick={() => handleDeterioration(row.id)} disabled={busy} className="btn-sm">Deteriorate</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
