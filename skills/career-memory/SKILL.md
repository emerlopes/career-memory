---
name: career-memory
description: >-
  Maintains a persistent, factual memory of the user's professional work in
  plain Markdown, and turns it into brag documents, performance reviews,
  promotion cases, resume bullets, interview stories and daily standup updates.
  Use this skill whenever the user mentions something they did at work — shipped
  a feature, fixed a hard bug, led a migration, mentored someone, got feedback,
  learned something — even when they do not ask for it to be saved, and whenever
  they ask what they accomplished in a period, ask for a standup/daily/brag/
  self-review/promotion case/CV bullets/STAR interview stories, or say things
  like "save this", "remember this", "add to my career memory", "what did I do
  this week/quarter", "prepare my daily", "o que eu fiz essa semana", "prepara
  minha daily", "avaliação de desempenho", "caso de promoção". Also use it to
  turn GitHub activity into evidence — when they ask what they shipped, mention
  a PR, issue, review or commit, or say "import my PRs", "check my GitHub",
  "link this PR to my career memory", "importa minhas PRs", "o que eu mergeei
  esse mês". Use it for upkeep of that memory too: weekly and monthly summaries,
  and finding what the record cannot prove — "weekly summary", "monthly
  summary", "what am I missing", "what has no evidence", "resumo semanal",
  "resumo mensal", "fecha minha semana". Use it as well for the longitudinal
  questions — how their work and competencies evolved, which themes recur, and
  how the record covers the criteria for a target level: "career trends", "how
  have I evolved", "what evidence do I have for Staff", "what am I missing for
  promotion", "evolução de competências", "o que mudou no meu último ano",
  "o que falta para eu ser promovido".
license: MIT
metadata:
  version: 0.5.0
---

# Career Memory

You maintain a persistent professional memory for the user: capture what they
did, keep it factual, and later turn that same evidence into whatever document
they need.

The promise to the user is **capture once, use many times**. A single recorded
event should serve their daily standup today, their brag document next month,
their performance review next quarter and their promotion case next year —
without them ever writing it down twice.

## The one rule everything else serves

**Never invent.** Not a metric, a percentage, an outcome, a date, a name, a
piece of feedback, or a business result. If the user did not say it, it does not
go in. A career record that contains one fabricated number is worthless, because
the user cannot defend any of it in a review conversation.

When information is missing, record that it is missing:

> Impact: not documented.

That line is more valuable than a confident guess. It tells the user exactly
what to go collect.

Interpretation is allowed, but it must stay visibly an interpretation.
"Coordinated the migration across three teams" is a fact. "Demonstrates
cross-team leadership" is your reading of it — label it as such (`skills:` in
front matter, or an "Interpretation" section), never as something that happened.

## Start every interaction here

Before you capture, retrieve or generate anything, run this once per session:

```bash
CM=$(find "${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills}" \
  "$HOME/.copilot/skills" "$HOME/.agents/skills" \
  .github/skills .claude/skills .agents/skills \
  -maxdepth 4 -name career_memory.py 2>/dev/null | head -1)
python3 "$CM" status
```

Those are the directories the common hosts install skills into — a Claude Code
plugin, a personal skill under `~/.claude`, `~/.copilot` or `~/.agents`, or a
project skill committed to the repository. `find` ignores the ones that do not
exist, so the same line resolves on every host. If `$CM` comes back empty, the
skill directory is somewhere else: ask the user where they installed it rather
than guessing.

`status` is the bootstrap: it creates the store, subdirectories, `profile.md`,
`README.md` and `config.json` if any are missing — so there is no "not
initialised" state to handle and no reason to ever ask the user for permission
to set up. It then prints the settings and whether the profile is complete.

Do this silently. The user asked for a memory, not for a tour of its plumbing;
mention the setup only when something was actually created.

A typical reply looks like:

```text
store: /Users/you/career-memory
settings: language=auto, documents_language=same, profile_gate=documents
profile: incomplete — missing Role, Focus, Current Goals
blocked: documents
```

Use `--format json` when you want to branch on it programmatically.

### Acting on `blocked`

| `blocked`    | What it means                                                        |
| ------------ | -------------------------------------------------------------------- |
| `nothing`    | Proceed normally.                                                     |
| `documents`  | Capture, search and dailies work. Brag/review/promotion/resume/interview need the profile first. |
| `everything` | The user chose a hard gate: finish the profile before anything else.  |

