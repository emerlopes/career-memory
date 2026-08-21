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
  esse mês".
license: MIT
metadata:
  version: 0.2.0
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

## Where the memory lives

A directory of Markdown files, resolved in this order:

1. `$CAREER_MEMORY_HOME`
2. `./career-memory` in the current project, if it exists
3. `~/career-memory`

Resolve the CLI path once per session and reuse it:

```bash
CM=$(find "${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/career-memory}" -maxdepth 4 -name career_memory.py 2>/dev/null | head -1)
python3 "$CM" where
```

If `where` reports the store is not initialised, run `python3 "$CM" init` and
tell the user where it landed. On first setup, offer to fill in `profile.md`
(role, focus, goals) — it costs one question and improves every document you
generate later. Do not block capture on it.

## Use the CLI for the mechanical parts

Hand-writing front matter invites typos, duplicate ids and silent schema drift,
and grepping a growing store gets slow and unreliable. The bundled script does
those parts exactly; you do the judgment.

| Need                    | Command                                                                         |
| ----------------------- | ------------------------------------------------------------------------------- |
| Create the store        | `python3 "$CM" init`                                                            |
| Record an entry         | `python3 "$CM" add "Title" --date … --type … --project … --tags … --evidence …` |
| Attach evidence later   | `python3 "$CM" update <id> --add-evidence 'github_pr:#1234'`                    |
| Recent work             | `python3 "$CM" list --window 7d`                                                |
| Find evidence           | `python3 "$CM" search "reliability" --window last-quarter`                      |
| Read one entry          | `python3 "$CM" show <id>`                                                       |
| Full text for synthesis | `python3 "$CM" list --window last-quarter --format full`                        |
| Confirm a candidate     | `python3 "$CM" promote <id>`                                                    |
| Themes and gaps         | `python3 "$CM" stats --window 6m`                                               |
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

Shared rules, in short: pull only from recorded entries; group related evidence;
lead with what happened, not with adjectives; keep the user's voice; list the
evidence; and include an honest "not documented" section instead of padding.

Write generated documents to `outputs/` in the store, and tell the user the path.

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
