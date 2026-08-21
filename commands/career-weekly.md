---
description: Write the weekly summary of what your career memory recorded
argument-hint: "[week, e.g. last-week]"
---

Use the `career-memory` skill, following `references/proactive.md`.

Write the weekly summary for: $ARGUMENTS (default to last week if no period is
given; use the current week only if the user asks for it).

Run `summary --window <period> --format markdown` for the facts, start from
`templates/weekly-summary.md`, and save the result to
`outputs/summaries/<YYYY-Www>.md` — the path `summary` prints. Keep that name:
it is how `checkup` knows the week is done.

Report the record, not the week. A quiet week means few entries were recorded,
which is not the same as a quiet week — say it that way, and offer
`github discover` for the same range before anyone concludes anything. End with
the open questions from the entries that lack evidence or impact, and let the
user answer them.
