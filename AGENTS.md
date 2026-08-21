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
│   └── outputs.md        brag, review, promotion, resume, interview
├── templates/        starting points for generated documents
└── scripts/
    └── career_memory.py  the store: create, update, search, validate
```

The skill is agent-agnostic by design: Markdown instructions plus one
standard-library Python script. Nothing depends on a particular provider, and
the user's data is plain Markdown in a directory they own.

If you are working *on* this repository rather than using the skill: the
non-negotiable property is that the skill never fabricates career evidence.
Any change that makes it easier for the agent to state something the user did
not is a regression, however good the output looks.