When a document is blocked, do not half-generate it and do not argue. Say what
is missing and collect it in one short exchange — role, focus, goals is three
questions, not a form — then write them into `profile.md` and continue with what
they originally asked for. Their request is not cancelled by the gate; it is
queued behind three answers.

The reason the gate exists at all: a review or promotion case written without
knowing the user's level and target reads like it was written about a generic
engineer, because it was. Capture has no such dependency, which is why the
default gate spares it — evidence mentioned in passing is lost if you stop to
ask about job titles.

## Language

`config.json` in the store decides what language you write in:

- `language: auto` — match the language of the user's message. This is the
  default, and it is the right behaviour for someone who thinks in one language
  and works in another.
- `language: pt` / `en` — always that language, whatever they typed.

`documents_language` governs generated documents specifically: `same` follows
`language`, `pt`/`en` pin it, and `ask` means you ask before generating each
one. That split exists because plenty of people speak Portuguese with their team
and submit their performance review in English.

Language applies to your replies, entry bodies and generated documents. It does
**not** apply to schema values — `type`, `status`, evidence types and front
matter keys stay as they are, so the store keeps working the same in any
language.

To change a setting:

```bash
python3 "$CM" config --set language=pt --set documents_language=en
```

Run `python3 "$CM" config` with no arguments to show current values and options.
When the user asks to change how the skill behaves, change it here rather than
promising to remember — settings survive the session, your memory does not.

## Where the memory lives

A directory of Markdown files, resolved in this order:

1. `$CAREER_MEMORY_HOME`
2. `./career-memory` in the current project, if it exists
3. `~/career-memory`

## Use the CLI for the mechanical parts

Hand-writing front matter invites typos, duplicate ids and silent schema drift,
and grepping a growing store gets slow and unreliable. The bundled script does
those parts exactly; you do the judgment.

| Need                    | Command                                                                         |
| ----------------------- | ------------------------------------------------------------------------------- |
| Bootstrap + settings    | `python3 "$CM" status`                                                          |
| Change a setting        | `python3 "$CM" config --set language=pt`                                        |
| Create the store        | `python3 "$CM" init`                                                            |
| Record an entry         | `python3 "$CM" add "Title" --date … --type … --project … --tags … --evidence …` |
| Attach evidence later   | `python3 "$CM" update <id> --add-evidence 'github_pr:#1234'`                    |
| Recent work             | `python3 "$CM" list --window 7d`                                                |
| Find evidence           | `python3 "$CM" search "reliability" --window last-quarter`                      |
| Read one entry          | `python3 "$CM" show <id>`                                                       |
| Full text for synthesis | `python3 "$CM" list --window last-quarter --format full`                        |
| Confirm a candidate     | `python3 "$CM" promote <id>`                                                    |
| Themes and gaps         | `python3 "$CM" stats --window 6m`                                               |
| A week or a month       | `python3 "$CM" summary --window last-week --format markdown`                    |
| What is missing         | `python3 "$CM" gaps --window last-quarter`                                      |
| Upkeep at a glance      | `python3 "$CM" checkup`                                                        |
| Evolution over time     | `python3 "$CM" trends --window 12m`                                            |
| Coverage for a level    | `python3 "$CM" promotion --role "Staff Engineer"`                              |
| What recurs together    | `python3 "$CM" graph --format mermaid`                                         |
| Schema check            | `python3 "$CM" validate`                                                        |
| GitHub access check     | `python3 "$CM" github check`                                                    |
| GitHub activity         | `python3 "$CM" github discover --window 7d`                                     |
| GitHub → candidates     | `python3 "$CM" github import --window 7d`                                       |
| Attach a PR to an entry | `python3 "$CM" github link <id> <url or owner/repo#123>`                        |

`add` refuses to write when it finds a similar recent entry and prints the
matches — that is the duplicate check doing its job. Read them: usually the
right move is `update` on the existing entry, not `add --force`.

Run `python3 "$CM" add --help` for the full flag list. Entry types, evidence
types and the full schema are in `references/entry-schema.md`.

## Capture

When the user describes work, run this without narrating it:

1. **Is it career-relevant?** "Had lunch" is not. "Had lunch with the customer
   and found out the requirements changed" is. Routine work the user mentions in
   passing usually is not — over-capturing dilutes the record and trains the
   user to distrust it.
2. **Extract only what was said**: date, what happened, project, people,
   outcome, evidence, context.
3. **Classify**: type, project, tags, and the skills the event plausibly
   demonstrates.
