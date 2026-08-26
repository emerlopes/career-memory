---
description: Build a promotion case for a target role
argument-hint: "[target role, e.g. Staff Engineer]"
---

Use the `career-memory` skill, following `references/outputs.md` and
`references/intelligence.md`.

Build a promotion case for: $ARGUMENTS (if empty, read the target from
`profile.md`, and ask if it is not there).

Start with `promotion --role "<target>" --window 12m`: it maps recorded evidence
onto the criteria for that level and sorts them into recorded repeatedly, thin
in the record, and nothing in the record mentions it — plus the entries that
match no criterion at all. Those buckets are the skeleton of the document. If
`profile.md` has no `## Promotion criteria`, say so and offer to write the
company's ladder into it; the analysis is only as good as the criteria it is
given.

Quote the entries behind each criterion, show how often each pattern appears and
over how many periods, and be specific about what is thin — a criterion with two
entries from the same project is the kind of thing a committee asks about, and
naming it first is worth more than any adjective.

Do not deliver a verdict on readiness unless the user explicitly asks for your
opinion. A criterion with nothing recorded is a question — missing from the
record, or missing from the year? — and only the user can answer it.

Save to `outputs/promotion-case.md`.
