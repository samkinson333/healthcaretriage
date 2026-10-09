import { useState } from 'react'
import { registerPatient } from '../services/api'

const SEX_OPTIONS = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'other', label: 'Other' },
]

export default function PatientPanel({ patients, selectedId, onSelect, onRegistered }) {
  const [form, setForm] = useState({ full_name: '', age: '', sex: 'other' })
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
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
      setForm({ full_name: '', age: '', sex: 'other' })
      setMessage({ type: 'success', text: `Registered ${patient.reference}.` })
    } catch (error) {
      setErrors(error.fieldErrors || {})
      setMessage({ type: 'error', text: error.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <h2>Patient</h2>

      <div className="field">
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
        {patients.length === 0 && <p className="hint">No patients yet. Register one below.</p>}
      </div>

      <form className="subform" onSubmit={handleSubmit} noValidate>
        <h3>Register new patient</h3>
        <div className="grid">
          <div className="field">
            <label htmlFor="full_name">Full name</label>
            <input
              id="full_name"
              type="text"
              value={form.full_name}
              onChange={(event) => update('full_name', event.target.value)}
              placeholder="Optional"
            />
            {errors.full_name && <p className="error">{errors.full_name}</p>}
          </div>

          <div className="field">
            <label htmlFor="age">Age (years)</label>
            <input
              id="age"
              type="number"
              min="0"
              max="120"
              value={form.age}
              onChange={(event) => update('age', event.target.value)}
              placeholder="e.g. 42"
              required
            />
            {errors.age && <p className="error">{errors.age}</p>}
          </div>

          <div className="field">
            <label htmlFor="sex">Sex</label>
            <select id="sex" value={form.sex} onChange={(event) => update('sex', event.target.value)}>
              {SEX_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.sex && <p className="error">{errors.sex}</p>}
          </div>
        </div>

        <button type="submit" className="btn btn-secondary" disabled={busy}>
          {busy ? 'Registering…' : 'Register patient'}
        </button>
        {message && <p className={`notice notice-${message.type}`}>{message.text}</p>}
      </form>
    </section>
  )
}