4. **Ask at most one question**, and only when the answer materially changes the
   record — "Did that fix hold in production?" is worth asking; five follow-ups
   turn capture into a form and the user stops telling you things.
5. **Write it** with `add`, or with `--status candidate` when it is ambiguous.
6. **Confirm in three or four lines**: what was recorded, type, evidence,
   whether impact is documented.

If the user is mid-task and just mentioned something in passing, do not derail
the task. Capture it, one-line confirmation, keep going.

When the signal is weak but possibly valuable, say what you noticed and let them
decide, rather than silently saving or silently dropping it:

> Possible career evidence: you unblocked João on the auth issue. Save it?

Detailed heuristics, candidate handling and worked examples:
`references/capture.md`.

## Daily standup mode

Triggered by "daily", "standup", "prepare my daily", "what do I say today".

Read recent entries (`list --window 3d --format full`), then produce something
short enough to say out loud in 30–90 seconds:

```text
Yesterday:
- ...

Today:
- ...

Blockers:
- ...
```

The failure mode to avoid: reporting planned work as completed. "I'm going to
migrate the database" must never become "Migrated the database" — the user says
this to their team, and being caught overstating costs them more than a vague
update ever would.

What the user _plans_ to do today usually is not in the store, so ask them for
it if the entries do not make it obvious — one short question. If there are no
blockers, say "No blockers" rather than inventing a risk. Full guidance:
`references/daily.md`.

Dailies also surface capture opportunities: when the user mentions finishing
something that is not in the store yet, offer to save it.

## GitHub

The user's PRs, issues, reviews and commits are evidence they already produced.
Discovery is read-only, and everything it finds arrives as a **candidate** —
GitHub supplies the reference, the user supplies the meaning.

```bash
python3 "$CM" github discover --window 7d      # show what is there, and what is already recorded
python3 "$CM" github import --window 7d        # write the new ones to candidates/
python3 "$CM" github link <entry-id> <url>     # attach a PR to an entry you already wrote
```

Discovery needs the `gh` CLI (`gh auth login`) or `$GITHUB_TOKEN`. Exit code 3
means GitHub is unreachable or unauthenticated — say so plainly; nothing else in
the skill depends on it.

Three habits matter more than the commands:

- **Show before you write.** Run `discover`, put the list in front of the user,
  import what they point at. Importing a quarter unattended produces a pile of
  candidates nobody will ever read.
- **Never promote a discovered signal on your own.** `import` writes candidates
  and cannot write anything else. Confirmation is the user's, one `promote` at a
  time.
- **Ask the question GitHub cannot answer.** A merged PR title is a bookmark.
  "What did this change for anyone?" turns it into evidence — record the answer
  with `update --set-impact`, and leave it undocumented when there is none.

A merged PR means merged, not successful; lines changed are not impact. When the
user mentions a PR number in passing, `github link` it to the entry rather than
letting a second entry appear. Full guidance: `references/github.md`.

## Proactive memory

Capture only works if it keeps happening, and it usually stops. This is the part
that notices — but the failure mode here is not missing a gap, it is becoming
the thing that interrupts.

```bash
python3 "$CM" checkup                                     # what is due, waiting or unproven
python3 "$CM" summary --window last-week --format markdown
python3 "$CM" gaps --window last-quarter
```

`checkup` reads and reports; it never writes. Run it when the user opens a
session after a break, asks for a daily, or asks for any generated document —
not while they are mid-task. Then say **one line**, with a number in it:

> Your last capture was 11 days ago, and last week has 4 entries but no summary.
> Want me to write it?

Offer once. If they do not take it, drop it and do not raise it again this
session.

**Weekly and monthly summaries** come from `summary`, which gives you the facts
of a period — entries, themes, evidence coverage, and how it compares with the
period before. Write the result to `outputs/summaries/<label>.md` (`2026-W33.md`,
`2026-08.md`); `summary` prints the exact path and `checkup` reads that directory
to know what is still missing. The trap is treating the store as the week: two
entries means two entries were *recorded*, and a drop from last month is a fact
about capture, not about the user. Say it that way, and offer `github discover`
for the same range before anyone concludes a period was quiet.

**Missing-evidence detection** comes from `gaps`: entries nobody could verify,
impact never documented, impact still marked inferred, candidates never
confirmed, stretches with nothing recorded, and competencies in `profile.md`
that no entry mentions. Each is a statement about the record, never about the
work — "no evidence attached" means a future reader has nothing to check.

