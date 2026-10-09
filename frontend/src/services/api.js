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

export function createAssessment(patientId, payload) {
  return request(`/patients/${patientId}/assessments/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getAssessment(assessmentId) {
  return request(`/assessments/${assessmentId}/`)
}

export function getQueue() {
  return request('/queue/')
}

export function advanceDemoClock(minutes) {
  return request('/demo/clock/', {
    method: 'POST',
    body: JSON.stringify({ minutes }),
  })
}

export function recordDeterioration(assessmentId, requestId) {
  return request(`/assessments/${assessmentId}/deterioration/`, {
    method: 'POST',
    body: JSON.stringify({ request_id: requestId }),
  })
}
