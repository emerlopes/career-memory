# Changelog

## Unreleased

- GitHub Copilot support, verified end to end: the skill installs with
  `gh skill install --agent github-copilot`, validates against the Agent Skills
  specification (`gh skill publish --dry-run`), and runs unchanged on the CLI,
  in VS Code and in the coding agent
- The bootstrap in `SKILL.md` no longer assumes a Claude Code install. It now
  resolves `career_memory.py` from every directory the common hosts use —
  `$CLAUDE_PLUGIN_ROOT`, `~/.claude/skills`, `~/.copilot/skills`,
  `~/.agents/skills`, and the project-level `.github/skills`, `.claude/skills`
  and `.agents/skills`. Before this, an install anywhere but `~/.claude` left
  `$CM` empty and every command failed
- `docs/MANUAL.md` gains a [GitHub Copilot](docs/MANUAL.md#github-copilot)
  section: install scopes, which Copilot surfaces load skills, how to turn the
  16 slash commands into VS Code prompt files, and the one thing that genuinely
  differs — the cloud coding agent's ephemeral store

## 0.5.0 — 2026-08-26

Implements the v0.5 scope of [`docs/SPEC.md`](docs/SPEC.md): career
intelligence — the same entries read across quarters instead of days.

- `trends` — how the record evolves: entries, evidence and impact coverage for
  every month, quarter or year in the range (empty ones included), each
  competency's trajectory across those periods (`steady`, `new`, `intermittent`,
  `paused`), the themes where an impact was actually documented, and the earlier
  half of the range against the recent half. `table`, `markdown` and `json`
  output; `--bucket auto` picks the period size from the range length
- `promotion` — promotion-gap analysis over time: the criteria for a target
  level, each sorted into recorded repeatedly, thin in the record, or nothing in
  the record mentions it, with the entries behind them and notes for the shapes
  that matter — all in one project, nothing in the last six months, no evidence
  attached. Criteria come from `--criterion`, a `## Promotion criteria` heading
  in `profile.md` (a heading naming the role wins), or `## Competencies` as a
  labelled fallback. Entries matching no criterion are reported too
- `graph` — the evidence graph: projects, skills, tags and people that entries
  name together, with an edge wherever two share enough entries, plus the
  clusters they form. `table`, `mermaid` and `json` output
- `checkup` now names ladder criteria with nothing recorded — only when the user
  has written criteria into `profile.md`, so it stays silent for everyone else
- Longitudinal summaries live in `outputs/trends/<since>_<until>.md`;
  `profile.md` gained optional `## Target role` and `## Promotion criteria`
  sections; `career-trends` slash command, `references/intelligence.md` and a
  career-trends template

Two invariants hold this version together, because a table of quarters reads
like a measurement of a person and it is not one. A theme that fades has faded
from the *record* — the work may have continued unrecorded, and no output
narrates a decline. And coverage is never a verdict: `promotion` reports how the
record covers the criteria and refuses to conclude readiness in either
direction.

## 0.4.0 — 2026-08-26

Every interaction now starts from a known state, and the skill speaks the
user's language.

- `status` — one idempotent bootstrap that creates the store, subdirectories,
  `profile.md`, `README.md` and `config.json` when any are missing, then reports
  the settings and whether the profile is complete. The skill runs it before
  capturing, retrieving or generating anything, so there is no uninitialised
  state to handle and no reason to ask permission to set up. `--format json`
  for programmatic use.
- `config` — settings that persist in `config.json` in the store: `language`
  (`auto`/`pt`/`en`), `documents_language` (`same`/`pt`/`en`/`ask`) and
  `profile_gate` (`documents`/`all`/`remind`). Every value is validated; an
  unreadable config falls back to defaults with a warning rather than failing.
- An incomplete `profile.md` gates generated documents by default. Capture,
  search and dailies are never blocked — evidence mentioned in passing is lost
  if the skill stops to ask about job titles, while a review written without
  knowing the user's level reads generic because it is.
- Language governs replies, entry bodies and documents, never schema values, so
  a store stays portable across languages.
- New `/career-config`; `/career-init` now confirms the language settings.

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