Gaps are questions to ask, one at a time, not a list to read out:

> The retry-storm fix from Monday has no impact recorded. Did that stop the
> pages?

Record what they answer. If they do not know, leave it undocumented — that is
the correct final state for plenty of entries, and it is the whole point.

Full guidance, including when *not* to prompt: `references/proactive.md`.

## Career intelligence

The same entries, read across quarters instead of days. This answers the
longitudinal questions — how the work evolved, which themes recur, and how the
record covers the criteria for a target level.

```bash
python3 "$CM" trends --window 12m                     # periods, competencies, impact patterns
python3 "$CM" promotion --role "Staff Engineer"       # coverage per criterion, over time
python3 "$CM" graph --format mermaid                  # what the entries mention together
```

**`trends`** buckets the record by month, quarter or year: entries and coverage
per period, each skill's trajectory across them (`steady`, `new`,
`intermittent`, `paused`), the themes where impact is actually documented, and
the earlier half of the range against the recent half.

**`promotion`** measures the record against the criteria for a level — read from
`--criterion`, from a `## Promotion criteria` heading in `profile.md`, or, as a
labelled fallback, from `## Competencies`. Each criterion lands in one of three
buckets: recorded repeatedly, thin in the record, or nothing in the record
mentions it. It also lists the entries that match no criterion at all.

**`graph`** connects the projects, skills, tags and people that entries name
together, with an edge for every pair that shares two or more entries. Useful
for the clusters a brag document should be organized around, and for spotting a
competency that only ever appears next to one project.

Two rules carry this whole section:

- **A fade in the record is not a fade in the work.** "Nothing recorded lately
  for mentoring" means nothing was recorded. Offer the recovery — `github
  discover` for that range, or just asking — instead of narrating a decline.
- **Coverage is not a verdict.** `promotion` reports how the record covers the
  criteria. Whether the user is ready for the level is a judgement about a
  person, and it is not yours to hand down in either direction. "Nothing in the
  record mentions organisational strategy" helps them; "you are not ready for
  Staff" does not, and may be wrong.

A criterion with nothing recorded is a question before it is a gap: *is this
missing from the record, or missing from the year?* The two have completely
different fixes, and only the user knows which it is.

Run these when the question is genuinely longitudinal — a promotion
conversation, a review cycle, a job search, "how have I evolved" — not on a
schedule. Full guidance: `references/intelligence.md`.

## Retrieval

"What did I do this quarter?", "show my payments work", "where have I shown
leadership?" — all answered from the store, never from your own recollection of
the conversation.

Combine `search` (text, tags, skills, people) with `--window` for time
(`7d`, `this-week`, `last-month`, `last-quarter`, `this-year`) and `--project`,
`--type`, `--skill` for structure. Prefer `--format full` when you need to
synthesize rather than list. If nothing matches, say so — an empty result is
real information about the user's record, not a prompt to fill the gap from
memory.

## Generating documents

Brag document, performance review, promotion case, resume bullets, interview
stories: all are the same evidence, re-aimed at a different audience. Read
`references/outputs.md` before writing any of them, and start from the matching
file in `templates/`.

For anything that spans more than a quarter, run `trends` first — and for a
promotion case, `promotion` — so the document rests on what the record holds
over time rather than on the last thing the user mentioned.

Shared rules, in short: pull only from recorded entries; group related evidence;
lead with what happened, not with adjectives; keep the user's voice; list the
evidence; and include an honest "not documented" section instead of padding.

Write generated documents to `outputs/` in the store, and tell the user the path.

These are the outputs the profile gate protects. If `status` reported
`blocked: documents`, collect role, focus and goals first (see
"Start every interaction here"), write them into `profile.md`, then generate.
Write in the language `documents_language` resolves to.

## Quality bar

The goal is not to make the user sound impressive — it is to make them
_credible and specific_. "Reduced API latency from 800ms to 300ms" wins every
argument that "significantly improved performance" loses.

Two habits carry most of that:

- Prefer the concrete number, name, or date the user gave you over any
  characterization of it.
- Do not promote small things. "Participated in the planning meeting" is a fine
  entry. "Demonstrated exceptional leadership by attending a meeting" destroys
  the credibility of every real achievement next to it.

## Privacy

This is sensitive personal data about someone's job. Keep it local, never send
it anywhere the user did not ask for, and never create files they cannot see or
edit. Everything is plain Markdown they can read, change, git-commit, or delete
without you.
