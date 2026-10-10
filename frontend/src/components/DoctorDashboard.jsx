import { useMemo, useState } from 'react'
import { assignResponder, recordDeterioration } from '../services/api'
import UrgencyChip from './UrgencyChip'

const LEVEL_COPY = {
  U1: { label: 'Immediate', action: 'See now' },
  U2: { label: 'Urgent', action: 'Prioritise next' },
  U3: { label: 'Soon', action: 'Clinical review soon' },
  U4: { label: 'Standard', action: 'Routine review' },
  U5: { label: 'Low', action: 'Staff review' },
}

function levelClass(level) {
  return `urgency urgency-${level.toLowerCase()}`
}

function RuleList({ rules }) {
  if (!rules?.length) return <span className="muted">No rule detail recorded</span>
  return (
    <ul className="rule-list">
      {rules.map((rule) => <li key={`${rule.id}-${rule.reason}`}><strong>{rule.id}</strong> {rule.reason}</li>)}
    </ul>
  )
}

export default function DoctorDashboard({ queue, onRefresh, onAdvanceClock }) {
  const [busyId, setBusyId] = useState(null)
  const [clockBusy, setClockBusy] = useState(false)
  const [message, setMessage] = useState(null)
  const [expandedId, setExpandedId] = useState(null)
  const [assignmentDrafts, setAssignmentDrafts] = useState({})

  const counts = useMemo(() => queue.reduce((result, row) => {
    result[row.display_level] = (result[row.display_level] || 0) + 1
    return result
  }, { U1: 0, U2: 0, U3: 0, U4: 0, U5: 0 }), [queue])

  async function handleDeterioration(id) {
    setBusyId(id)
    setMessage(null)
    try {
      await recordDeterioration(id, crypto.randomUUID())
      await onRefresh()
      setMessage({ type: 'success', text: 'Deterioration recorded and queue priority updated.' })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setBusyId(null)
    }
  }

  async function handleClockAdvance(minutes) {
    setClockBusy(true)
    setMessage(null)
    try {
      await onAdvanceClock(minutes)
      setMessage({ type: 'success', text: `Demo clock advanced by ${minutes} minutes.` })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setClockBusy(false)
    }
  }

  function updateAssignment(id, defaultRole, field, value) {
    setAssignmentDrafts((current) => ({
      ...current,
      [id]: { role: current[id]?.role || defaultRole, assignee: current[id]?.assignee || '', [field]: value },
    }))
  }

  async function handleAssignment(id) {
    const draft = assignmentDrafts[id] || { role: 'nurse', assignee: '' }
    setBusyId(id)
    setMessage(null)
    try {
      await assignResponder(id, draft)
      await onRefresh()
      setMessage({ type: 'success', text: 'Responder assigned. The handoff is shown below for the response team.' })
    } catch (error) {
      setMessage({ type: 'error', text: error.fieldErrors?.assignee || error.fieldErrors?.role || error.message })
    } finally {
      setBusyId(null)
    }
  }

  const assignedCases = queue.filter((row) => row.assignment?.role)

  return (
    <section className="doctor-dashboard" aria-labelledby="doctor-dashboard-title">
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">Clinical worklist</p>
          <h2 id="doctor-dashboard-title">Doctor priority dashboard</h2>
          <p className="dashboard-description">Ordered by the server-calculated provisional urgency, then arrival time. This is a synthetic prototype—not a clinical decision.</p>
        </div>
        <div className="clock-controls" aria-label="Demo clock controls">
          <button type="button" className="button-secondary" onClick={onRefresh}>Refresh queue</button>
          <button type="button" className="button-secondary" onClick={() => handleClockAdvance(15)} disabled={clockBusy}>+15 min</button>
          <button type="button" className="button-secondary" onClick={() => handleClockAdvance(60)} disabled={clockBusy}>+60 min</button>
        </div>
      </div>

      <div className="severity-summary" aria-label="Waiting patients by urgency">
        {Object.keys(LEVEL_COPY).map((level) => (
          <div className={levelClass(level)} key={level}>
            <span>{level}</span><strong>{counts[level]}</strong><small>{LEVEL_COPY[level].label}</small>
          </div>
        ))}
      </div>

      {message && <p className={`notice notice-${message.type}`} role="status">{message.text}</p>}

      <section className="response-board" aria-labelledby="response-board-title">
        <div>
          <p className="eyebrow">Handover board</p>
          <h3 id="response-board-title">Nurse and trainee assignments</h3>
        </div>
        {assignedCases.length === 0 ? (
          <p className="muted">No responder handoffs yet. A doctor can assign a waiting case below when immediate support is needed.</p>
        ) : (
          <div className="response-list">
            {assignedCases.map((row) => (
              <div className="response-item" key={row.id}>
                <UrgencyChip level={row.display_level} />
                <strong>{row.patient.reference} · {row.patient.full_name || 'Unnamed patient'}</strong>
                <span>Assigned to {row.assignment.role}: <strong>{row.assignment.assignee}</strong></span>
              </div>
            ))}
          </div>
        )}
      </section>

      {queue.length === 0 ? (
        <div className="dashboard-empty">
          <h3>No patients waiting</h3>
          <p>Register a synthetic patient and complete an assessment to add a case to this worklist.</p>
        </div>
      ) : (
        <div className="case-list">
          {queue.map((row, index) => {
            const isExpanded = expandedId === row.id
            const level = LEVEL_COPY[row.display_level] || LEVEL_COPY.U3
            return (
              <article className={`case-card ${row.display_level === 'U1' || row.display_level === 'U2' ? 'case-card-priority' : ''}`} key={row.id}>
                <div className="case-rank" aria-label={`Queue position ${index + 1}`}>{index + 1}</div>
                <div className="case-main">
                  <div className="case-title-row">
                    <div>
                      <p className="patient-reference">{row.patient.reference}</p>
                      <h3>{row.patient.full_name || 'Unnamed patient'}</h3>
                    </div>
                    <UrgencyChip level={row.display_level} />
                  </div>
                  <p className="case-complaint">{row.complaint || 'No presenting complaint recorded.'}</p>
                  <div className="case-meta">
                    <span><strong>Age:</strong> {row.patient.age} years</span>
                    <span><strong>Sex:</strong> {row.patient.sex}</span>
                    <span><strong>Wait:</strong> {row.wait_minutes} min</span>
                    <span><strong>Action:</strong> {level.action}</span>
                    {(row.patient.age < 16 || row.patient.age >= 65) && <span className="aged-note">Age review</span>}
                    {row.aged_from && <span className="aged-note">Aged from {row.aged_from}</span>}
                    {row.needs_reassessment && <span className="reassess-note">Reassess due</span>}
                  </div>
                  {isExpanded && <div className="case-rules"><h4>Calculation explanation</h4><RuleList rules={row.fired_rules} /></div>}
                </div>
                <div className="case-actions">
                  <button type="button" className="button-link" onClick={() => setExpandedId(isExpanded ? null : row.id)} aria-expanded={isExpanded}>
                    {isExpanded ? 'Hide details' : 'Why this priority?'}
                  </button>
                  <button type="button" className="button-danger" onClick={() => handleDeterioration(row.id)} disabled={busyId === row.id || row.display_level === 'U1'}>
                    {busyId === row.id ? 'Updating…' : row.display_level === 'U1' ? 'Maximum urgency' : 'Record deterioration'}
                  </button>
                  {['U1', 'U2'].includes(row.display_level) ? (
                    <div className="assignment-controls">
                      <label htmlFor={`role-${row.id}`}>Emergency responder handoff</label>
                      <select id={`role-${row.id}`} value={assignmentDrafts[row.id]?.role || row.assignment?.role || 'nurse'} onChange={(event) => updateAssignment(row.id, row.assignment?.role || 'nurse', 'role', event.target.value)}>
                        <option value="nurse">Nurse</option>
                        <option value="trainee">Trainee</option>
                      </select>
                      <input aria-label={`Responder name for ${row.patient.reference}`} placeholder="Responder name" value={assignmentDrafts[row.id]?.assignee || row.assignment?.assignee || ''} onChange={(event) => updateAssignment(row.id, row.assignment?.role || 'nurse', 'assignee', event.target.value)} />
                      <button type="button" className="button-secondary" onClick={() => handleAssignment(row.id)} disabled={busyId === row.id}>
                        {row.assignment?.role ? 'Reassign' : 'Assign'}
                      </button>
                    </div>
                  ) : <p className="assignment-unavailable">Emergency handoff is available for U1/U2 cases.</p>}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
