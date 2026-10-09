const BASE = '/api/v1'

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new Error('Could not reach the server. Is the Django backend running?')
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const error = new Error(data.detail || 'Request failed.')
    error.fieldErrors = data.errors || {}
    error.status = response.status
    throw error
  }

  return data
}

export function listPatients() {
  return request('/patients/')
}

export function registerPatient(payload) {
  return request('/patients/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getPatientVitals(patientId) {
  return request(`/patients/${patientId}/vitals/`)
}

export function submitVitals(patientId, payload) {
  return request(`/patients/${patientId}/vitals/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
