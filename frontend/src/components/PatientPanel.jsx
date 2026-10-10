import { useEffect, useRef, useState } from 'react'
import { registerPatient } from '../services/api'

const SEX_OPTIONS = [
  { value: 'female', label: 'F' },
  { value: 'male', label: 'M' },
  { value: 'other', label: 'Other' },
]

const EMPTY_FORM = { full_name: '', age: '', sex: 'other' }

export default function PatientPanel({ patients, selectedId, onSelect, onRegistered, queueCount = 0 }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [sessionCount, setSessionCount] = useState(0)
  const ageRef = useRef(null)

  useEffect(() => {
    ageRef.current?.focus()
  }, [])

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setErrors({})
    setMessage(null)
    try {
      const patient = await registerPatient({
        full_name: form.full_name,
        age: form.age,
        sex: form.sex,
      })
      onRegistered(patient)
      setForm(EMPTY_FORM)
      setSessionCount((count) => count + 1)
      setMessage({ type: 'success', text: `Added ${patient.reference}. Ready for the next patient.` })
      ageRef.current?.focus()
    } catch (error) {
      setErrors(error.fieldErrors || {})
      setMessage({ type: 'error', text: error.message })
    } finally {
      setBusy(false)
    }
  }

  const busyQueue = queueCount >= 8

  return (
    <section className="card">
      <div className="panel-heading">
        <h2>Patient</h2>
        {sessionCount > 0 && <span className="muted count-pill">{sessionCount} added this session</span>}
      </div>

      {busyQueue && (
        <p className="notice notice-warning" role="status">
          {queueCount} patients waiting — high intake. Use quick entry and keep each patient brief.
        </p>
      )}

      <form className="quick-add" onSubmit={handleSubmit} noValidate>
        <h3>Quick add</h3>
        <p className="hint">
          Age is the only required field. Type the age and press <kbd>Enter</kbd> to add and move on.
        </p>
        <div className="quick-add-row">
          <div className="field field-age">
            <label htmlFor="quick-age">Age <span className="req" aria-hidden="true">*</span></label>
            <input
              ref={ageRef}
              id="quick-age"
              name="age"
              type="number"
              inputMode="numeric"
              min="0"
              max="120"
              value={form.age}
              onChange={(event) => update('age', event.target.value)}
              placeholder="42"
              required
              aria-required="true"
              aria-invalid={Boolean(errors.age)}
            />
            {errors.age && <p className="error">{errors.age}</p>}
          </div>

          <div className="field field-name">
            <label htmlFor="quick-name">Name <span className="opt">(optional)</span></label>
            <input
              id="quick-name"
              name="full_name"
              type="text"
              value={form.full_name}
              onChange={(event) => update('full_name', event.target.value)}
              placeholder="Patient name"
              aria-invalid={Boolean(errors.full_name)}
            />
            {errors.full_name && <p className="error">{errors.full_name}</p>}
          </div>

          <fieldset className="field field-sex">
            <legend>Sex</legend>
            <div className="segmented">
              {SEX_OPTIONS.map((option) => (
                <label key={option.value} className={form.sex === option.value ? 'seg is-active' : 'seg'}>
                  <input
                    type="radio"
                    name="sex"
                    value={option.value}
                    checked={form.sex === option.value}
                    onChange={() => update('sex', option.value)}
                  />
                  {option.label}
                </label>
              ))}
            </div>
            {errors.sex && <p className="error">{errors.sex}</p>}
          </fieldset>

          <button type="submit" className="btn" disabled={busy}>
            {busy ? 'Adding…' : 'Add patient'}
          </button>
        </div>
        {message && <p className={`notice notice-${message.type}`} role="status">{message.text}</p>}
      </form>

      <div className="field select-existing">
        <label htmlFor="patient-select">Associate vitals with a registered patient</label>
        <select
          id="patient-select"
          value={selectedId ?? ''}
          onChange={(event) => onSelect(event.target.value ? Number(event.target.value) : null)}
        >
          <option value="">Select a patient…</option>
          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.reference} — {patient.full_name || 'Unnamed'} ({patient.age})
            </option>
          ))}
        </select>
        {patients.length === 0 && <p className="hint">No patients yet. Add one above.</p>}
      </div>
    </section>
  )
}
