# Entry schema

An entry is one Markdown file: YAML front matter for structure, body for the
human story. Nothing else is required to read it — that is the point.

## Front matter

```yaml
---
id: 2026-08-20-payment-race-condition # unique; generated as <date>-<slug>
date: 2026-08-20 # YYYY-MM-DD, when the work happened
type: problem-solving
project: payments # optional
status: confirmed # confirmed | candidate | dismissed
tags:
  - debugging
  - reliability
skills: # interpretation, not fact
  - technical problem solving
people:
  - João
evidence:
  - type: github_pr
    reference: "acme/payments#1234" # or "#1234" when the repository is obvious
    url: https://github.com/acme/payments/pull/1234 # optional
    title: Serialise payment capture # optional, as it reads on GitHub
  - type: metric
    reference: "API latency dashboard"
    value: "800ms → 300ms"
impact:
  statement: Addressed intermittent payment-processing failures
  confidence: factual # factual | inferred | uncertain
context: The issue was intermittent and hard to reproduce
source: slack # where the user told you, optional
---
```

Entries imported from GitHub use `<date>-<kind>-<owner>-<repo>-<number>` as the
id (`2026-08-20-pr-acme-payments-1234`) and carry `source: github`.

Only `id` and `date` are structurally required. Everything else is omitted when
unknown — an absent field is honest, an empty guess is not.

## Types

| Type              | Use when                                           |
| ----------------- | -------------------------------------------------- |
| `achievement`     | A concrete accomplishment                          |
| `delivery`        | Something shipped, released, launched              |
| `impact`          | A measured or reported outcome                     |
| `problem-solving` | A hard problem diagnosed or fixed                  |
| `feedback`        | Feedback received (goes to `feedback/`)            |
| `learning`        | Something learned; not yet an achievement          |
| `leadership`      | Direction-setting, decisions, mentoring, ownership |
| `collaboration`   | Work with or for other people                      |

Infer the type; do not ask the user to pick one. When an event is genuinely two
types (led a migration _and_ shipped it), pick the dominant one and put the
other in `tags`.

## Evidence types

`github_pr`, `github_issue`, `github_review`, `github_commit`, `document`,
`metric`, `dashboard`, `feedback`, `email`, `slack_message`, `meeting`,
`ticket`, `external_link`

GitHub evidence carries `url` and `title` alongside `reference` when the skill
knows them — `github link` and `github import` fill all three. Anything that
resolves to the same pull request, issue or commit counts as one reference,
whether it was written as a URL or as `owner/repo#123`.

CLI form is `type:reference[:value]`:

```bash
--evidence 'github_pr:#1234'
--evidence 'github_pr:https://github.com/acme/payments/pull/1234'
--evidence 'metric:API latency dashboard:800ms → 300ms'
--evidence 'meeting:Q3 planning review'
```

A URL is kept whole; anything else splits on the next colon into a value.
For GitHub references, `github link <entry-id> <url>` is better than
`--evidence`: it resolves the kind, fetches the title and refuses duplicates.

Good evidence is specific, attributable and traceable — something the user could
show a skeptical manager. "A PR" is not evidence; "PR #1234" is.

## Confidence

- `factual` — the user stated it, or it follows arithmetically from what they stated
- `inferred` — a reasonable reading of what they stated
- `uncertain` — needs confirmation before anyone relies on it

Never silently upgrade `inferred` to `factual`. If a later conversation confirms
it, `update` the entry — that is a real change with a real trigger.

## Body

```markdown
# Short factual title

What happened, in the user's own terms.

## Impact

Not documented.

## Evidence

- GitHub PR #1234

## Context

Why this was hard, or what it connects to.

## Skills

- debugging
- ownership
```

Sections with nothing to say are dropped, except `## Impact`, where an explicit
"Not documented." is worth keeping: it is a to-do the user can act on.

## Storage layout

```text
career-memory/
├── README.md
├── profile.md          stable career context, not evidence
├── entries/            confirmed evidence
├── candidates/         awaiting the user's confirmation
├── feedback/           feedback received
├── projects/           per-project context
└── outputs/            generated documents
```

Feedback entries live in `feedback/` and confirmed candidates move to
`entries/` — `add` and `promote` handle that routing.
