# Career Memory — for agents

This repository packages one agent skill. The behavioral contract lives in
[`skills/career-memory/SKILL.md`](skills/career-memory/SKILL.md) — read that
first; everything else supports it.

```text
skills/career-memory/
├── SKILL.md          the contract: capture, retrieval, daily mode, outputs
├── references/       loaded on demand
│   ├── entry-schema.md   entry format, types, evidence types, confidence
│   ├── capture.md        what to record, candidates, duplicates, examples
│   ├── daily.md          standup mode
│   ├── github.md         discovery, import as candidates, evidence linking
│   ├── proactive.md      summaries, missing evidence, when not to prompt
│   └── outputs.md        brag, review, promotion, resume, interview
├── templates/        starting points for generated documents
└── scripts/
    ├── career_memory.py  the store: create, update, search, validate
    └── career_github.py  read-only GitHub discovery (gh CLI or a token)
```

The skill is agent-agnostic by design: Markdown instructions plus one
standard-library Python script. Nothing depends on a particular provider, and
the user's data is plain Markdown in a directory they own.

`tests/test_cli.sh` covers both scripts; GitHub discovery is exercised offline
through `tests/fake-gh.sh`, which answers from `tests/fixtures/github/`.

If you are working *on* this repository rather than using the skill: the
non-negotiable property is that the skill never fabricates career evidence.
Any change that makes it easier for the agent to state something the user did
not is a regression, however good the output looks. Two corollaries in the
GitHub code: discovered signals are written as candidates and nothing else, and
GitHub metadata is never read as impact.

The v0.3 commands (`summary`, `gaps`, `checkup`) report on the *record*, never
on the work — "no evidence attached" is a fact about a file. Keep that framing
in any wording change: the inverse reading is both discouraging and false, and
a gap the agent fills in for the user is the same regression as an invented
metric.
