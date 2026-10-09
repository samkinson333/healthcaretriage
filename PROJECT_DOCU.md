# SmartTriage AI

A clinician-supervised emergency-department queue management and decision-support application, extended with an OP registration and health-screening kiosk workflow.

> **Status: research and demonstration prototype.** It uses synthetic data only. It is not a diagnostic tool, is not clinically validated, and must not be used with real patients. Documentation version 1.0, prepared from Project Plan v4, 9 October 2026.

---

## 1. What the project is about

Emergency departments are crowded, and first-come-first-served queues leave urgent patients waiting behind routine ones. SmartTriage AI helps clinical staff:

- collect patient intake information and vital signs,
- flag configured warning signs,
- assign a **provisional urgency level (U1–U5)** with a clear explanation,
- order the waiting queue by urgency, arrival time and waiting-time aging,
- alert staff when a patient has waited too long,
- let clinicians override any recommendation with a recorded reason,
- keep a full audit trail of every decision.

It is a **decision-support** tool. Clinical staff stay responsible for every assessment and decision. It does not diagnose, treat or discharge.

### Core design principles

| Principle | Meaning |
|---|---|
| Safety-first prioritisation | Missing or implausible vital signs are never treated as normal. Automation can escalate urgency but never lower it on its own. |
| Explainable queue ordering | Queue position comes from urgency, arrival time, aging rules and recorded events, not an opaque AI ranking. |
| Clinician oversight | Authorised clinicians can override a recommendation with a mandatory reason. The original recommendation is always preserved. |
| AI-independent safety core | Rules and queue work without any language-model service. AI is optional and cannot bypass the rules. |

### Scope

- Adult emergency-department workflow (age 16 and above).
- Children (under 16) and pregnant patients are directed to **direct clinician assessment**.
- Current prototype: single web page, browser logic, in-memory state, synthetic data.

---

## 2. Intended users

| Role | Responsibility |
|---|---|
| Intake staff / triage nurse | Register patients, record complaints and vitals, review recommendations |
| Doctor / clinician | Review cases, reassess, override, give feedback |
| Queue operator | Monitor waiting patients, waiting times, alerts |
| Administrator | (Future) accounts, roles, configuration |
| Auditor / reviewer | Review assessment history, overrides, feedback, audit events |

Separate logins and server-enforced roles are not built yet.

---

## 3. Features and implementation status

| Feature | Status |
|---|---|
| Rules engine R1–R9 with NEWS2-based scoring, plus clinician override | Built (prototype) |
| Dynamic queue, aging, wait alerts, deterioration action, simulated clock | Built (prototype) |
| Doctor override and feedback (disagreement needs rationale, flagged for second review) | Built (prototype) |
| Queue simulation (FIFO, strict priority, priority + aging) and 10 in-page self-tests | Built (prototype) |
| 30-case synthetic evaluation | Built; clinician relabelling outstanding |
| OP registration and health-screening kiosk workflow | Planned |
| Device adapter layer (simulated device first) | Planned |
| Backend and database (FastAPI, SQLite) | Planned |
| Authentication and server-side authorisation | Planned |
| LLM-assisted structured intake and Malayalam/English support | Planned |

Planned features are never to be presented as working in the UI or the pitch.

---

## 4. How it works

### 4.1 Intake processing sequence

1. **Register patient**: capture complaint, age, available observations.
2. **Validate input**: identify missing or implausible vitals.
3. **Run deterministic rules**: calculate the NEWS2 score and evaluate red flags.
4. **Produce recommendation**: assign a provisional urgency and record fired rules.
5. **Update queue**: rank the patient and evaluate reassessment alerts.

### 4.2 Urgency levels

U1–U5 are project labels, **not ESI levels**.

| Level | Meaning | Intended action |
|---|---|---|
| U1 | Possible immediate life-threatening emergency | Immediate staff alert |
| U2 | Possible time-critical or high-risk condition | High-priority assessment and alert |
| U3 | Concerning presentation needing timely assessment | Prioritise over routine cases |
| U4 | No configured high-risk feature, complete data | Standard queue with reassessment |
| U5 | Potentially lower urgency | Staff assignment only, never automatic |

### 4.3 Rules engine

