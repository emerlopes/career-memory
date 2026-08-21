# Proactive memory

Capture only works if it happens. Left alone, everyone stops recording after two
weeks and rediscovers the store the night before a review — with a quarter
missing. This is the part of the skill that notices, at a moment when noticing
is useful, and says one useful sentence about it.

Three capabilities, one rule each:

| Capability          | Command             | The rule                                     |
| ------------------- | ------------------- | -------------------------------------------- |
| Periodic review     | `checkup`           | Offer once, then drop it                     |
| Weekly / monthly    | `summary`           | Report the record, not the week              |
| Missing evidence    | `gaps`              | Ask the user; never fill a gap yourself      |

## The nagging problem

The failure mode here is not missing a gap. It is becoming the tool that
interrupts. A skill that opens every session with "you have 6 unresolved gaps"
gets uninstalled, and then the user has no career memory at all.

So:

- **At most one proactive prompt per session**, and only when the user is not
  mid-task. If they asked you to debug a failing test, this can wait.
- **Offer, do not perform.** "Last week has 4 entries and no summary — want me
  to write it?" and then let it go. If they say nothing, drop it.
- **Never repeat a declined offer** in the same session. Once is a service,
  twice is nagging.
- **Say the number.** "3 entries from last week have no evidence" is worth
  interrupting for; "you should keep up your career memory" is not.

Good moments to raise it: when the user opens a session on a Monday, when they
ask for a daily, when they finish something and mention it, when they ask for
any generated document. Bad moments: mid-debugging, mid-incident, or right after
they told you something they wanted captured quietly.

## Checkup

```bash
python3 "$CM" checkup                  # summaries due, pending candidates, gaps
python3 "$CM" checkup --github         # also: GitHub activity not in the record
python3 "$CM" checkup --format json    # same facts, for your own reasoning
```

It reads and reports; it never writes. What it tells you:

- how long since the last capture, and this week's rate against last week's
- which finished weeks and months hold entries but were never summarised
- candidates that have been waiting (`--stale-days`, default 14)
- gap counts by kind over the last six months
- with `--github`, signals from the last week that are not linked anywhere

Turn that into **one line** for the user. Not a report:

> Your last capture was 11 days ago, and last week has 4 entries with no
> summary. Want me to write the weekly?

`--github` costs a network call and needs `gh` or a token; when it is
unavailable, `checkup` says so and carries on. Do not run it on every checkup —
use it when the user is asking about their work, not while they are working.

## Weekly and monthly summaries

```bash
python3 "$CM" summary                             # the current week, in progress
python3 "$CM" summary --window last-week --format markdown
python3 "$CM" summary --period month --format markdown
python3 "$CM" summary --from 2026-08-10 --to 2026-08-16 --format json
```

`summary` gives you the facts of a period: what was recorded, by type and
project, recurring skills and tags, who the user worked with, evidence and
impact coverage, how the period compares with the one before it, and which
candidates are still pending. A half-finished week is compared with the same
half of the previous week — otherwise every Wednesday looks like a decline.

Write the result to `outputs/summaries/<label>.md` — `2026-W33.md` for a week,
`2026-08.md` for a month. `summary` prints the exact path, and `checkup` looks
there to decide what is still missing, so keeping the name is what makes the
cadence work. Start from `templates/weekly-summary.md` or
`templates/monthly-summary.md`.

The one thing a summary must never become is a story about the week:

- **The store is not the week.** "Two entries this week" means two entries were
  recorded, not that the user did two things. Say it that way. When a period
  looks empty, suggest `github discover` for the same range before anyone
  concludes anything.
- **A drop is not a decline.** Fewer entries than last month is a fact about
  capture. It may mean a heavy on-call rotation, a holiday, or a long project
  with nothing shipped yet. Report the number; do not explain it for them.
- **No new claims.** A summary re-arranges recorded entries. If something is not
  in an entry, it is not in the summary.

A monthly summary is not twelve weekly summaries stapled together: group by
theme and project, name what carried across weeks, and keep it to something the
user can read in a minute. Both are inputs to the quarterly brag document — the
monthly especially, which is why an honest one beats a flattering one.

## Missing evidence

```bash
python3 "$CM" gaps                                   # last 6 months
python3 "$CM" gaps --window last-quarter --kind no-impact
python3 "$CM" gaps --format json --limit 5
```

Six kinds, each with a concrete fix:

| Kind                   | What it means                                             |
| ---------------------- | --------------------------------------------------------- |
| `no-evidence`          | An entry nobody could verify — no PR, doc, metric, ticket |
| `no-impact`            | Something happened; what it changed was never recorded    |
| `unverified-impact`    | Impact recorded as `inferred` or `uncertain`              |
| `stale-candidate`      | A candidate the user never confirmed or dismissed         |
| `quiet-period`         | Consecutive finished weeks with nothing recorded          |
| `uncovered-competency` | A competency in `profile.md` no entry mentions            |

Every one of them is a statement about the **record**, never about the work.
"No evidence attached" does not mean the work was unsubstantial; it means a
future reader has nothing to check. Word it that way to the user, because the
opposite reading is discouraging and false.

The gap list is a list of questions to ask, one at a time, at a moment when the
answer is easy to give:

> The retry-storm fix from Monday has no impact recorded. Did that stop the
> pages?

Then `update <id> --set-impact "…"` with what they actually said. If they do not
know, or there was no measurable outcome, leave it undocumented — an honest
`Impact: not documented` is the correct final state for plenty of entries, and
converting it into a guess is exactly the failure this skill exists to prevent.

Two gaps deserve care:

- **`quiet-period`** is the one that stings. Raise it as a recovery
  opportunity — "nothing recorded between June 22 and August 16; want me to
  check GitHub for that stretch?" — not as an accusation.
- **`uncovered-competency`** is a keyword search against `profile.md`, nothing
  more. It finds the competency the user claims and never evidences, which is
  the single most useful thing to know before a promotion conversation, but a
  miss can simply mean they word it differently in entries. Present it as
  "I could not find entries mentioning system design" — not as "you have not
  done system design".

## Automatic detection during normal work

Proactive memory is not only scheduled. Most evidence walks past in
conversation: the user mentions a fix, a review, a decision, a piece of
feedback, while asking you for something else entirely. `references/capture.md`
covers what to do with it. The proactive part is only this: notice it, name it
in one line, and let the user decide.

> That is the third time this month you have unblocked someone on auth. Worth
> recording as collaboration evidence?

Pattern observations like that are yours to offer, but they are interpretation —
say them as an observation about the entries, and let the user confirm before
any of it becomes a record.
