---
description: Find what your career memory cannot prove yet
argument-hint: "[period, e.g. last-quarter]"
---

Use the `career-memory` skill, following `references/proactive.md`.

Run `gaps --window $ARGUMENTS` (default to the last six months) and show the
user what is missing: entries with no evidence, entries with no documented
impact, impact still marked inferred, candidates never confirmed, stretches with
nothing recorded, and competencies from `profile.md` that no entry mentions.

Do not read the list out. Pick the two or three that would strengthen the record
most and ask about them one at a time — "the retry-storm fix has no impact
recorded; did that stop the pages?" — then write down exactly what the user
says with `update <id> --set-impact "…"` or `--add-evidence`.

If the user does not know, or there was no measurable outcome, leave it
undocumented. `Impact: not documented` is the correct final state for plenty of
entries; a guess is not.