| Rule | Trigger | Result |
|---|---|---|
| R1 | Unresponsive, airway compromise, active seizure, severe bleeding, anaphylaxis | U1 |
| R2 | Chest pain, stroke signs, severe breathlessness, vomiting blood | At least U2 |
| R3 | NEWS2 total 7 or more | U1 |
| R4 | NEWS2 total 5–6 | At least U2 |
| R5 | Any single NEWS2 parameter scoring 3 | At least U3 |
| R6 | Any required vital missing or implausible | At least U3, never treated as normal |
| R7 | Age below 16 or pregnancy | At least U3, direct clinician assessment |
| R8 | Complete data and no other rule triggered | U4 |
| R9 | Nurse concern flag | Raise urgency by one level |
| R10 | Clinician override | Any level, mandatory reason, original preserved |

R1, R2, R7 and R9 are team-proposed and need clinical review. R3–R5 follow NEWS2 thresholds, with NEWS2 SpO₂ Scale 1 by default and Scale 2 available when staff select the hypercapnic respiratory failure risk pathway. **Open item:** rule precedence, how simultaneous rules combine, R9 interaction with U1/U5, and how an override interacts with later automatic reassessment are not yet specified and need tests.

### 4.4 Queue scheduling

- Higher urgency ranks first; equal urgency is ordered by earlier arrival.
- Waiting U4/U5 patients are promoted one level per 60 minutes, never above U3, and aged patients rank below true U3 patients.
- A deterioration action moves a patient up one level and logs it.
- An assessment already in progress is not interrupted by reordering.
- Aging interval and alert thresholds are assumptions, not hospital protocols.

| Urgency | Wait alert threshold |
|---|---|
| U1 | Immediate |
| U2 | 15 min |
| U3 | 30 min |
| U4 | 60 min |
| U5 | 120 min |

Alerts are prompts to reassess, not safety guarantees. Patient states: Waiting, In consultation, Completed (future: Escalated, Reassessment Required, Cancelled, Left Without Being Seen).

### 4.5 Clinician override and feedback

- **Override:** open assessment, review rule triggers, choose the new level, enter a mandatory reason, save. Original recommendation is kept and the decision is logged as a separate event.
- **Feedback options:** Appropriate, Too urgent, Not urgent enough, Unable to judge. Disagreement requires a rationale and is flagged for second review. Feedback never changes live rules automatically.

### 4.6 OP registration and health-screening kiosk (planned)

Proposed journey: OP registration and ticket, visit linking, screening (BP, SpO₂, pulse, temperature; glucose only with a validated device), data validation with provenance, symptom intake, rules engine, clinician review, audit.

```
Kiosk / device -> Vendor SDK or API -> Device adapter -> Validation and normalisation
   -> OP visit record -> Assessment service -> Rules engine and queue
```

Each adapter normalises units without inventing values, records timestamps and source, handles timeouts and duplicates, keeps device and manual data separate, and never bypasses the rules. No physical kiosk, vendor API or hospital system is confirmed. One sensor does not measure everything: BP needs a cuff, SpO₂/pulse an optical sensor, temperature a thermometer, glucose a glucose device. Use clearly labelled simulated readings until a device is tested end to end.

---

## 5. Technology stack

### Current prototype
- Single web page, application logic in the browser
- In-memory state (resets on refresh)
- Browser-side rules engine, queue scheduler, simulation, feedback, in-page tests

### Planned backend (from the project plan)
| Layer | Technology |
|---|---|
| API | Python, FastAPI |
| Persistence | SQLite (reassess if multiple writers, high availability or hospital integration is needed) |
| Safety core | Deterministic rules engine and queue engine, independent of AI |
| Testing | pytest |
| Optional | LLM structured extraction and speech services (untrusted output, schema validated, staff confirmed, manual fallback) |

### Hackathon frontend (24-hour build, no real backend)
Suggested default, adjust to the repository: React + Vite + TypeScript, Tailwind with CSS variables for design tokens, Zustand or Context for in-memory state, lucide-react icons. Data sits behind a mock service (`services/triage`) so a real API can replace it later. Design rules (flat colours, no gradients, urgency by colour plus shape plus text, Atkinson Hyperlegible typeface) live in `.agent/skills`.

---

## 6. Architecture

