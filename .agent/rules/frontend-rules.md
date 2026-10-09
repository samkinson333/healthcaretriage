---
trigger: always_on
---
# SmartTriage AI — Frontend Rules (hackathon)

## Scope
- Build UI only. No real backend, auth, DB or device work. Use an in-memory store behind `services/triage.ts` (mock now, real API later).
- Product: clinician-supervised ED queue + decision support. Never present it as diagnosing, treating or discharging.
- Rules engine logic is deterministic. UI never lets free text, AI, or device failure lower urgency. Only escalate automatically; lowering is a clinician override with a mandatory reason.

## Priorities (in order)
1. The demo journey works end-to-end without errors (see skill `smarttriage-demo-flow`).
2. Queue board and clinician review look excellent and read at a glance.
3. Honest status labelling (see `smarttriage-honest-labels`).
4. Everything else.

## Stack defaults (follow the existing repo if one exists)
React + Vite + TypeScript, Tailwind with CSS variables for tokens, Zustand (or Context) for in-memory state, lucide-react icons. No UI kit that imposes its own look.

## Autonomy
- Read files, create/edit UI files, install small frontend dependencies, run dev server/build/lint without asking.
- Ask first only for: deleting files, changing the stack, adding a backend, adding paid/external services.

## Definition of done for any screen
Loads with seed data, keyboard reachable with visible focus, readable at 1366x768 and on a 390px phone, urgency never conveyed by colour alone, empty/error states written, no console errors, no gradient decoration.
