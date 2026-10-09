import { useMemo, useState } from 'react'

export default function NurseWorklist({ queue, onClose }) {
  const nurseCases = useMemo(
    () => queue.filter((row) => row.assignment?.role === 'nurse'),
    [queue],
  )
  const nurses = useMemo(
    () => [...new Set(nurseCases.map((row) => row.assignment.assignee))].sort(),
    [nurseCases],
  )
  const [selectedNurse, setSelectedNurse] = useState('')
  const visibleCases = selectedNurse
    ? nurseCases.filter((row) => row.assignment.assignee === selectedNurse)
    : nurseCases

  return (
    <main className="nurse-worklist" aria-labelledby="nurse-worklist-title">
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">Assigned emergency handoffs</p>
          <h2 id="nurse-worklist-title">Nurse worklist</h2>
          <p className="dashboard-description">Demo view only. Choose your name to see patients assigned to you by a doctor.</p>
        </div>
        <button type="button" className="button-secondary" onClick={onClose}>Back to doctor dashboard</button>
      </div>

      <div className="nurse-filter">
        <label htmlFor="nurse-assignee">Assigned nurse</label>
        <select id="nurse-assignee" value={selectedNurse} onChange={(event) => setSelectedNurse(event.target.value)}>
          <option value="">All assigned nurses</option>
          {nurses.map((nurse) => <option key={nurse} value={nurse}>{nurse}</option>)}
        </select>
      </div>

      {visibleCases.length === 0 ? (
        <div className="dashboard-empty">
          <h3>No assigned emergency patients</h3>
          <p>When a doctor assigns a U1 or U2 patient to a nurse, the patient’s OP details will appear here.</p>
        </div>
      ) : (
        <div className="nurse-case-grid">
          {visibleCases.map((row) => (
            <article className="nurse-case" key={row.id}>
              <div className="nurse-case-heading">
                <span className={`urgency-chip urgency urgency-${row.display_level.toLowerCase()}`}>{row.display_level}</span>
                <span className="reassess-note">Assigned to you</span>
              </div>
              <h3>{row.patient.full_name || 'Unnamed patient'}</h3>
              <dl className="patient-details">
                <div><dt>OP / patient reference</dt><dd>{row.patient.reference}</dd></div>
                <div><dt>Age / sex</dt><dd>{row.patient.age} years · {row.patient.sex}</dd></div>
                <div><dt>Complaint</dt><dd>{row.complaint || 'Not recorded'}</dd></div>
                <div><dt>Wait time</dt><dd>{row.wait_minutes} min</dd></div>
                <div><dt>Assigned by doctor</dt><dd>Emergency responder handoff</dd></div>
              </dl>
              {row.needs_reassessment && <p className="nurse-alert">Reassessment is due—seek clinician review.</p>}
            </article>
          ))}
        </div>
      )}
    </main>
  )
}
