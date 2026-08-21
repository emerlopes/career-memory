# Changelog

## 0.3.0 — 2026-08-20

Implements the v0.3 scope of [`docs/SPEC.md`](docs/SPEC.md): proactive memory —
the skill now notices when the record is falling behind, instead of waiting to
be asked.

- `summary` — the facts of a week or a month: entries, themes, recurring skills,
  people, evidence and impact coverage, and a comparison with the period before
  (a half-finished week is compared with the same half of the previous week, so
  Wednesday never reads as a decline). `table`, `markdown` and `json` output
- `gaps` — missing-evidence detection in six kinds: `no-evidence`, `no-impact`,
  `unverified-impact`, `stale-candidate`, `quiet-period` and
  `uncovered-competency` (a competency listed in `profile.md` that no entry
  mentions), each with the command that fixes it
- `checkup` — periodic review prompt: days since the last capture, this week
  against last week, weeks and months that hold entries but were never
  summarised, candidates still waiting, gap counts, and — with `--github` —
  GitHub activity that is not in the record yet
- Summaries live in `outputs/summaries/<2026-W33|2026-08>.md`; `checkup` reads
  that directory to know what is still due
- `career-weekly`, `career-monthly`, `career-checkup` and `career-gaps` slash
  commands, `references/proactive.md`, and weekly/monthly templates

Nothing here writes on its own, and no gap is ever filled by the agent: a gap is
a question to ask the user, and `Impact: not documented` remains a correct
answer.

## 0.2.0 — 2026-08-20

Implements the v0.2 scope of [`docs/SPEC.md`](docs/SPEC.md): GitHub as a source
of candidate evidence.

- `github check` — verify GitHub access; `gh` CLI by default, `$GITHUB_TOKEN`
  otherwise, `$GITHUB_API_URL` for GitHub Enterprise
- `github discover` — pull requests, issues, reviews and commits in a window,
  marked against what is already recorded
- `github import` — new signals become candidates (never confirmed entries),
  skipping references already in the store and suggesting a link when a signal
  matches an existing entry
- `github link` — attach a PR, issue, review or commit to an entry from a URL,
  `owner/repo#123` or `owner/repo@sha`, with the title resolved from GitHub
- `github_review` evidence type; GitHub evidence carries `url` and `title`
- `--evidence 'github_pr:https://…'` now keeps the URL whole
- `career-github` slash command and `references/github.md`

Discovery is read-only and local: nothing is written to GitHub, and no
discovered signal becomes career memory without the user promoting it.

## 0.1.0 — 2026-08-20

First release. Implements the v0.1 scope of [`docs/SPEC.md`](docs/SPEC.md).

- `career-memory` skill: capture, candidate detection, retrieval, brag
  documents, daily standup mode, plus performance review, promotion case,
  resume and interview-story generation
- `career_memory.py`: dependency-free CLI for the store — `init`, `add`,
  `update`, `list`, `search`, `show`, `promote`, `dismiss`, `stats`,
  `validate`, `where`
- Duplicate detection on `add`
- Nine slash commands (`career-init`, `career-add`, `career-daily`,
  `career-brag`, `career-review`, `career-promotion`, `career-resume`,
  `career-interview`, `career-search`)
- Templates for every generated document
- Distributed as a Claude Code plugin, installable from this repository
