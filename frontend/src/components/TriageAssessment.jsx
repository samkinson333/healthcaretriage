import { useState } from 'react'
import { createAssessment } from '../services/api'

const OBSERVATION_FIELDS = [
  { name: 'respiratory_rate', label: 'Respiratory rate', unit: 'bpm', min: '0', max: '60' },
  { name: 'spo2', label: 'SpO2', unit: '%', min: '0', max: '100' },
  { name: 'temperature_c', label: 'Temperature', unit: '°C', min: '30', max: '45', step: '0.1' },
  { name: 'systolic_bp', label: 'Systolic BP', unit: 'mmHg', min: '0', max: '300' },
  { name: 'pulse', label: 'Pulse', unit: 'bpm', min: '0', max: '300' },
  { name: 'consciousness', label: 'Consciousness', unit: 'AVPU' },
]

export default function TriageAssessment({ patient, onCreated }) {
  const [values, setValues] = useState({
    age: patient?.age || '',
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

  function update(field, value) {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  function updateObs(field, value, source = 'manual') {
    setValues((prev) => ({
      ...prev,
      observations: { ...prev.observations, [field]: { value, source } },
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setMessage(null)
    setResult(null)

    try {
      const assessment = await createAssessment(patient.id, values)
      setResult(assessment)
      onCreated(assessment)
      setMessage({ type: 'success', text: 'Assessment completed.' })
    } catch (error) {
      setErrors(error.fieldErrors || {})
      setMessage({ type: 'error', text: error.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <h2>Triage assessment {patient && `— ${patient.reference}`}</h2>
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="complaint">Complaint</label>
          <input
            id="complaint"
            value={values.complaint}
            onChange={(e) => update('complaint', e.target.value)}
          />
        </div>
        {/* ... more fields ... */}
        <button type="submit" disabled={busy}>Submit assessment</button>
      </form>
      {result && (
        <div className="result">
          <h3>Recommendation: {result.recommendation}</h3>
          ...
        </div>
      )}
      {message && <p className={`notice notice-${message.type}`}>{message.text}</p>}
    </section>
  )
}
