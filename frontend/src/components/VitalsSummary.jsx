import { summarizeVitals } from '../services/vitals'

function formatTime(value) {
  return new Date(value).toLocaleString()
}

export default function VitalsSummary({ patient, measurements }) {
  if (!patient) {
    return (
      <section className="card">
        <h2>Measurement summary</h2>
        <p className="hint">Select a patient to review recorded measurements.</p>
      </section>
    )
  }

  if (measurements.length === 0) {
    return (
      <section className="card">
        <h2>Measurement summary</h2>
        <p className="hint">{patient.reference} has no measurements yet.</p>
      </section>
    )
  }

  const latest = measurements[0]
  const summary = summarizeVitals(latest)

  return (
    <section className="card">
      <h2>Measurement summary</h2>
      <p className="hint">
        Latest reading for {patient.reference} — {formatTime(latest.measured_at)} ({latest.source}).
      </p>

      <div className="summary-grid">
        {summary.map((item) => (
          <div className="summary-item" key={item.label}>
            <span className="summary-label">{item.label}</span>
            <span className="summary-value">{item.value}</span>
            <span className={`badge badge-${item.band.tone}`}>{item.band.label}</span>
          </div>
        ))}
      </div>

      <p className="disclaimer">
        Informational prototype categories only — not a diagnosis and not a substitute for clinical assessment.
      </p>

      <h3>History ({measurements.length})</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Measured at</th>
              <th>BP (mmHg)</th>
              <th>Pulse (bpm)</th>
              <th>Temp (°C)</th>
              <th>SpO₂ (%)</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {measurements.map((item) => (
              <tr key={item.id}>
                <td>{formatTime(item.measured_at)}</td>
                <td>{item.systolic_bp}/{item.diastolic_bp}</td>
                <td>{item.pulse}</td>
                <td>{item.temperature_c}</td>
                <td>{item.spo2}</td>
                <td>{item.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
