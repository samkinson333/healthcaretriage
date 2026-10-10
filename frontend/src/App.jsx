import { useCallback, useEffect, useState } from 'react'
import PatientPanel from './components/PatientPanel'
import VitalsForm from './components/VitalsForm'
import VitalsSummary from './components/VitalsSummary'
import TriageAssessment from './components/TriageAssessment'
import DoctorDashboard from './components/DoctorDashboard'
import NurseWorklist from './components/NurseWorklist'
import { getPatientVitals, listPatients, getQueue, advanceDemoClock } from './services/api'
import { Activity, ClipboardList, Stethoscope, LayoutDashboard } from 'lucide-react'

export default function App() {
  const [patients, setPatients] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [measurements, setMeasurements] = useState([])
  const [queue, setQueue] = useState([])
  const [error, setError] = useState(null)
  
  // Navigation State
  const [activeTab, setActiveTab] = useState('queue')

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
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <aside className="app-sidebar">
        <div className="brand-logo">
          <Activity size={28} />
          <h2>SmartTriage AI</h2>
        </div>
        
        <nav className="nav-menu">
          <button 
            className={`nav-item ${activeTab === 'queue' ? 'active' : ''}`}
            onClick={() => setActiveTab('queue')}
          >
            <LayoutDashboard size={20} />
            Doctor Dashboard
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'intake' ? 'active' : ''}`}
            onClick={() => setActiveTab('intake')}
          >
            <ClipboardList size={20} />
            Patient Intake
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'nurse' ? 'active' : ''}`}
            onClick={() => setActiveTab('nurse')}
          >
            <Stethoscope size={20} />
            Nurse Worklist
          </button>
        </nav>
        
        <div className="demo-tag">
          Synthetic Demo Data
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="app-main-wrapper">
        <header className="app-topbar">
          <div>
            <h1>{activeTab === 'queue' ? 'Clinical Worklist' : activeTab === 'intake' ? 'Patient Intake & Vitals' : 'Assigned Emergency Handoffs'}</h1>
            <p>Healthcare Triage System — Professional Grade</p>
          </div>
          <div className="topbar-actions">
             {/* We can put global actions here later */}
          </div>
        </header>

        <main className="app-main-content">
          {error && <p className="notice notice-error">{error}</p>}

          {activeTab === 'nurse' && (
            <NurseWorklist queue={queue} onClose={() => setActiveTab('queue')} />
          )}

          {activeTab === 'intake' && (
            <div className="layout">
<PatientPanel
            patients={patients}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onRegistered={handleRegistered}
            queueCount={queue.length}
          />
              <VitalsForm patient={selectedPatient} onSubmitted={handleSubmitted} />
              <VitalsSummary patient={selectedPatient} measurements={measurements} />
              <TriageAssessment patient={selectedPatient} onCreated={() => {
                refreshQueue()
                setActiveTab('queue')
              }} />
            </div>
          )}

          {activeTab === 'queue' && (
            <DoctorDashboard
              queue={queue}
              onRefresh={refreshQueue}
              onAdvanceClock={async (minutes) => {
                await advanceDemoClock(minutes)
                await refreshQueue()
              }}
            />
          )}
        </main>
      </div>
    </div>
  )
}
