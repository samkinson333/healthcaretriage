# Triage Assessment and Priority Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a working React + Django synthetic-data presentation workflow that captures triage inputs, calculates and explains a provisional U1–U5 recommendation on Django, persists assessments, and orders the waiting queue.

**Architecture:** Django remains authoritative for validation, scoring, assessment persistence, queue selection, simulated time and event recording. React provides the intake, recommendation and queue interface through the existing `/api/v1/` Vite proxy. Use the documented prototype rules only, with explicit precedence/versioning and synthetic/demo disclaimers; do not imply clinical validation or deployment readiness.

**Tech Stack:** Django, SQLite, Python, React 19, Vite, JavaScript/JSX, CSS, Django TestCase.

**Spec:** `docs/superpowers/specs/2026-10-09-triage-assessment-priority-design.md`

## Global Constraints

- Synthetic data only; prototype is not for real-patient care or deployment.
- Django is the authoritative source for assessment and priority; React must not calculate or overwrite authoritative urgency.
- Missing or implausible observations remain unknown and trigger at least the documented R6 caution floor; never silently use normal defaults.
- U5 is staff/clinician assigned only; automation never assigns it.
- Automated logic may escalate only; a clinician downgrade requires a reason and must preserve the original recommendation.
- Priority queue: higher urgency first, equal-level earlier arrival first; waiting U4/U5 age one level per 60 simulated minutes, cap U3, aged cases rank below true U3.
- Assumed wait prompts: U1 immediate, U2 15 minutes, U3 30 minutes, U4 60 minutes, U5 120 minutes; prompts are not safety guarantees.
- Persistent UI copy must state synthetic demo data, not for clinical use; rules are prototype/unvalidated.
- No auth/RBAC, LLM, Malayalam, real-device, hospital, ABDM, or deployment claims in this scope.
- Follow `.agent/skills/smarttriage-design-system`, `smarttriage-screens`, `smarttriage-demo-flow`, `smarttriage-honest-labels`, `.agent/skills/smarttriage-ui-pitfalls`, and `.agent/rules/frontend-rules.md`.

## Review Focus

- Partial observations paired with a red flag must not be downgraded or hidden by R6; test combined red-flag and missing-vital behavior in Task 2.
- Non-boolean values, booleans-as-numbers, strings, `null`, and out-of-range input must return field errors rather than 500s; test in Task 3.
- Simulated clock requests must reject negative/oversized advances and be deterministic under repeated requests; test in Task 5.
- Stale/double-click submissions must not create confusing duplicate queue records; test idempotence or make the UI prevent duplicate submissions in Task 8.
- Patients in consultation/completed states must not enter waiting ordering or accrue waiting aging; test in Task 6.

---

## File Map

- `backend/triage/assessment.py` — deterministic NEWS2 parameter scoring, rule combination, reasons, warnings, and version.
- `backend/triage/models.py` — assessment and append-only queue event persistence linked to existing patient records.
- `backend/triage/migrations/` — generated schema migration.
- `backend/triage/queue.py` — queue ordering, aging, wait prompts, and state-specific selection.
- `backend/triage/validation.py` — server-side assessment request validation.
- `backend/triage/views.py`, `backend/triage/urls.py` — JSON endpoints and serialization.
- `backend/triage/tests.py` — assessment, API, queue, event and edge-case regression tests.
- `frontend/src/services/api.js` — assessment and queue endpoint client methods.
- `frontend/src/components/TriageAssessment.jsx` — data capture, validation display, submission, result explanation.
- `frontend/src/components/PriorityQueue.jsx` — queue rows, simulated clock actions, loading/empty/error states.
- `frontend/src/App.jsx` — integrate the module with existing patient/vitals flow and queue refresh.
- `frontend/src/index.css` — urgency tokens, assessment/queue layout, responsive/focus styles.
- `chats/jims_chats.md` — concise project and session context requested by the user.

## Task 1: Add Assessment and Queue Event Models

**Files:**
- Modify: `backend/triage/models.py`
- Create: `backend/triage/migrations/<generated initial assessment migration>`
- Test: `backend/triage/tests.py`

**Interfaces:**
- Consumes: existing `Patient` model.
- Produces: `TriageAssessment(patient, inputs, recommendation, effective_level, fired_rules, news2_breakdown, warnings, rule_version, state, arrived_at, created_at)`; `QueueEvent(assessment, event_type, before, after, reason, occurred_at)`. JSON fields preserve input/output snapshots.

