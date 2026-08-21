---
description: Generate a brag document from your recorded evidence
argument-hint: "[period, e.g. last-quarter]"
---

Use the `career-memory` skill, following `references/outputs.md`.

Generate a brag document covering: $ARGUMENTS (default to the last quarter if no
period is given).

Pull evidence with `list --format full` and `stats` for recurring themes. Group
related work by theme, include evidence references, label patterns as
observations, and end with an honest list of work that has no documented
evidence. Save to `outputs/brag.md` in the store and tell the user the path.
