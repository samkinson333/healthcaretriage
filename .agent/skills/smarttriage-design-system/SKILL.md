---
name: smarttriage-design-system
description: Visual tokens, urgency colour semantics, typography and layout rules for SmartTriage AI. Use before writing any component styles.
---
# SmartTriage design system

**Subject:** emergency-department staff under time pressure, reading a queue on a shared monitor or a nurse's laptop. The design's job: make the most urgent patient, and why, obvious in under 2 seconds. Calm, clinical, legible. Not a startup landing page.

## Colour (CSS variables, define once in `index.css`)
Neutrals are cool and quiet so urgency colours are the only loud thing on screen.
- `--ink` #1B2733 text, `--ink-soft` #4A5968 secondary text
- `--paper` #F3F6F8 app background, `--surface` #FFFFFF panels, `--line` #D3DBE2 borders
- `--brand` #0E6B78 (actions, focus ring, selected state). One brand colour only.

Urgency tokens:
| Level | Meaning | Fill | Tint | Shape + label |
|---|---|---|---|---|
| U1 | Immediate | #B3261E | #FBE9E7 | octagon icon, "U1 Immediate" |
| U2 | High risk | #C4570F | #FCEDE0 | triangle icon, "U2 Urgent" |
| U3 | Timely | #8A6A00 | #FAF1D2 | diamond icon, "U3 Soon" |
| U4 | Standard | #2B6A9B | #E4EFF7 | circle icon, "U4 Standard" |
| U5 | Lower | #5B6772 | #ECEFF2 | outlined circle, "U5 Low" (staff-assigned only) |

Rules: every urgency chip = colour + icon shape + text label + level code. Keep 4.5:1 contrast for text on tint. Red is reserved for U1 and failed/destructive states.
Data-quality warning: amber outline with icon. Device/API failure: neutral grey banner with warning icon. Never green "OK" styling for missing or failed data.

## No gradients
Flat fills only. No gradient backgrounds, gradient text, gradient buttons, glow shadows or glassmorphism. Depth comes from 1px borders; one shadow level for popovers/modals only. If the page feels plain, fix hierarchy and spacing, not decoration.

## Typography
- Family: **Atkinson Hyperlegible Next** (Google Fonts, or bundled locally for demo safety), fallback `system-ui, sans-serif`. Chosen for clear character shapes (1/l/I, 0/O) in patient IDs and vitals. One family, weights 400/600/700.
- `font-variant-numeric: tabular-nums` on vitals, timers and IDs.
- Scale (px): 12 meta, 14 body/table, 16 form, 20 panel title, 28 page title, 40 big-display timer/level. Line-height 1.45.
- Sentence case everywhere. No tracked ALL-CAPS eyebrows, no middle-dot meta strings, no "→" on buttons.

## Layout and shape
- 8px spacing grid. Radius: 6px controls, 10px panels, full-round only for chips. Do not use one radius for everything.
- Queue rows 64-72px high: one line of patient info, wait timer right-aligned.
- App shell: left nav (Queue, Intake, Audit, Roadmap), top bar with simulated clock and a persistent "Synthetic demo data" tag.
- Left-align text. Max 70ch for paragraphs.

## Motion
Only: queue row reordering (200ms layout animation so staff see who moved), a one-time pulse on a new U1 arrival, wait-alert badge appearing, drawer open. Respect `prefers-reduced-motion`. No section entrance fades, no hover lifts on cards.

## Icons
lucide-react, 20px, 1.75 stroke, paired with text whenever the meaning is clinical.
