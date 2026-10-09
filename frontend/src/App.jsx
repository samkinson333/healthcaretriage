import { useCallback, useEffect, useState } from 'react'
import PatientPanel from './components/PatientPanel'
import VitalsForm from './components/VitalsForm'
import VitalsSummary from './components/VitalsSummary'
import TriageAssessment from './components/TriageAssessment'
import PriorityQueue from './components/PriorityQueue'
import { getPatientVitals, listPatients, getQueue, advanceDemoClock } from './services/api'

export default function App() {
  const [patients, setPatients] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [measurements, setMeasurements] = useState([])
  const [queue, setQueue] = useState([])
  const [error, setError] = useState(null)

  const selectedPatient = patients.find((patient) => patient.id === selectedId) || null

  const refreshQueue = useCallback(async () => {
    try {
      const data = await getQueue()
      setQueue(data.queue)
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    listPatients()
      .then((data) => setPatients(data.patients))
      .catch((err) => setError(err.message))
    refreshQueue()
  }, [refreshQueue])

  const loadVitals = useCallback(async (patientId) => {
    if (!patientId) {
      setMeasurements([])
      return
    }
    try {
      const data = await getPatientVitals(patientId)
      setMeasurements(data.measurements)
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    loadVitals(selectedId)
  }, [selectedId, loadVitals])

  function handleRegistered(patient) {
    setPatients((prev) => [patient, ...prev])
    setSelectedId(patient.id)
  }

  function handleSubmitted(measurement) {
    setMeasurements((prev) => [measurement, ...prev])
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Healthcare Triage</h1>
        <p>Patient vitals intake — prototype, synthetic data only.</p>
      </header>

      {error && <p className="notice notice-error">{error}</p>}

      <main className="layout">
        <PatientPanel
          patients={patients}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onRegistered={handleRegistered}
        />
        <VitalsForm patient={selectedPatient} onSubmitted={handleSubmitted} />
        <VitalsSummary patient={selectedPatient} measurements={measurements} />
        <TriageAssessment patient={selectedPatient} onCreated={refreshQueue} />
        <PriorityQueue queue={queue} onRefresh={refreshQueue} onAdvanceClock={async (m) => { await advanceDemoClock(m); refreshQueue(); }} />
      </main>
    </div>
  )
}
