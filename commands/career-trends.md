---
description: See how your recorded work and competencies evolved over time
argument-hint: "[period, e.g. 12m or 2y]"
---

Use the `career-memory` skill, following `references/intelligence.md`.

Run `trends --window $ARGUMENTS` (default to the last 12 months) and show the
user how the record evolved: entries and coverage period by period, each
competency's trajectory across those periods, the themes where impact is
actually documented, and the earlier half of the range against the recent half.

Report the record, not the person. A theme that fades may have moved, stopped,
or simply stopped being written down — offer `github discover` for that range
before anyone concludes anything, and never explain the curve on the user's
behalf. Skills, and trajectories built on them, are interpretation: say so.

If the user wants the longitudinal document, run
`trends --format markdown`, start from `templates/career-trends.md`, and save it
to `outputs/trends/<since>_<until>.md` — the path the command prints.

End with the two or three questions the view raises, one at a time.