- [ ] **Step 1: Add model tests** for assessment-to-patient linkage, default `effective_level == recommendation`, waiting state and event ordering.
- [ ] **Step 2: Run the targeted tests** with `cd backend && ../../.venv/bin/python manage.py test triage.tests.AssessmentModelTests -v 2`; confirm they fail because models do not exist yet.
- [ ] **Step 3: Implement the two models** using `JSONField(default=dict)` for snapshots/rule details, constrained choices for U-level/state/event types, and explicit ordering/indexes for patient/time and waiting-state queries. Keep `recommendation` immutable by service convention; store override in `effective_level` separately.
- [ ] **Step 4: Generate and apply migration** with `../../.venv/bin/python manage.py makemigrations triage` and `../../.venv/bin/python manage.py migrate` from `backend/`.
- [ ] **Step 5: Run model tests** with `../../.venv/bin/python manage.py test triage.tests.AssessmentModelTests -v 2` and confirm pass.

## Task 2: Implement Deterministic Assessment Engine

**Files:**
- Create: `backend/triage/assessment.py`
- Modify: `backend/triage/tests.py`

**Interfaces:**
- Consumes: validated assessment input mapping.
- Produces: `assess(inputs: dict) -> dict` returning `recommendation` (`U1`–`U4` only), `fired_rules` (list of `{id, reason}`), `news2_breakdown` (per parameter points and total or `None` if incomplete), `warnings` (list), `direct_clinician_assessment` (bool), `rule_version` (constant `prototype-1`).
- Precedence: evaluate all eligible R1–R9; determine the most urgent permitted automatic result; enforce floor constraints; preserve U5 exclusion. Never let a lower-priority rule undo a higher one. R9 raises one level from the current automatic result but cannot create U5.

- [ ] **Step 1: Write failing tests** for each NEWS2 parameter boundary and total boundary R3/R4; R1, R2, R5, R6, R7, R8, R9; simultaneous triggers; no automatic U5; and partial observations with red flags.
- [ ] **Step 2: Run** `cd backend && ../../.venv/bin/python manage.py test triage.tests.AssessmentEngineTests -v 2`; confirm missing import/function failures.
- [ ] **Step 3: Implement NEWS2 scoring** according to the project's documented RCP NEWS2 2017 Scale 1 parameter bands for respiratory rate, SpO₂ Scale 1, supplemental oxygen, systolic BP, pulse, temperature, and consciousness. Keep band definitions explicit and isolated. For any missing/invalid required field, do not calculate a misleading complete total; include a warning and apply R6 floor U3.
- [ ] **Step 4: Implement rule combination** with a documented urgency ordering, all fired-rule reasons, R1/R2 symptom flags, R7 direct-assessment flag, R9 one-level escalation, and automated levels limited to U1–U4. Do not infer unsupported alternate clinical policy; add a code comment that this is a project prototype interpretation and not clinician-reviewed.
- [ ] **Step 5: Run engine tests** and confirm pass; if thresholds conflict with the project plan, stop and surface the ambiguity rather than silently changing them.

## Task 3: Validate Assessment API Payloads

**Files:**
- Modify: `backend/triage/validation.py`
- Modify: `backend/triage/tests.py`

**Interfaces:**
- Produces: `validate_assessment(payload) -> (cleaned, errors)`; cleaned values include `age`, `pregnant`, `observations`, `symptoms`, `nurse_concern`, and per-observation `source`.
- Use explicit allowed symptom/source field sets; reject unknown keys or normalize only documented optional fields.

- [ ] **Step 1: Add validation tests** for valid complete and incomplete assessments, omitted values, malformed JSON types, bool-as-number, numeric strings, out-of-range values, malformed symptom arrays and source values.
- [ ] **Step 2: Run** `cd backend && ../../.venv/bin/python manage.py test triage.tests.AssessmentValidationTests -v 2`; confirm tests fail before the validator is added.
- [ ] **Step 3: Implement strict validation** for types, documented plausible ranges, allowed values, and missing values represented explicitly as `None`; return per-field errors without applying normal defaults. Treat Python `bool` as invalid for numeric observation fields.
- [ ] **Step 4: Run validation tests** and confirm all pass, including malformed/hostile JSON structures returning errors rather than exceptions.

## Task 4: Assessment Create/Read API and Persistence

**Files:**
- Modify: `backend/triage/views.py`
- Modify: `backend/triage/urls.py`
- Modify: `backend/triage/tests.py`

**Interfaces:**
- `POST /api/v1/patients/<pk>/assessments/` validates, calls `assess`, persists `TriageAssessment`, and returns serialized assessment (`201`).
- `GET /api/v1/assessments/<pk>/` returns saved input/result snapshots.
- Assessment serializer includes patient reference, recommendation, effective level, fired rules, NEWS2 breakdown, warnings, direct-assessment flag, rule version, state and timestamps.

