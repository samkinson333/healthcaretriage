---
name: smarttriage-ui-pitfalls
description: Common frontend design mistakes to avoid in SmartTriage AI, a 24-hour hackathon build order and a QA checklist.
---
# Mistakes to avoid

## Visual
- Gradient hero, buttons, text, purple-blue washes, glow. Use flat tokens.
- Identical cards with one radius and one grey shadow. Queue rows are dense and flat, panels bordered, only modals get shadow.
- A marketing landing page before the app. Open straight into the queue board.
- Urgency by colour alone. Always colour + shape + text.
- Red everywhere. Reserve it for U1 and failures.
- Template chrome: tracked ALL-CAPS eyebrows, 01/02/03 numbering on non-sequences, middle-dot meta strings, arrows on buttons, one accented word in headlines.
- Text under 12px, or light grey vitals on white.
- Emoji as icons.

## Interaction
- Silent queue reordering. Animate moves and show why (rule chips, "Aged from U4").
- Timer width jitter. Use tabular numbers.
- Modals for everything. Review uses a side drawer.
- Required fields marked only by an asterisk. Disable Save and say why.
- Empty vitals defaulting to normal-looking numbers.
- Forms that reset on validation error.
- Dead buttons for planned features.

## Layout and CSS
- Fixed heights that clip on a projector; test 1366x768, 1920x1080 and 390px.
- Section padding fighting element margins; one spacing scale, avoid competing class and element selectors.
- Horizontal page scroll on mobile; wide tables scroll inside their own container.
- Z-index wars: drawer 40, modal 50, toast 60.

## State
- Queue order stored separately from patients. Derive it from patients + simulated clock in a selector.
- Wall-clock time for waits. Use the simulated clock store everywhere.
- Overwriting the original recommendation on override. Store `recommended` and `effective` separately.

# 24-hour build order
| Hours | Deliverable |
|---|---|
| 0-2 | Vite app, tokens, font, shell, UrgencyChip, seed data, mock service |
| 2-6 | Queue board: sorting, aging, simulated clock, wait alerts, reorder animation |
| 6-10 | Review drawer: fired rules, NEWS2 breakdown, timeline |
| 10-14 | Intake stepper with simulated device and failure state |
| 14-17 | Override, deterioration, feedback with required reasons |
| 17-19 | Audit view, compare-policies panel, roadmap panel |
| 19-21 | Demo controls, reset, rehearse the journey twice |
| 21-23 | Responsive and accessibility pass, bug fixes, backup recording |
| 23-24 | Freeze; blockers only |
Cut order if behind: policy charts, roadmap polish, feedback form, audit filters. Never cut: queue board, assessment explanation, override, audit trace.

# QA checklist
- [ ] Full demo journey runs from Reset with no console errors
- [ ] Tab reaches every control; focus ring visible (brand colour, 2px)
- [ ] Text contrast 4.5:1; urgency distinguishable in greyscale
- [ ] Missing vital never appears as a number or in green
- [ ] Override cannot save without a reason; original stays visible
- [ ] Reduced-motion setting disables reorder animation
- [ ] No gradients, lorem ipsum or real personal data
- [ ] Synthetic-data tag visible on every screen
