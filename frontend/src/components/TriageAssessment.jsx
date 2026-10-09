import { useState, useEffect } from 'react'
import { createAssessment } from '../services/api'

const OBSERVATION_FIELDS = [
  { name: 'respiratory_rate', label: 'Respiratory rate', unit: 'bpm', type: 'number' },
  { name: 'spo2', label: 'SpO2', unit: '%', type: 'number' },
  { name: 'supplemental_oxygen', label: 'Supplemental O₂', type: 'checkbox' },
  { name: 'temperature_c', label: 'Temperature', unit: '°C', type: 'number', step: '0.1' },
  { name: 'systolic_bp', label: 'Systolic BP', unit: 'mmHg', type: 'number' },
  { name: 'pulse', label: 'Pulse', unit: 'bpm', type: 'number' },
  { name: 'consciousness', label: 'Consciousness', unit: 'AVPU', type: 'select', options: ['alert', 'confusion', 'voice', 'pain', 'unresponsive'] },
]

export default function TriageAssessment({ patient, onCreated }) {
  const [values, setValues] = useState({
    pregnant: false,
    complaint: '',
    observations: {},
    symptoms: [],
    nurse_concern: false,
  })
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)

  // Initialize observations object on mount
  useEffect(() => {
    const initialObs = {}
    OBSERVATION_FIELDS.forEach(f => {
      initialObs[f.name] = { value: null, source: 'manual' }
    })
    setValues(prev => ({ ...prev, observations: initialObs }))
  }, [])

  function update(field, value) {
    setValues(prev => ({ ...prev, [field]: value }))
  }

  function updateObs(field, value, source = 'manual') {
    const finalValue = value === '' || value === null ? null : value
    setValues(prev => ({
      ...prev,
      observations: { ...prev.observations, [field]: { value: finalValue, source } },
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setMessage(null)
    setResult(null)
    setErrors({})

    try {
      const payload = {
        ...values,
        age: patient?.age,
      }
      const assessment = await createAssessment(patient.id, payload)
      setResult(assessment)
      onCreated(assessment)
      setMessage({ type: 'success', text: 'Assessment completed.' })
    } catch (error) {
      setErrors(error.fieldErrors || {})
      setMessage({
        type: 'error',
        text: Object.keys(error.fieldErrors || {}).length ? 'Please fix the errors below.' : error.message
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <h2>Triage Assessment {patient && <small className="hint"> — {patient.reference}</small>}</h2>

      {!patient && <p className="hint">Select a patient to begin assessment.</p>}

      {patient && (
        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="complaint">Presenting complaint</label>
            <input
              id="complaint"
              type="text"
              value={values.complaint}
              onChange={e => update('complaint', e.target.value)}
              placeholder="e.g. Chest pain, difficulty breathing"
              aria-invalid={Boolean(errors.complaint)}
            />
            {errors.complaint && <p className="error">{errors.complaint}</p>}
          </div>

          <div className="grid">
            {OBSERVATION_FIELDS.map(field => (
              <div className="field" key={field.name}>
                <label htmlFor={field.name}>
                  {field.label} <small>({field.unit})</small>
                </label>
                {field.type === 'select' ? (
                  <select
                    id={field.name}
                    value={values.observations[field.name]?.value ?? ''}
                    onChange={e => updateObs(field.name, e.target.value)}
                  >
                    <option value="">--</option>
                    {field.options.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                ) : field.type === 'checkbox' ? (
                  <input
                    id={field.name}
                    type="checkbox"
                    checked={values.observations[field.name]?.value ?? false}
                    onChange={e => updateObs(field.name, e.target.checked)}
                  />
                ) : (
                  <input
                    id={field.name}
                    type="number"
                    step={field.step || '1'}
                    value={values.observations[field.name]?.value ?? ''}
                    onChange={e => updateObs(field.name, e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && e.preventDefault()}
                    aria-invalid={Boolean(errors[`observations.${field.name}`])}
                  />
                )}
                {errors[`observations.${field.name}`] && (
                  <p className="error">{errors[`observations.${field.name}`]}</p>
                )}
              </div>
            ))}
          </div>

          <div className="field" style={{ marginTop: '0.75rem' }}>
            <label>
              <input
                type="checkbox"
                checked={values.nurse_concern}
                onChange={e => update('nurse_concern', e.target.checked)}
              />
              {' '}Nurse Concern
            </label>
          </div>

          <button type="submit" className="btn" disabled={busy || !patient}>
            {busy ? 'Analyzing...' : 'Submit assessment'}
          </button>
        </form>
      )}

      {result && (
        <div className="result subform">
          <h3>Recommendation: <span className={`chip chip-${result.recommendation?.toLowerCase() || 'u3'}`}>{result.recommendation}</span></h3>
          {result.fired_rules?.length > 0 && (
            <p><strong>Rules fired:</strong> {result.fired_rules.map(r => r.id).join(', ')}</p>
          )}
        </div>
      )}
      {message && <p className={`notice notice-${message.type}`}>{message.text}</p>}
    </section>
  )
}