---
description: Write the monthly summary of what your career memory recorded
argument-hint: "[month, e.g. last-month or 2026-07]"
---

Use the `career-memory` skill, following `references/proactive.md`.

Write the monthly summary for: $ARGUMENTS (default to last month if no period is
given).

Run `summary --window <period> --format markdown` and `stats --window 3m` for
recurring themes, start from `templates/monthly-summary.md`, and save to
`outputs/summaries/<YYYY-MM>.md` — the path `summary` prints.

A month is not four weeks stapled together: group by theme and project, name
what carried across weeks, and keep it readable in a minute. Every claim traces
to an entry; patterns are labelled as observations. Close with the gaps from
`gaps --window <period>` and what is worth carrying into the quarterly brag
document.