```
Web interface:  Intake | Queue | Clinician review | Audit
        |
FastAPI layer:  Authentication | Validation | Endpoints | Authorisation      (planned)
        |
Safety core:    Rules engine (scoring, escalation) | Queue engine (ordering, alerts)
        |
SQLite layer:   Patients | Assessments | Overrides | Reviews | Queue events | Audit events   (planned)

Optional AI / speech: untrusted extraction -> schema validation -> staff confirmation -> manual fallback   (planned)
```

Browser-side logic is not a security boundary, which is why server-side validation and permissions are planned.

---

## 7. Planned API (proposed, not built)

Base path `/api/v1`, JSON, ISO 8601 timestamps, opaque IDs, server-enforced authorisation.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /auth/login, /auth/logout | Session handling |
| GET, POST | /patients | List or register patients |
| GET | /patients/{id} | Patient record |
| POST | /patients/{id}/assessments | Submit intake, get recommendation |
| GET | /assessments/{id} | Assessment and fired rules |
| POST | /assessments/{id}/reassessments | New observations, re-evaluate |
| GET | /queue | Ordered waiting queue |
| POST | /queue/{id}/deterioration | Record deterioration |
| POST | /assessments/{id}/overrides | Clinician override |
| POST | /assessments/{id}/feedback | Clinician feedback |
| GET | /audit-events | Audit events |
| GET | /health | Service health |

Errors must never imply a patient is low risk because a request or optional service failed.

### Proposed data entities
users, patients, assessments, assessment_rules, overrides, feedback, queue_events, audit_events, rule_versions, plus for the kiosk: op_visits, screening_sessions, vital_measurements, device_events.

---

## 8. Security and privacy

| Control | Status |
|---|---|
| Escalate-only logic | Built |
| Original recommendation preserved on override | Built |
| Audit log (assessments, overrides, clock changes) | Built |
| Basic English injection-phrase flagging | Built, limited |
| Password hashing (Argon2/bcrypt), server-side RBAC, rate limiting, session expiry, server-side validation | Planned |
| Hash-chained audit log, TLS, encrypted backups | Future work |

Real-patient use would require assessing India's Digital Personal Data Protection Act, possible medical-device software obligations, hospital approval, retention policy and protected backups.

### AI safety stance
The LLM may extract candidate fields and suggest questions only. It must not diagnose, invent vitals, override rules or lower urgency. Patient text is untrusted. Malayalam/English intake is planned and untested.

---

## 9. Validation results (recorded in Project Plan v4)

### Self-tests
10 of 10 in-page tests passed on 9 October 2026 (software checks only; re-run before quoting as fresh).

### 30-case synthetic evaluation
Expected labels were written by the team, not independently reviewed.

| Metric | Result |
|---|---|
| Exact-level agreement | 27/30 |
| Emergency sensitivity | 12/13 |
| Expected U1 predicted U1 | 6/6 |
| Under-triaged / over-triaged | 3 / 0 |

Under-triaged cases: SpO₂ 91% with otherwise normal vitals (engine U3, expected U2); fever 39.3°C with HR 100 (engine U4, expected U3); frail 80-year-old with NEWS2 total 4 (engine U4, expected U3). Agreement is not clinical accuracy.

### Queue simulation
30 synthetic patients, one clinician, non-preemptive, 1,000 seeds. Mean waits in minutes, simulated.

| Overloaded (9 min gap) | FIFO | Strict | Priority + aging |
|---|---|---|---|
| U1+U2 mean wait | 142.1 | 27.6 | 27.7 |
| All-patient mean wait | 144.1 | 177.1 | 174.5 |
| U4 mean wait | 145.3 | 269.7 | 283.0 |
| Worst U4/U5 wait | 278.6 | 447.3 | 358.0 |

| Moderate (20 min gap) | FIFO | Strict | Priority + aging |
|---|---|---|---|
| U1+U2 mean wait | 37.9 | 12.6 | 12.6 |
| All-patient mean wait | 39.2 | 48.0 | 47.2 |
| U4 mean wait | 40.1 | 70.0 | 74.6 |
| Worst U4/U5 wait | 91.8 | 218.3 | 178.3 |

Takeaway: urgent patients wait far less, lower-urgency patients wait longer, and aging trims the worst waits but not the U4 mean. This shows scheduler behaviour, not clinical outcomes.

---

## 10. Hackathon demonstration flow

