---
name: smarttriage-honest-labels
description: How the UI labels built, simulated and planned features and phrases safety-critical copy. Use when writing visible text, badges, empty states or results panels.
---
# Honest labelling

The project documentation insists planned features are never shown as working. The UI does the same.

## Persistent labels
- Top bar on every screen: "Synthetic demo data. Not for clinical use."
- Every vital shows a source tag: Device (simulated), Manual, or Missing.
- StatusBadge on feature panels: **Built**, **Simulated** (kiosk device, queue simulation results), **Planned** (login, persistence, LLM extraction, Malayalam, real kiosk API). Planned items live only on the Roadmap panel as disabled cards.

## Copy rules
- "Recommended urgency", never "diagnosis".
- 30-case evaluation: "27 of 30 matched team-authored labels. Not clinical accuracy; clinician review pending." List the three under-triage cases openly.
- Simulation: "Simulated mean wait in minutes, one clinician, synthetic arrivals."
- Alerts: "Reassess due" (a prompt, not a safety guarantee).
- Errors say what happened and what to do: "Device read failed. Retry or enter the value manually."
- Buttons name the action ("Save override", "Run assessment", "Record deterioration"); toasts reuse the verb ("Override saved").
- Level names: U1 Immediate, U2 Urgent, U3 Soon, U4 Standard, U5 Low. Tooltip once: these are project levels, not ESI.

## Never
- Green "normal" styling for missing or failed data.
- Any UI path that lowers urgency automatically.
- Fake login, real-looking patient names, invented latency or accuracy figures.
