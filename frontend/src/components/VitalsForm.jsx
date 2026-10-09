import { useState } from 'react'
import { submitVitals } from '../services/api'
import { VITAL_FIELDS, emptyVitals, validateVitals } from '../services/vitals'

export default function VitalsForm({ patient, onSubmitted }) {
  const [values, setValues] = useState(emptyVitals)
  const [errors, setErrors] = useState({})
  const [source, setSource] = useState('manual')
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)

  const disabled = !patient

  function update(field, value) {
    setValues((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  function handleBlur(field) {
    const { errors: nextErrors } = validateVitals(values)
    setErrors((prev) => ({ ...prev, [field]: nextErrors[field] }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (disabled) {
      setMessage({ type: 'error', text: 'Select or register a patient first.' })
      return
    }

    const { errors: nextErrors, cleaned } = validateVitals(values)
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      setMessage({ type: 'error', text: 'Fix the highlighted measurements before saving.' })
      return
    }

    setBusy(true)
    setMessage(null)
    try {
      const measurement = await submitVitals(patient.id, { ...cleaned, source })
      onSubmitted(measurement)
      setValues(emptyVitals())
      setErrors({})
      setMessage({ type: 'success', text: 'Measurements saved.' })
    } catch (error) {
      setErrors(error.fieldErrors || {})
      setMessage({ type: 'error', text: error.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <h2>Vital signs</h2>
      <p className="hint">
        {patient
          ? `Recording for ${patient.reference} — ${patient.full_name || 'Unnamed'} (${patient.age} yrs).`
          : 'Select or register a patient to record vitals.'}
      </p>

      <form onSubmit={handleSubmit} noValidate>
        <div className="grid">
          {VITAL_FIELDS.map((field) => (
            <div className="field" key={field.name}>
              <label htmlFor={field.name}>
                {field.label} <span className="unit">({field.unit})</span>
              </label>
              <input
                id={field.name}
                name={field.name}
                type="number"
                inputMode="decimal"
                min={field.min}
                max={field.max}
                step={field.step}
                placeholder={field.placeholder}
                value={values[field.name]}
                onChange={(event) => update(field.name, event.target.value)}
                onBlur={() => handleBlur(field.name)}
                aria-invalid={Boolean(errors[field.name])}
                disabled={disabled}
              />
              {errors[field.name] && <p className="error">{errors[field.name]}</p>}
            </div>
          ))}

          <div className="field">
            <label htmlFor="source">Source</label>
            <select
              id="source"
              value={source}
              onChange={(event) => setSource(event.target.value)}
              disabled={disabled}
            >
              <option value="manual">Manual entry</option>
              <option value="device">Device (simulated)</option>
            </select>
          </div>
        </div>

        <button type="submit" className="btn" disabled={disabled || busy}>
          {busy ? 'Saving…' : 'Save measurements'}
        </button>
        {message && <p className={`notice notice-${message.type}`}>{message.text}</p>}
      </form>
    </section>
  )
}
