---
description: Find GitHub work and turn it into candidate career evidence
argument-hint: "[period or repo, e.g. last-month or acme/payments]"
---

Use the `career-memory` skill, following `references/github.md`.

Discover the user's GitHub activity and turn what matters into evidence:
$ARGUMENTS (default to the last 30 days when no period is given).

Run `github discover` first and show the user what came back, marking what is
already recorded. Import only what they want kept — imports land in
`candidates/`, and only the user promotes them. For each candidate, ask what the
change actually did for anyone, and record their answer as impact; leave it
undocumented if there is none.

If a discovered PR matches something they already told you about, link the
evidence to that entry instead of creating a second one.

If GitHub is unreachable or unauthenticated (exit code 3), say so and stop —
do not reconstruct their GitHub activity from memory.
