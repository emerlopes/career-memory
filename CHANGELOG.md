# Changelog

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
