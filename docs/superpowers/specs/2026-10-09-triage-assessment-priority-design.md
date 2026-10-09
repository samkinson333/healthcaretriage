# Triage Assessment and Priority Module — Design

**Date:** 2026-10-09  
**Status:** Design approved in conversation; awaiting written-spec review.  
**Scope:** Presentation-ready React + Django prototype using synthetic data only; not for real-patient care or deployment.

## Intent and success criteria

Build the assigned Triage Assessment & Priority module so its presentation workflow works end to end: collect screening data, submit to Django, receive and explain a provisional U1–U5 recommendation, persist it with the patient, and show the patient in a priority-ordered queue. The prototype must state that rules are unvalidated and that clinicians retain responsibility. It must not claim unrelated roadmap items (authentication, LLM extraction, Malayalam, or production readiness) are implemented.

## Current context

The repository contains a React 19 + Vite frontend and a Django backend with a `triage` app and SQLite. The backend currently supports patient registration and vital-measurement APIs. It does not yet contain triage assessments, scoring, queue ordering, override/feedback APIs, or an integrated assessment screen. Project skills under `.agent/` define visual semantics, expected intake workflow, honest status labels, synthetic seed scenarios, and queue behavior. These specifications govern the UI copy and presentation behavior.

## Architecture and data flow

Django is authoritative for assessment and priority. React captures the form and renders results; it does not compute or mutate an authoritative urgency level.

1. React submits patient context, screening observations and provenance, complaint/red-flag selections, and nurse concern to a versioned Django API.
2. Django validates the request, treats missing/implausible observations as unknown rather than normal, calculates the documented prototype rules and NEWS2-based breakdown, and persists an assessment.
3. The API returns the recommendation, fired rules and explanations, data-quality warnings, direct-clinician-assessment notice where applicable, and rule version.
4. React renders the explanation and fetches the ordered waiting queue from Django.
5. Queue operations (simulated clock advancement, deterioration, and any implemented clinician review action) are persisted as events; original recommendation remains distinct from effective clinician-assigned urgency.

No LLM, external clinical service, real device, or network-dependent scoring path is in scope. All seed data and demo records must be visibly synthetic.

## Assessment inputs and rule behavior

The form captures age and pregnancy status; respiratory rate, SpO₂, temperature, systolic blood pressure, pulse, consciousness, and supplemental oxygen; red-flag symptoms; nurse concern; and source/provenance for each observation (manual or simulated device). The interface must allow missing readings to remain missing and explain their caution effect.

Use the project's documented prototype rule set without inventing new clinical thresholds:

- R1: specified immediate red flags → U1.
- R2: specified high-risk symptoms → at least U2.
- R3/R4: documented NEWS2 total thresholds → U1 / at least U2.
- R5: any NEWS2 parameter score of 3 → at least U3.
- R6: any required observation missing or implausible → at least U3, never normal.
- R7: age under 16 or pregnancy → at least U3 and direct clinician assessment.
- R8: complete data and no other rule → U4.
- R9: nurse concern escalates one level.
- U5 is staff/clinician assigned only; automation never assigns it.
- Overrides, if exposed in this module, require a reason and preserve the original recommendation.

The backend response should include the rule IDs and plain-language reasons, parameter-level NEWS2 breakdown where calculable, warnings, and a stable rule-version identifier. Rule precedence and interaction behavior must be explicit in code and tests; ambiguity found in existing project material must not be silently filled with unsupported clinical policy. Any necessary implementation interpretation should be clearly labelled as a prototype assumption and surfaced for clinician review.

## Queue and presentation workflow

The queue is retrieved from Django and ordered by effective urgency, then arrival time. Waiting U4/U5 cases age one level per 60 simulated minutes, capped at U3; an aged case remains below a genuine U3 case. Assumed maximum-wait prompts are U1 immediate, U2 15 minutes, U3 30 minutes, U4 60 minutes, U5 120 minutes. Alerts request reassessment and are not guarantees or substitutes for clinical judgment. A deterioration action raises urgency one level and records an event. In-consultation work is not reordered/interrupted.

Provide a simulated clock so a presenter can deterministically demonstrate aging and alerts. Display queue position, urgency code and text/shape cue, reference, fired-rule indicators, wait duration, state, aging provenance, and reassessment prompt. Do not communicate urgency by color alone. Preserve existing patient registration/vitals workflow and connect its patient records to the assessment flow.

## Persistence and API boundary

Persist assessments linked to existing patients, including submitted input snapshot and provenance, recommendation, rule reasons/breakdown, rule version, timestamps, and lifecycle state. Preserve original recommendation separately from effective urgency and append queue/review events rather than silently rewriting history.

Define Django endpoints for creating/retrieving assessments, getting the ordered queue, and advancing the simulated clock / recording deterioration if those actions are included in the delivered workflow. Match existing repository API style unless a concrete limitation requires a documented adjustment. Validate data server-side. This is still a presentation prototype: do not represent current unauthenticated endpoints as production-secure or expose them for real-patient use.

## UI and honest status

Build on the existing React/Vite app and CSS; do not change stacks. Add a triage assessment screen with a clear U1–U5 indicator, recommendation label, fired rule explanations, NEWS2 breakdown, data-quality warnings, and queue placement. Follow `.agent/skills/smarttriage-design-system`, `smarttriage-screens`, `smarttriage-demo-flow`, `smarttriage-honest-labels`, and `.agent/rules/frontend-rules.md` where applicable. Persistent copy must state that this is synthetic demo data, not for clinical use, and that rules are prototype/unvalidated. Keep planned features visibly planned and nonfunctional rather than simulating them as built.

## Testing and verification

Backend tests cover representative rules and boundaries, missing/implausible data, no automatic downgrade/U5 assignment, persistence and original recommendation preservation, queue priority and arrival tie-break, aging at/around 60-minute boundaries and cap, max-wait thresholds, and deterioration event recording. Frontend verification includes a successful production build and manual flow checks for validation/errors, returned explanation, queue update, responsive layout, keyboard access, and visible status disclaimers. Run the full Django suite and frontend build; report actual results, including any gaps.

## Out of scope

Real-patient use or deployment; clinical validation; new clinical rules or thresholds; login/RBAC/rate limiting; LLM or speech extraction; Malayalam; real-device integration; hospital or ABDM integration; production privacy/security/compliance certification; and features from the full plan not required by this assessment-and-priority assignment.

## Important risks and presentation caveats

- These rules have not been clinician-reviewed; NEWS2 and team-proposed red flags do not establish clinical safety.
- Missing-data escalation to U3 is the documented prototype behavior, not proof of safety; critical cases with partial data may still be under-prioritized.
- The red-flag list is short; frailty, chronic CO₂ retention, pediatric and pregnancy-specific assessment, trauma, poisoning, snakebite, self-harm, and diabetic emergencies remain limitations.
- Priority scheduling can substantially increase lower-urgency waits; aging and alerts do not remove this trade-off.
- Existing backend has no authentication and its current API uses CSRF exemptions for selected write views; it must remain a local synthetic-data presentation prototype.
- No clinical claims may be inferred from successful software tests or simulations.