- [ ] **Step 1: Add API tests** for 201 creation and persistence, GET round trip, unknown patient/assessment 404, invalid payload 400, and preserving returned recommendation on subsequent queue changes.
- [ ] **Step 2: Run targeted API tests** and confirm failures before endpoint wiring.
- [ ] **Step 3: Implement JSON parsing/serialization and endpoints** following current `views.py` patterns. Keep write endpoints synthetic-prototype-only and do not describe them as authenticated or production secure.
- [ ] **Step 4: Run API tests** and confirm database records preserve the original engine recommendation and fired-rule explanation.

## Task 5: Queue Selector, Simulated Clock, and Wait Prompts

**Files:**
- Create: `backend/triage/queue.py`
- Modify: `backend/triage/models.py` (clock persistence model if needed)
- Modify: `backend/triage/views.py`
- Modify: `backend/triage/urls.py`
- Modify: `backend/triage/tests.py`

**Interfaces:**
- `get_waiting_queue(now) -> list[dict]` orders waiting assessments by effective urgency and arrival, calculates aged display level, wait minutes, aging origin, and threshold alert.
- `advance_demo_clock(minutes) -> datetime` advances persisted demo time only for allowed increments (15 or 60 minutes); reject negative, arbitrary, or excessive advances.
- Endpoint `GET /api/v1/queue/`; `POST /api/v1/demo/clock/` with `{minutes: 15|60}`.

- [ ] **Step 1: Add tests** for same-level arrival tie-break, higher urgency ordering, 59/60/119/120-minute aging boundaries, U3 cap, aged U4/U5 below true U3, each alert boundary, consultation/completed exclusion, invalid clock increments, and repeatable clock advancement.
- [ ] **Step 2: Run queue tests** and confirm they fail before selector and clock exist.
- [ ] **Step 3: Implement queue calculations** in a pure selector using an explicit `now` argument; use simulated time from a singleton clock row initialized to a deterministic documented value. Do not use wall-clock time in tests or queue waits.
- [ ] **Step 4: Implement queue and clock endpoints** with strict request validation and a persisted clock event.
- [ ] **Step 5: Run queue tests** and confirm all edge cases pass.

## Task 6: Deterioration Event and State-safe Queue Updates

**Files:**
- Modify: `backend/triage/views.py`
- Modify: `backend/triage/urls.py`
- Modify: `backend/triage/queue.py`
- Modify: `backend/triage/tests.py`

**Interfaces:**
- `POST /api/v1/assessments/<pk>/deterioration/` records one-level escalation (never beyond U1), updates `effective_level`, appends `QueueEvent`, returns updated queue row.
- State values: `waiting`, `in_consultation`, `completed`; only waiting assessments appear in queue or age. No transition may silently erase recommendation history.

- [ ] **Step 1: Add tests** for escalation at U4/U3/U2/U1, repeated deterioration, event before/after values, and no queue inclusion/aging for non-waiting records.
- [ ] **Step 2: Run targeted tests** and confirm failure before endpoint.
- [ ] **Step 3: Implement the endpoint** with allowed method, assessment existence checks, an atomic transaction for level + event persistence, and a defined idempotency behavior for accidental repeated submissions (client request ID or server duplicate-window guard).
- [ ] **Step 4: Run targeted and full backend tests** and confirm no regression.

## Task 7: Frontend API Client and Assessment Form

**Files:**
- Modify: `frontend/src/services/api.js`
- Create: `frontend/src/components/TriageAssessment.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- API client: `createAssessment(patientId, payload)`, `getAssessment(id)`, `getQueue()`, `advanceDemoClock(minutes)`, `recordDeterioration(id, requestId)`.
- `TriageAssessment({patient, onCreated})` captures age/pregnancy, observations and source, symptom flags, nurse concern; submits to API; renders backend response and accessible field errors.

- [ ] **Step 1: Add focused pure UI tests** if a test runner already exists; otherwise add only a small standard React testing setup after checking package scripts/dependencies. Cover missing values remain blank and payload/source mapping exactly.
- [ ] **Step 2: Implement API methods** with current `request()` error handling and no locally calculated urgency.
- [ ] **Step 3: Implement assessment form** with explicit `Missing` state, input provenance tags, device simulated label only, symptom flags, nurse concern, one submission at a time, and visible backend errors.
- [ ] **Step 4: Render response explanation** with the level code + descriptive label + shape cue, rule reasons, NEWS2 breakdown, warnings, direct-clinician-assessment notice and persistent disclaimer. Never render green success styling for missing readings.
- [ ] **Step 5: Integrate selected patient** into `App.jsx` without removing existing registration/vitals features; verify form is unavailable until a patient is selected.

## Task 8: Priority Queue UI and End-to-end Presentation Flow

**Files:**
- Create: `frontend/src/components/PriorityQueue.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- `PriorityQueue({queue, clock, onAdvanceClock, onDeterioration, onRefresh})` renders API-supplied order and status; React does not sort or recalculate urgency.
- Assessment submission refreshes queue and selected assessment; API failures preserve form data and show retry guidance.

