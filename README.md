# Career Memory

**Never forget the work you've done.**

Career Memory is an agent skill that keeps a persistent, factual record of your
professional work — and turns that same record into whatever you need to write
later: a standup update, a brag document, a performance review, a promotion
case, resume bullets, interview stories.

You mention what you did, in your own words, while you're already working:

> "Finally fixed that payment race condition. PR is #1234."

It becomes a durable piece of evidence:

```markdown
---
id: 2026-08-20-fixed-payment-race-condition
date: 2026-08-20
type: problem-solving
project: payments
status: confirmed
tags: [debugging, reliability]
evidence:
  - type: github_pr
    reference: "#1234"
---

# Fixed payment race condition

Identified and fixed a race condition in the payment processing system.

## Impact

Not documented.
```

Six months later, that entry writes part of your review. You captured it once.

```text
Work → Evidence → Memory → Narrative
```

## Why

Your work is scattered across PRs, Slack threads, tickets, meetings and memory.
By review season, most of it is gone. The usual fix — "keep a brag document" —
fails because it asks you to stop and write, which nobody does consistently.

Career Memory captures during the conversation you're already having with your
coding agent, and pays it back when you need it.

## The rule that makes it usable

**It never invents anything.** No metrics you didn't state, no outcomes you
didn't report, no feedback you didn't receive. When something is unknown it
records `Impact: not documented` instead of guessing.

That constraint is the product. A career record that inflates is one you can't
defend in a review conversation — so this one doesn't.

## Install

### Claude Code (recommended)

```bash
/plugin marketplace add emerlopes/career-memory
```

```bash
/plugin install career-memory@emerlopes-plugins
```

### Any agent that reads `SKILL.md`

Copy the skill directory into wherever your agent looks for skills:

```bash
git clone https://github.com/emerlopes/career-memory.git
cp -r career-memory/skills/career-memory ~/.claude/skills/career-memory
```

The skill is plain Markdown plus one dependency-free Python script — nothing is
Claude-specific except the install path.

## First run

```text
/career-memory:career-init
```

That creates your store (default `~/career-memory`) and helps you fill in a short
profile. Then just work — and mention what you did.

Pin the location anywhere you like:

```bash
export CAREER_MEMORY_HOME="$HOME/Documents/career-memory"
```

## Using it

Mostly you don't invoke anything. Say what happened and it gets captured:

> "Shipped the new dashboard today, customer's using it already."
>
> "Spent the morning helping João debug the auth flow."
>
> "Manager said the planning meeting went well because I ran it."

Then ask for what you need:

| Ask                                           | You get                                                    |
| --------------------------------------------- | ---------------------------------------------------------- |
| "prepare my daily"                            | A 30–90 second standup, split Yesterday / Today / Blockers |
| "what did I do this quarter?"                 | Your actual entries, with dates and evidence               |
| "generate my brag document"                   | Themed highlights with evidence, plus what's undocumented  |
| "draft my performance review"                 | Structured review, every claim traceable                   |
| "what evidence do I have for Staff Engineer?" | Strengths, patterns, and the specific gaps                 |
| "turn this into resume bullets"               | One-line bullets, real numbers only                        |
| "prep me for behavioral interviews"           | STAR stories built from real events                        |

Slash commands are available for the same things: `/career-memory:career-daily`,
`career-add`, `career-brag`, `career-review`, `career-promotion`,
`career-resume`, `career-interview`, `career-search`.

## Your data

Plain Markdown in a directory you own:

```text
~/career-memory/
├── profile.md          your role, focus, goals
├── entries/            confirmed evidence, one file per event
├── candidates/         possible evidence awaiting your confirmation
├── feedback/           feedback received
├── projects/           per-project context
└── outputs/            generated documents
```

Local by default. No database, no account, no server, nothing sent anywhere.
Readable and editable without any agent. Put it in a private git repository if
you want history:

```bash
cd ~/career-memory && git init && git add . && git commit -m "career memory"
```

## CLI

The skill drives a small CLI so entry ids, front matter and searching are exact
rather than improvised. You can use it directly too:

```bash
CM=skills/career-memory/scripts/career_memory.py

python3 $CM init
python3 $CM add "Led migration of 4 services" --type leadership --project platform
python3 $CM update 2026-08-20-led-migration-of-4-services --add-evidence 'github_pr:#88'
python3 $CM list --window last-quarter
python3 $CM search "reliability" --format full
python3 $CM stats --window 6m
python3 $CM validate
```

Python 3.9+, standard library only. PyYAML is used if present, but isn't
required.

## Roadmap

- **v0.1** — Markdown storage, capture, candidates, search, brag documents, daily mode _(current)_
- **v0.2** — GitHub: discover PRs, issues, commits and reviews as candidate evidence
- **v0.3** — Proactive memory: weekly/monthly summaries, missing-evidence detection
- **v0.4** — More interfaces: Telegram, standalone CLI, other agents
- **v0.5** — Career intelligence: competency evolution, promotion-gap analysis over time

Full specification: [`docs/SPEC.md`](docs/SPEC.md).

## Contributing

Issues and pull requests are welcome. The behavioral contract lives in
[`skills/career-memory/SKILL.md`](skills/career-memory/SKILL.md); anything that
changes what the agent records or claims should be argued for there first.

Run the test suite before opening a PR:

```bash
./tests/test_cli.sh
```

## License

MIT — see [LICENSE](LICENSE).