1. Register a demo patient and create an OP ticket.
2. Link a screening session to the visit.
3. Enter or simulate vital signs.
4. Enter the complaint and confirm intake data.
5. Run the deterministic assessment; show fired rules and explanation.
6. Place the patient in the queue; show wait-time and aging alerts.
7. Record a clinician reassessment or override with a mandatory reason.
8. Open the audit view and trace the original recommendation and later events.
9. Show a device or API failure and the safe manual fallback.
10. Explain which results are software tests, synthetic evaluation, simulation, or independently reviewed clinical evidence.

All sample patients and measurements must be labelled synthetic.

---

## 11. Known limitations

- Rules are unvalidated and not yet clinically reviewed.
- Short red-flag list; trauma, poisoning, snakebite, self-harm and diabetic emergencies are not covered.
- NEWS2 has no frailty adjustment; SpO₂ Scale 2 is supported only when staff explicitly select the hypercapnic respiratory failure risk pathway.
- Children and pregnant patients are outside the supported workflow.
- Simulation is synthetic with one clinician; priority scheduling lengthens some lower-urgency waits.
- Browser state resets on refresh; no real login or persistence.
- LLM extraction and Malayalam accuracy are untested.
- No real hospital, kiosk or ABDM integration and no outcome evidence.

---

## 12. Roadmap and priorities

1. **Triage rules and evidence:** regression tests for the three under-triage cases, define rule precedence, re-run tests and evaluation, obtain clinician review and independent labels.
2. **Persistent backend and security:** FastAPI, SQLite with migrations, validated schemas, authentication, server-side roles, rate limiting, persistence of all events.
3. **OP registration and kiosk:** visit IDs, device adapter interface, simulated adapter first, vendor adapters only after device details are confirmed.
4. **End-to-end demo:** full journey including device failure and clear implemented / simulated / planned labelling.
5. **Optional AI and language support:** schema-validated, staff-confirmed extraction; Malayalam/English phrase testing (20–30 phrases reviewed by a native speaker).

Cut order if time is short: language support first.

### Readiness checklist (0/23 complete)
- **Clinical:** documented clinician review; verify NEWS2 bands; define rule precedence; independent labelling of 30 cases; rerun evaluation.
- **Backend:** endpoints and validation; SQLite schema and migrations; hashing and auth; server-side roles; rate limiting and session expiry; persisted assessments, overrides and audit.
- **Testing:** re-run 10 self-tests; boundary and aging tests (59, 60, 119, 120 minutes); persistence and recovery; unauthorised access; AI-failure fallback; performance under stated load.
- **Release docs:** verify simulation values; separate implemented from planned; record clinical review status; document privacy and regulatory limits; demo and backup recording; review all claims.

---

## 13. Suggested repository layout

```
.
├── README.md
├── .agent/                    # AI agent rules, skills and workflows (frontend UI design)
│   ├── rules/frontend-rules.md
│   ├── skills/                # design system, screens, demo flow, honest labels, pitfalls
│   └── workflows/             # /build-ui-24h, /ui-review
├── src/                       # frontend app
│   ├── components/            # UrgencyChip, RuleChip, WaitTimer, SourceTag, StatusBadge ...
│   ├── screens/               # Queue board, Intake/screening, Review drawer, Audit, Roadmap
│   ├── services/triage.*      # mock rules engine, queue and audit (swap for API later)
│   └── store/                 # in-memory state, simulated clock
└── PROJECT_HISTORY.md         # task log (gitignored)
```

---

## 14. Glossary

| Term | Meaning |
|---|---|
| NEWS2 | National Early Warning Score 2, reference for vital-sign scoring |
| ESI | Emergency Severity Index, background reference only |
| U1–U5 | SmartTriage AI urgency levels, not ESI |
| FIFO | First in, first out |
| Under-triage / Over-triage | Assigning lower / higher urgency than the reference |
| OP | Outpatient |
| RBAC | Role-based access control |
| ABDM | Ayushman Bharat Digital Mission (interoperability investigated, not integrated) |

---

## Disclaimer

SmartTriage AI is a research and demonstration prototype. Successful software tests and promising simulations do not establish clinical safety or real-world effectiveness. It must remain a prototype until clinical, security, privacy, regulatory and operational requirements have been independently addressed. It does not replace a hospital's approved triage protocol.
