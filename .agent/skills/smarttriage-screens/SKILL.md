---
name: smarttriage-screens
description: Screen architecture, components and interaction details for the SmartTriage AI frontend (queue board, intake/kiosk flow, clinician review, audit). Use when building or changing any page.
---
# Screens (build in this order)

## 1. Queue board (the hero: build first and best)
Purpose: who is next and why.
```
+--------------------------------------------------------------+
| Queue  [Waiting 7] [In consultation 1]   Clock 14:32 [+15m]  |
+--------------------------------------------------------------+
| #1 [U1 Immediate] DEMO-004  Unresponsive  R1     wait 02:10  |
| #2 [U2 Urgent]    DEMO-002  Chest pain    R2  Reassess due   |
| #3 [U3 Soon]      DEMO-003  SpO2 91%      R5     wait 12:00  |
| #4 [U3 Soon]      DEMO-001  Aged from U4         wait 61:00  |
+--------------------------------------------------------------+
```
- Row: rank, urgency chip, patient reference, short complaint, fired-rule chips, wait timer, state.
- Aged patients show a small "Aged from U4" tag and rank below true U3 patients.
- Wait alert: row tint plus "Reassess due" button; acknowledging records an event.
- Row click opens the review drawer (not a new page) so the board stays visible.
- Simulated clock control top right: +15 min, +60 min.
- Empty state: "No patients waiting. Register a patient to start." with a button.
- Policy comparison (FIFO / Strict priority / Priority + aging) lives on a secondary "Compare policies" panel, not on the main board.

## 2. Intake and screening (kiosk-style stepper)
Genuinely sequential steps: Register, Screening, Symptoms, Confirm. Touch targets at least 48px, one task per step.
- Register: patient reference auto-generated (DEMO-###), age, pregnancy; shows an OP ticket card.
- Screening: RR, SpO2, temperature, systolic BP, HR, consciousness, supplemental oxygen. Each reading carries a source tag: Device (simulated) or Manual. Buttons: "Read from device (simulated)", "Enter manually". Demo button "Simulate device failure" produces a failed-read state.
- Missing or implausible value: inline amber message, e.g. "Heart rate is missing. It is treated as unknown, not normal." Never default to a number.
- Symptoms: free-text complaint plus red-flag checkboxes (chest pain, stroke signs, severe breathlessness, vomiting blood, seizure, severe bleeding, anaphylaxis, unresponsive) and a nurse-concern toggle.
- Confirm: summary of inputs with provenance, then "Run assessment".
- Age under 16 or pregnancy: notice "Needs direct clinician assessment"; patient still enters the queue at least U3.

## 3. Assessment result and clinician review (right drawer)
1. Header: patient ref, large urgency chip, "Recommended by rules (prototype-1)".
2. Why: fired rules as plain sentences ("R5: one NEWS2 parameter scores 3") and a NEWS2 breakdown table.
3. Data-quality warnings.
4. Actions: "Record deterioration" (+1 level), "Override urgency", "Give feedback".
5. Timeline of events, newest first.
Override dialog: choose level, reason required (Save disabled with visible explanation until filled), shows the original recommendation that will be kept. After saving: chip shows "Clinician: U2" with "Rules said: U4" beneath.
Feedback: Appropriate, Too urgent, Not urgent enough, Unable to judge. Disagreement requires a rationale and shows "Flagged for second review".

## 4. Audit view
Read-only table: time, actor role, event, patient, before and after, reason, rule version. Filters: patient, event type. Overrides show original and clinician decision side by side. No edit or delete controls.

## 5. Roadmap panel
Disabled cards with Planned badges: login and roles, persistence, LLM extraction, Malayalam intake, real kiosk device integration.

## 6. Demo controls (collapsible, bottom-left, `?demo=1` or toggle)
Load seed patients, reset, advance clock, simulate device failure, simulate U1 arrival.

## Shared components
UrgencyChip, RuleChip, WaitTimer, SourceTag, StatusBadge (Built/Simulated/Planned), EventTimeline, ConfirmDialog, EmptyState, InlineWarning.
