export const VITAL_FIELDS = [
  { name: 'systolic_bp', label: 'Systolic BP', unit: 'mmHg', min: 50, max: 300, step: 1, placeholder: '120' },
  { name: 'diastolic_bp', label: 'Diastolic BP', unit: 'mmHg', min: 20, max: 200, step: 1, placeholder: '80' },
  { name: 'pulse', label: 'Pulse', unit: 'bpm', min: 20, max: 250, step: 1, placeholder: '72' },
  { name: 'temperature_c', label: 'Temperature', unit: '°C', min: 25, max: 45, step: 0.1, placeholder: '36.8' },
  { name: 'spo2', label: 'SpO₂', unit: '%', min: 50, max: 100, step: 1, placeholder: '98' },
]

const INT_FIELDS = new Set(['systolic_bp', 'diastolic_bp', 'pulse', 'spo2'])

export function emptyVitals() {
  return VITAL_FIELDS.reduce((acc, field) => {
    acc[field.name] = ''
    return acc
  }, {})
}

export function validateVitals(values) {
  const errors = {}
  const cleaned = {}

  for (const field of VITAL_FIELDS) {
    const raw = String(values[field.name] ?? '').trim()
    if (raw === '') {
      errors[field.name] = 'This measurement is required.'
      continue
    }
    const value = INT_FIELDS.has(field.name) ? Number.parseInt(raw, 10) : Number.parseFloat(raw)
    if (Number.isNaN(value)) {
      errors[field.name] = 'Enter a valid number.'
      continue
    }
    if (value < field.min || value > field.max) {
      errors[field.name] = `Value must be between ${field.min} and ${field.max}.`
      continue
    }
    cleaned[field.name] = value
  }

  const systolic = cleaned.systolic_bp
  const diastolic = cleaned.diastolic_bp
  if (systolic !== undefined && diastolic !== undefined && systolic <= diastolic) {
    errors.systolic_bp = 'Systolic pressure must be higher than diastolic.'
  }

  return { errors, cleaned }
}

function classify(value, bands) {
  for (const band of bands) {
    if (band.test(value)) {
      return { label: band.label, tone: band.tone }
    }
  }
  return { label: 'Unknown', tone: 'normal' }
}

export function summarizeVitals(vital) {
  if (!vital) return []

  const { systolic_bp: sys, diastolic_bp: dia, pulse, temperature_c: temp, spo2 } = vital

  const bp = classify(sys, [
    { test: (v) => v >= 180 || dia >= 120, label: 'Hypertensive crisis', tone: 'high' },
    { test: (v) => v >= 140 || dia >= 90, label: 'High', tone: 'high' },
    { test: (v) => v >= 130 || dia >= 80, label: 'Elevated', tone: 'warning' },
    { test: (v) => v < 90 || dia < 60, label: 'Low', tone: 'warning' },
    { test: () => true, label: 'Normal', tone: 'normal' },
  ])

  const pulseBand = classify(pulse, [
    { test: (v) => v < 60, label: 'Low', tone: 'warning' },
    { test: (v) => v > 100, label: 'High', tone: 'warning' },
    { test: () => true, label: 'Normal', tone: 'normal' },
  ])

  const tempBand = classify(temp, [
    { test: (v) => v >= 40, label: 'High fever', tone: 'high' },
    { test: (v) => v >= 38, label: 'Fever', tone: 'warning' },
    { test: (v) => v < 35, label: 'Low', tone: 'warning' },
    { test: () => true, label: 'Normal', tone: 'normal' },
  ])

  const spo2Band = classify(spo2, [
    { test: (v) => v < 90, label: 'Critically low', tone: 'high' },
    { test: (v) => v < 95, label: 'Low', tone: 'warning' },
    { test: () => true, label: 'Normal', tone: 'normal' },
  ])

  return [
    { label: 'Blood pressure', value: `${sys}/${dia} mmHg`, band: bp },
    { label: 'Pulse', value: `${pulse} bpm`, band: pulseBand },
    { label: 'Temperature', value: `${temp} °C`, band: tempBand },
    { label: 'SpO₂', value: `${spo2}%`, band: spo2Band },
  ]
}