- [ ] **Step 1: Implement queue rows** with rank, urgency chip (color + shape + text), synthetic reference, short complaint, rule chips, simulated wait, state, aging provenance and “Reassess due” prompt.
- [ ] **Step 2: Add simulated clock controls** for +15m and +60m; disable controls while request in flight, refresh queue from Django on success, keep controls deterministic.
- [ ] **Step 3: Add deterioration action** that calls Django once per click, displays result/error, refreshes queue and avoids duplicate submissions.
- [ ] **Step 4: Add loading, empty, and failure states**; empty text: “No patients waiting. Register a patient to start.” Do not drop current form entries after API errors.
- [ ] **Step 5: Confirm the full demo flow** from patient registration through assessment result to queue ordering, aging and alerts, reload to prove records persist, and backend unavailable state with retry.

## Task 9: Responsive/Accessibility Pass and Required Chat Context

**Files:**
- Modify: `frontend/src/index.css`
- Create: `chats/jims_chats.md`

**Interfaces:**
- Responsive UI works at 1366x768 and 390px without page-level horizontal scrolling; all controls keyboard reachable.
- `chats/jims_chats.md` records concise session decisions, repository architecture/current feature status, key safety limitations, and remaining work. It must not assert unimplemented work as complete.

- [ ] **Step 1: Add CSS tokens and styles** using `.agent` design system values (cool neutrals, single teal brand, U1–U5 distinct colors, no gradients, visible focus, tabular numbers, minimum readable text and touch targets).
- [ ] **Step 2: Check responsive layout and reduced motion** at desktop/mobile sizes; queue table scrolls within its region only if needed; use `prefers-reduced-motion` for any reordering animation.
- [ ] **Step 3: Keyboard-check** patient selection, assessment inputs, submit, queue clock controls and deterioration; verify focus ring, labels, `aria-invalid`, and announced result/error states.
- [ ] **Step 4: Write `chats/jims_chats.md`** with: user asked for full-stack assessment/priority module and session summary; chosen backend-authoritative approach; synthetic-only/non-deployment intent; rules and queue caveats; commands to run tests/build; actual verification results only after Task 10.

## Task 10: Full Verification and Presentation Audit

**Files:**
- No additional files unless failures require focused fixes.

- [ ] **Step 1: Run Django checks/tests**: `cd backend && ../../.venv/bin/python manage.py check && ../../.venv/bin/python manage.py test triage -v 2`.
- [ ] **Step 2: Run frontend production build**: `cd frontend && npm run build`.
- [ ] **Step 3: Run local end-to-end smoke test** with synthetic patient: register → assess → inspect returned fired-rule details → queue ordering → +60m aging/alert → deterioration → reload and confirm persistence.
- [ ] **Step 4: Audit all visible claims and labels** against spec and `.agent/skills/smarttriage-honest-labels`; correct any “validated”, “accurate”, real-patient, or planned-as-built language.
- [ ] **Step 5: Record exact test/build/smoke outcomes** in `chats/jims_chats.md` and final report; explicitly note anything unverified or blocked.

## Spec Coverage Self-review

- Django authoritative assessment and persistence: Tasks 1–4.
- Documented scoring/rules and explanation: Task 2.
- Missing/implausible handling and strict request validation: Tasks 2–3.
- Priority queue, aging, alerts, deterministic simulated time: Task 5.
- Deterioration event and state behavior: Task 6.
- React screen and API integration: Tasks 7–8.
- Existing patient/vitals flow retained: Task 7.
- Accessibility/responsive/honest labels: Tasks 7–9.
- Backend and frontend verification: Task 10.
- Chat context output: Task 9, updated with actual verification in Task 10.

## Execution Notes

Do not commit unless the user explicitly asks. Before implementing Task 2, re-check the NEWS2 chart source and project specifications available in repository; if the values are not verifiable from the checked-in materials or exact precedence remains ambiguous, surface the gap instead of guessing a clinical threshold. Any unresolved clinical ambiguity stays clearly identified as a prototype assumption and is not described as clinically reviewed.
