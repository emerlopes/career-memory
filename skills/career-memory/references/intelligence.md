# Career intelligence

The first four versions answered "what happened?". This one answers "what has
been happening?" — the same entries, read across quarters instead of days.

Three commands, one rule each:

| Capability            | Command      | The rule                                        |
| --------------------- | ------------ | ----------------------------------------------- |
| Trends over time      | `trends`     | A fade in the record is not a fade in the work   |
| Promotion-gap analysis| `promotion`  | Coverage, never a verdict                       |
| Evidence graph        | `graph`      | An edge is a co-mention, not a relationship      |

Everything here is longitudinal arithmetic over recorded entries. That makes it
the most dangerous part of the skill, because a table of quarters looks like a
measurement of a person. It is not. It measures the record.

## Trends

```bash
python3 "$CM" trends                                  # last 12 months
python3 "$CM" trends --window 2y --bucket quarter
python3 "$CM" trends --project payments
python3 "$CM" trends --window 18m --format markdown   # the longitudinal document
python3 "$CM" trends --format json                    # for your own reasoning
```

What it gives you:

- **Period by period** — entries, evidence coverage, impact coverage and
  projects, for every month/quarter/year in the range, empty ones included.
  Empty periods are the point: a competency that disappears for two quarters
  only shows up if those quarters are still columns.
- **Competency evolution** — each skill across the periods, with a trajectory:
  `steady`, `new`, `intermittent`, `paused`. Below three periods, or on a single
  entry, no trajectory is claimed at all.
- **Recurring impact patterns** — the themes that repeat, and how often an
  impact was actually written down. `6/9 reliability` says nine entries carry
  that tag and six of them say what changed. That ratio is the difference
  between a promotion case and a list of tasks.
- **Halves** — the earlier half of the range against the recent half, in
  entries, evidence and impact.

`--bucket` defaults to `auto`: months up to about a year, quarters up to four,
years beyond. Override it when the user asks for a specific grain.

The trap, and it is the same one as weekly summaries, only larger:

- **A fade is a fade in the record.** "Nothing recorded lately for: mentoring"
  means nothing was recorded. The user may have mentored someone every week and
  told no one. Offer the recovery — `github discover` for the range, or simply
  asking — instead of narrating a decline.
- **Trajectories are interpretation.** So are skills, which are your reading of
  an entry in the first place. Two layers of interpretation stacked on each
  other deserve the label, every time.
- **Do not editorialise the curve.** Report "12 entries in Q1, 4 in Q2". Do not
  explain it. On-call rotations, parental leave, a long project with nothing
  shipped and a bad month all produce the same shape, and the user knows which
  one it was.

Write the markdown output to `outputs/trends/<since>_<until>.md` — the path the
command prints. Start from `templates/career-trends.md`.

## Promotion-gap analysis

```bash
python3 "$CM" promotion                                   # target role from profile.md
python3 "$CM" promotion --role "Staff Engineer" --window 18m
python3 "$CM" promotion --criterion "Technical leadership: mentoring, RFC"
python3 "$CM" promotion --format markdown
```

It takes the criteria for a level and reports, per criterion: how many entries
mention it, across how many periods, first and last, evidence and impact
coverage, which projects, and what is notable — all in one project, nothing in
the last six months, no evidence attached anywhere.

Each criterion lands in one of three buckets:

| Bucket                            | What it means                                        |
| --------------------------------- | ---------------------------------------------------- |
| `recorded repeatedly`             | Enough entries, spread over more than one period      |
| `thin in the record`              | Below `--min-entries` (3), or confined to one period  |
| `nothing in the record mentions it` | No entry in the range matches it                    |

Criteria come from, in order: `--criterion`, a `## Promotion criteria` heading
in `profile.md` (a heading that names the role wins — one profile can hold more
than one ladder), and finally `## Competencies` as a fallback. The output says
which, and the fallback says so explicitly, because competencies are what the
user claims and a ladder is what the company asks for. When the user's company
publishes a ladder, getting it into `profile.md` is the single highest-value
thing to do before a promotion conversation:

```markdown
## Promotion criteria — Staff Engineer

- Technical leadership: mentoring, migration, RFC
- Organisational impact: cross-team, roadmap
- System design: architecture, design doc
```

The words after the colon are what the matcher looks for in entries, on top of
the criterion name itself. They matter: a ladder says "drives organisational
impact" and entries say "coordinated three teams", and nothing links the two
unless somebody writes the words down.

Two things this command must never become:

- **A verdict.** It says how the record covers the criteria. Whether the user is
  ready is a judgement about a person, made by people who know the context, and
  it is not yours to hand down — in either direction. "Nothing in the record
  mentions organisational strategy" is useful. "You are not ready for Staff" is
  not, and it may be flatly wrong.
- **A to-do list of things to go do.** A criterion with nothing recorded is
  first a question: *is this missing from the record, or missing from the year?*
  Ask it that way. If it is missing from the record, the fix is capture, and
  `github discover` over the same range often recovers most of it.

The "entries matching no criterion" section is worth reading out loud. It is
either work the ladder does not describe — genuinely useful to know — or a
vocabulary mismatch between the ladder and the way the user writes entries.

## Evidence graph

```bash
python3 "$CM" graph                                     # projects, skills, people
python3 "$CM" graph --nodes project,skill,tag,person
python3 "$CM" graph --min-weight 3 --format mermaid     # paste into a document
```

Nodes are the things entries name — projects, skills, tags, people. An edge
means *N entries mention both*, nothing more. What it is good for:

- finding the clusters the user's work actually falls into, which is how a brag
  document gets its sections;
- seeing which people recur across which projects;
- spotting a skill that only ever appears next to one project, which is exactly
  the "all in one project" weakness a promotion committee asks about.

`--format mermaid` prints a diagram that renders anywhere Mermaid does, which
makes it a reasonable figure in a brag document. Keep `--min-weight` at 2 or
higher; at 1 every entry becomes its own little star and the picture says
nothing.

Say what an edge is when you show one. "Ana and payments appear together in four
entries" is a fact. "Ana is your main collaborator on payments" is a guess about
a working relationship built on four Markdown files.

## When to run any of this

Not on a schedule, and not while the user is mid-task. These commands are for
the moments when the question is genuinely longitudinal:

- the user asks what changed over the last year, or how their work has evolved;
- they are preparing a promotion conversation, a performance review, or a job
  search;
- they ask what evidence they have for a specific level;
- `checkup` reported ladder criteria with nothing recorded — which it only does
  when the user has written criteria into `profile.md`.

One prompt, with a number in it, and then let it go. The proactive rules in
`references/proactive.md` apply here unchanged, and the temptation to run a
twelve-month analysis unprompted is stronger, because the output looks
impressive. It is still an interruption.

## Feeding the documents

`trends` and `promotion` are inputs to the documents in `references/outputs.md`,
not replacements for them:

- **Promotion case** — run `promotion` first. Its three buckets map directly
  onto the template's "Demonstrated strengths" and "Gaps / thin evidence"
  sections, and its per-criterion entry lists are the evidence to quote.
- **Brag document** — `trends` supplies the themes and the honest sentence about
  frequency ("cross-team coordination appears in 12 entries over three
  quarters"), and `graph --format mermaid` can supply the picture.
- **Performance review** — the halves comparison and the impact-coverage ratio
  are the two numbers a review can carry without overclaiming.

In all three: the numbers describe the record, the entries carry the claims, and
anything the record does not hold stays out.
