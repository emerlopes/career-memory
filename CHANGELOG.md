# Changelog

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
