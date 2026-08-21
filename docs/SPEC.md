# Career Memory Skill

**Version:** 0.1
**Status:** Draft Specification
**Type:** Agent Skill
**Primary goal:** Maintain a persistent, factual memory of a person's professional work and transform that memory into useful career artifacts.

---

# 1. Overview

Career Memory is an agent skill designed to help professionals continuously capture, organize, retrieve, and communicate what they do at work.

The skill acts as a **professional memory layer**.

Instead of asking the user to periodically remember everything they accomplished, the skill captures small pieces of information throughout the user's normal workflow and turns them into structured career evidence.

The system can later use this information to generate:

- brag documents;
- performance reviews;
- promotion cases;
- CV/resume bullets;
- interview stories;
- career summaries;
- competency evidence;
- project summaries;
- daily standup/daily updates.

The core principle is:

> **Your career should have a memory.**

The skill is not primarily a note-taking system and is not primarily a document generator.

It is a system for creating a persistent relationship between:

**Work → Evidence → Memory → Narrative**

---

# 2. Problem

Professionals frequently forget or lose evidence of their work.

Important events are distributed across:

- GitHub;
- pull requests;
- commits;
- issues;
- Slack;
- Teams;
- email;
- documents;
- project management tools;
- meetings;
- personal notes;
- conversations;
- and memory.

As time passes, it becomes difficult to answer questions such as:

- What did I accomplish this quarter?
- What impact did I have this year?
- What were my biggest technical contributions?
- When did I demonstrate leadership?
- What evidence do I have for a promotion?
- What did I learn?
- What problems did I solve?
- What feedback did I receive?
- What did I actually do last week?
- What should I say in today's daily?

Career Memory solves this by maintaining a structured, continuously updated professional memory.

---

# 3. Goals

## 3.1 Primary goals

The skill must:

1. Capture career-relevant events.
2. Preserve factual information.
3. Distinguish facts from interpretations.
4. Organize entries into a searchable professional history.
5. Retrieve historical evidence.
6. Generate career narratives from recorded evidence.
7. Generate concise daily updates.
8. Work with multiple AI coding agents.
9. Keep user data portable and human-readable.
10. Minimize the effort required from the user.

---

# 4. Non-goals

Version 0.1 does not attempt to:

- replace a full HR system;
- automatically evaluate employee performance;
- determine whether someone deserves a promotion;
- fabricate achievements;
- automatically infer business impact without evidence;
- become a task-management system;
- become a project-management system;
- require a hosted database;
- require a specific AI provider;
- require Telegram;
- require GitHub;
- require an external SaaS backend.

---

# 5. Product Philosophy

## 5.1 Low friction

The user should be able to write naturally.

Examples:

> "Finally fixed that payment race condition."

> "Spent most of the morning helping João with the auth issue."

> "Customer loved the new dashboard."

> "We decided to drop the old architecture."

The skill should interpret these statements instead of forcing the user into a form.

---

## 5.2 Facts over fiction

The skill must never invent:

- metrics;
- business outcomes;
- customer feedback;
- dates;
- people;
- project names;
- percentages;
- financial results;
- performance improvements;
- promotion evidence.

If information is missing, it must remain missing.

Bad:

> "The fix improved system reliability by 30%."

when the user never provided that metric.

Good:

> "The fix addressed an intermittent payment-processing issue."

---

## 5.3 Evidence over adjectives

Prefer:

> "Reduced API response time from 800ms to 300ms."

over:

> "Significantly improved API performance."

Prefer:

> "Led the migration of 4 services."

over:

> "Successfully led an important migration."

---

## 5.4 Interpretation is allowed, but must remain interpretation

The skill may identify possible competencies or implications.

For example:

**Fact:**

> "I coordinated the migration across three teams."

**Possible interpretation:**

> Leadership, cross-team coordination, ownership.

The interpretation must not be presented as a factual event.

---

# 6. Core Concepts

Career Memory has five fundamental concepts:

1. **Entry**
2. **Evidence**
3. **Candidate**
4. **Context**
5. **Output**

---

# 7. Entry

An Entry is a confirmed piece of professional memory.

Example:

```markdown
---
id: 2026-08-20-payment-race-condition
date: 2026-08-20
type: problem-solving
project: payments
status: confirmed
tags:
  - debugging
  - reliability
  - ownership
---

# Resolved payment race condition

Identified and fixed a race condition in the payment processing system.

## Impact

Not documented.

## Evidence

- GitHub PR #1234

## Context

The issue was intermittent and difficult to reproduce.

## Skills

- debugging
- technical problem solving
- ownership
```

Entries must be human-readable Markdown.

---

# 8. Candidate

Not every observation should immediately become permanent career memory.

The skill may identify a **candidate**.

Example:

> "I spent the morning helping João debug authentication."

The skill may respond:

> Possible career evidence detected:
>
> **Collaboration:** helped João investigate an authentication issue.
>
> Save this to your career memory?

A candidate can become:

```text
candidate → confirmed
candidate → dismissed
candidate → edited → confirmed
```

This prevents the memory from becoming polluted with irrelevant information.

---

# 9. Entry Types

Version 0.1 defines the following types:

```text
achievement
delivery
impact
problem-solving
feedback
learning
leadership
collaboration
```

The user does not need to explicitly select a type.

The agent should infer the most appropriate type.

An entry can have multiple tags and inferred competencies.

---

# 10. Entry Schema

The canonical entry schema is:

```yaml
---
id: unique-entry-id
date: YYYY-MM-DD
type: achievement
project: optional-project
status: confirmed
tags:
  - tag
skills:
  - skill
people:
  - person
evidence:
  - type: github_pr
    reference: "#123"
impact:
  statement: optional
  confidence: factual
context: optional
source: optional
---
```

The body contains the human-readable narrative.

---

# 11. Evidence

Evidence is a reference supporting an entry.

Possible evidence types include:

```text
github_pr
github_issue
github_commit
document
metric
dashboard
feedback
email
slack_message
meeting
ticket
external_link
```

Version 0.1 does not require automatic integration with these systems.

The schema must nevertheless support them.

Example:

```yaml
evidence:
  - type: github_pr
    reference: "#1234"

  - type: metric
    reference: "API latency dashboard"
    value: "800ms → 300ms"
```

---

# 12. Evidence Rules

The skill should prefer evidence that is:

1. specific;
2. attributable;
3. measurable;
4. traceable;
5. reproducible.

When generating a career artifact, evidence should be surfaced when available.

---

# 13. Confidence

Information may have different confidence levels.

Recommended values:

```text
factual
inferred
uncertain
```

### factual

Directly stated or explicitly supported.

### inferred

Reasonable interpretation derived from factual information.

### uncertain

Information that requires confirmation.

The skill must not silently convert inferred information into factual information.

---

# 14. Storage

Version 0.1 is local-first.

Recommended structure:

```text
career-memory/
├── README.md
├── profile.md
├── entries/
│   ├── 2026-08-20-payment-race-condition.md
│   ├── 2026-08-18-client-meeting.md
│   └── ...
├── projects/
│   ├── payments.md
│   └── authentication.md
├── feedback/
│   └── 2026-08-15.md
├── candidates/
│   └── ...
└── outputs/
    ├── brag.md
    ├── performance-review.md
    ├── promotion-case.md
    └── daily.md
```

The storage format should be:

- plain text;
- Markdown;
- version-control friendly;
- human-readable;
- portable;
- editable without the agent.

---

# 15. profile.md

The profile file contains relatively stable career context.

Example:

```markdown
# Career Profile

## Role

Senior Software Engineer

## Focus

Backend systems, distributed systems, technical leadership

## Current Goals

- Grow toward Staff Engineer
- Improve technical leadership
- Increase cross-team impact

## Competencies

- system design
- backend engineering
- technical leadership
- mentoring
```

The profile must not be treated as evidence.

It provides context for interpreting and generating outputs.

---

# 16. Capture Workflow

When the user describes something related to work, the skill should follow this workflow.

## Step 1 — Detect relevance

Determine whether the information could represent career-relevant evidence.

Not every work activity deserves an entry.

For example:

> "Had lunch."

should not be recorded.

But:

> "Had lunch with the customer and discovered a major requirement change."

may be relevant.

---

## Step 2 — Extract facts

Extract:

- date;
- event;
- project;
- people;
- outcome;
- impact;
- evidence;
- context.

Only information actually available should be populated.

---

## Step 3 — Classify

Determine:

- type;
- tags;
- potential skills;
- project.

---

## Step 4 — Identify missing high-value information

Do not interrogate the user.

Ask at most one clarification question when the answer materially improves the record.

Example:

> "Did the fix actually resolve the production issue?"

rather than asking five separate questions.

---

## Step 5 — Persist

Create or update the corresponding Entry.

---

## Step 6 — Confirm

Provide a concise confirmation.

Example:

> **Recorded**
>
> Fixed intermittent payment-processing race condition.
>
> Type: Problem solving
> Evidence: PR #1234
> Impact: not documented

---

# 17. Duplicate Detection

Before creating a new entry, the skill should check whether a similar event already exists.

If it finds a likely duplicate:

> I found a similar entry from August 18. Should I update it instead of creating a new one?

The skill should prefer updating an existing entry over creating duplicates.

---

# 18. Daily Summary Mode

## 18.1 Purpose

Daily Summary Mode is a dedicated capability for professionals who need to communicate their work during daily standups or similar recurring meetings.

The purpose is **not** to produce a complete career record.

The purpose is to produce a short, natural, spoken summary of:

1. what happened recently;
2. what is happening now;
3. what matters next;
4. blockers or risks, when relevant.

---

# 19. Daily Summary Input

The user may say:

> "Daily"

or:

> "Prepare my daily."

or:

> "What should I say in today's standup?"

The skill should retrieve relevant recent Career Memory entries and construct a concise summary.

---

# 20. Daily Time Window

By default, Daily Summary Mode should consider:

### Yesterday

Work completed, problems solved, decisions made, relevant collaboration, important discoveries.

### Today

Current work, active initiatives, planned work, continuation of previous work.

### Blockers

Only include blockers that are relevant to the daily.

### Optional

Important context that the team should know.

---

# 21. Daily Summary Format

The canonical output should be:

```text
Yesterday:
- ...

Today:
- ...

Blockers:
- ...
```

The output should be concise enough to be spoken naturally.

---

# 22. Daily Summary Example

Suppose the memory contains:

```text
Yesterday:
- Fixed payment race condition.
- Reviewed João's authentication PR.
- Investigated API latency.

Today:
- Continue payment reliability work.
- Start database migration.

No blockers.
```

The generated daily could be:

> **Yesterday:** I fixed the race condition in the payment flow and helped review the authentication work. I also investigated the API latency issue.
>
> **Today:** I'll continue the payment reliability work and start the database migration.
>
> **Blockers:** No blockers at the moment.

---

# 23. Daily Summary Principles

The daily mode must:

- prioritize important work;
- remove unnecessary detail;
- avoid reading the entire career history;
- avoid inventing tasks;
- avoid exaggerating impact;
- sound natural when spoken;
- be concise;
- preserve uncertainty;
- mention blockers only when relevant.

The output should generally fit within approximately **30–90 seconds of spoken communication**, unless the user requests more detail.

---

# 24. Daily Summary vs Career Memory

These are intentionally different.

### Career Memory

Optimized for:

> "What did I accomplish?"

It preserves detailed evidence.

### Daily Summary

Optimized for:

> "What should I tell my team?"

It compresses recent information into a conversational update.

The Daily Summary should **read from Career Memory but should not replace it**.

---

# 25. Daily Capture

Daily Summary Mode can also identify missing information.

Example:

> "I finished the migration yesterday."

The skill may recognize this as potentially valuable career evidence and ask:

> "Do you want me to save the migration completion as a career entry too?"

This creates a useful relationship:

```text
Daily activity
      ↓
Career candidate
      ↓
Career memory
      ↓
Future career outputs
```

---

# 26. Daily Mode and Current Work

The skill must distinguish:

### Completed

What happened yesterday or previously.

### In progress

What is currently being worked on.

### Planned

What the user intends to work on.

These must not be conflated.

For example:

> "I'm planning to migrate the database."

must not become:

> "Migrated the database."

---

# 27. Natural Language Interface

The skill should understand natural requests.

Examples:

```text
"Save this."
"Add this to my career memory."
"Remember this achievement."
"Record this."
"Did I already mention this?"
"What did I do this week?"
"What were my biggest wins this month?"
"Show my impact on the payments project."
"Generate my brag document."
"Prepare my performance review."
"What evidence do I have for leadership?"
"Prepare my daily."
"What should I say in today's standup?"
"Summarize yesterday and today."
```

---

# 28. Canonical Commands

For consistency, implementations may expose:

```text
career add
career list
career search
career brag
career review
career promotion
career daily
career profile
```

Natural-language interaction remains preferred.

---

# 29. Brag Document

The Brag Document is an output generated from Career Memory.

It should:

- summarize meaningful achievements;
- group related evidence;
- emphasize impact;
- identify patterns;
- preserve factual accuracy;
- include supporting evidence;
- distinguish facts from interpretations.

Example structure:

```markdown
# Career Highlights — August 2026

## Technical Impact

### Improved payment reliability

Identified and fixed a race condition in the payment processing system.

Evidence:

- GitHub PR #1234

## Collaboration

### Supported authentication investigation

Helped investigate an authentication issue and collaborated with another engineer to identify the underlying problem.

## Leadership

...
```

---

# 30. Performance Review

The skill can generate a performance review from accumulated evidence.

Suggested structure:

```text
Executive Summary

Key Accomplishments

Technical Impact

Business Impact

Leadership

Collaboration

Growth

Challenges

Areas for Development

Supporting Evidence
```

The generated review must never contain unsupported claims.

---

# 31. Promotion Case

The promotion mode should organize evidence against a target role.

Example:

> "Build my case for Staff Engineer."

The skill should:

1. read the user's profile;
2. read relevant career entries;
3. identify evidence related to the target level;
4. identify strengths;
5. identify gaps;
6. distinguish evidence from interpretation.

It must not state:

> "You are ready for Staff."

as a factual conclusion unless the user explicitly asks for an opinion.

Instead:

> "Your recorded evidence shows repeated examples of cross-team technical leadership. I found fewer examples related to organizational-level strategy."

---

# 32. Resume / CV

The skill can convert entries into concise resume bullets.

Example:

Career memory:

> Reduced API latency from 800ms to 300ms by redesigning caching strategy.

Resume output:

> Reduced API latency by 62.5% through a redesigned caching strategy.

The calculation is allowed when based entirely on supplied numbers.

The skill must not introduce metrics that were not supplied.

---

# 33. Interview Stories

The skill can generate interview material using recorded evidence.

Suggested structure:

```text
Situation

Task

Action

Result

Evidence
```

This is compatible with STAR-style interview preparation.

---

# 34. Search

The skill must support semantic retrieval conceptually.

Examples:

> "What did I do related to reliability?"

> "Show everything related to payments."

> "What examples do I have of mentoring?"

> "When did I demonstrate ownership?"

Search should consider:

- text;
- tags;
- skills;
- projects;
- dates;
- types;
- evidence.

---

# 35. Time-based Retrieval

The skill should support:

```text
today
yesterday
this week
last week
this month
last month
this quarter
last quarter
this year
last year
custom date range
```

Examples:

> "What did I accomplish last quarter?"

> "Show my work from this week."

---

# 36. Project Context

Projects can have their own context file.

Example:

```markdown
# Payments

## Purpose

Payment processing platform.

## Role

Backend engineering and technical leadership.

## Key Goals

- Improve reliability
- Reduce latency
- Simplify architecture
```

Entries can reference projects.

This allows the skill to answer:

> "What have I contributed to Payments?"

---

# 37. Skills and Competencies

Skills may be inferred from entries.

Examples:

```text
technical leadership
system design
debugging
communication
mentoring
ownership
project management
cross-team collaboration
customer communication
architecture
delivery
problem solving
```

These are interpretations, not facts.

The skill should avoid over-tagging.

---

# 38. Feedback

Feedback deserves special treatment.

Example:

```markdown
---
id: 2026-08-15-feedback-leadership
date: 2026-08-15
type: feedback
status: confirmed
---

# Positive feedback on meeting leadership

Received positive feedback from my manager regarding how I facilitated the project planning meeting.

## Source

Manager feedback

## Exact Feedback

[User-provided text if available]

## Interpretation

Potential evidence of communication and leadership.
```

The exact wording of feedback should only be included when actually provided.

---

# 39. Learning

Not every learning event is an achievement.

Example:

> "I learned that our retry strategy can create duplicate payment attempts."

This should be recorded as:

```text
learning
```

It may later become evidence of technical growth.

---

# 40. Career Patterns

Over time, the skill may identify recurring patterns.

Example:

> "Over the last six months, your entries frequently involve cross-team technical coordination."

This is a derived observation.

It should be labeled as such.

Example:

```text
Pattern detected:
Cross-team coordination appears in 12 entries over the last 6 months.
```

---

# 41. No Automatic Self-Promotion

The skill should not make every event sound impressive.

Bad:

> "Demonstrated exceptional leadership by attending a meeting."

Good:

> "Participated in project planning meeting."

The system should preserve credibility.

---

# 42. Privacy

Career Memory may contain sensitive professional information.

The implementation should:

- keep data local by default;
- avoid transmitting data unnecessarily;
- avoid external services unless explicitly configured;
- allow the user to inspect all stored information;
- allow manual deletion;
- never hide persistent data from the user.

---

# 43. Portability

The memory must not depend on a proprietary database.

A user should be able to:

1. copy the directory;
2. put it in Git;
3. open it in an editor;
4. move it to another computer;
5. use another compatible agent.

---

# 44. Git Compatibility

The directory can optionally live inside a Git repository.

Example:

```text
~/career-memory/
```

or:

```text
~/projects/career-memory/
```

The user can version changes over time.

The skill should not require Git to function.

---

# 45. Agent Compatibility

The skill should be designed to work with agent environments such as:

- Claude Code;
- GitHub Copilot;
- other coding agents that support skill/instruction files.

The skill should avoid provider-specific behavior whenever possible.

The canonical behavioral contract should live in:

```text
SKILL.md
```

Provider-specific adapters may be added separately.

---

# 46. GitHub Integration

GitHub integration is not required for v0.1.

However, the architecture must support it.

Future versions may identify evidence from:

- pull requests;
- issues;
- commits;
- reviews;
- discussions;
- repositories.

Example future workflow:

> "I noticed you merged three PRs that reduced API latency. This looks like potential career evidence. Save it?"

The system should always ask before turning automatically discovered signals into confirmed career entries.

## Implemented in v0.2

Discovery reads pull requests, issues, reviews and commits for the authenticated
user, through the `gh` CLI or a read-only token. It is read-only in both
directions that matter: nothing is written to GitHub, and nothing discovered
becomes a confirmed entry.

```text
GitHub activity
    ↓  github discover      (listed, marked against what is already recorded)
    ↓  github import        (written to candidates/ only)
    ↓  user confirms        (promote / dismiss)
Career Memory
```

Evidence already attached to an entry is recognised whether it was recorded as a
URL or as `owner/repo#123`, so re-running discovery never duplicates it. A signal
that resembles an existing entry is offered as an evidence link (`github link`)
rather than as a new entry.

GitHub metadata supplies references, never significance: titles, labels, dates
and states are recorded as facts, and impact stays undocumented until the user
states it.

Discussions and repository-level signals remain out of scope.

---

# 47. Telegram Integration

Telegram is an optional future interface to Career Memory.

The Telegram bot should not contain the career-memory logic itself.

Instead:

```text
Telegram
    ↓
Career Memory Interface
    ↓
Career Memory
    ↓
Entries
```

This allows the same memory to be used from:

- Claude Code;
- GitHub Copilot;
- Telegram;
- future web/mobile interfaces.

Telegram is particularly useful for capturing events immediately after they happen.

Example:

> User:
> "Today I fixed that race condition in payments."

The bot can invoke the same Career Memory capture workflow.

The Telegram integration must not create a separate source of truth.

---

# 48. Interface Independence

The system should conceptually separate:

```text
Interface
   ↓
Skill / Agent
   ↓
Career Memory Model
   ↓
Filesystem
```

Interfaces may include:

```text
Claude Code
GitHub Copilot
Telegram
CLI
Web UI
Mobile
```

The underlying data remains the same.

---

# 49. Output Quality Rules

All generated outputs must follow these rules:

1. Do not invent facts.
2. Do not invent metrics.
3. Do not invent feedback.
4. Do not exaggerate.
5. Prefer concrete examples.
6. Prefer evidence.
7. State when information is missing.
8. Distinguish facts from interpretations.
9. Preserve the user's voice when appropriate.
10. Optimize output for its intended audience.

---

# 50. Daily Output Quality Rules

Daily summaries additionally must:

1. Be short.
2. Be conversational.
3. Be easy to say aloud.
4. Focus on meaningful work.
5. Separate yesterday from today.
6. Include blockers only when relevant.
7. Never report planned work as completed work.
8. Avoid unnecessary technical detail unless useful to the audience.

---

# 51. Suggested File Structure

The complete v0.1 implementation may use:

```text
career-memory/
├── SKILL.md
├── README.md
├── profile.md
│
├── entries/
│   ├── 2026-08-20-payment-race-condition.md
│   ├── 2026-08-19-authentication-review.md
│   └── ...
│
├── candidates/
│   └── ...
│
├── projects/
│   ├── payments.md
│   └── authentication.md
│
├── feedback/
│   └── ...
│
├── outputs/
│   ├── brag.md
│   ├── performance-review.md
│   ├── promotion-case.md
│   ├── resume.md
│   ├── interview-stories.md
│   └── daily.md
│
└── templates/
    ├── entry.md
    ├── brag.md
    ├── review.md
    ├── promotion.md
    ├── resume.md
    ├── interview.md
    └── daily.md
```

---

# 52. Canonical SKILL.md Behavior

The actual `SKILL.md` should establish the following behavioral contract:

```markdown
# Career Memory

You maintain a persistent professional memory for the user.

Your job is to capture, organize, retrieve and synthesize factual
evidence about the user's professional work.

## Core principles

1. Never invent facts, metrics, outcomes, feedback, dates or evidence.
2. Preserve the user's original meaning.
3. Distinguish facts from interpretations.
4. Prefer concrete evidence over adjectives.
5. Do not turn every activity into an achievement.
6. Minimize questions during capture.
7. Ask at most one high-value clarification question when needed.
8. Keep all persistent data human-readable.
9. Treat stored career memory as the source of truth for generated career artifacts.
10. Explicitly identify missing information.
11. Never present an inference as a fact.
12. Avoid duplicate entries.

## Capture

When the user describes work-related activity:

1. Determine whether it is career-relevant.
2. Extract factual information.
3. Determine the appropriate entry type.
4. Identify project, skills and tags when possible.
5. Preserve evidence references.
6. Ask for clarification only when materially useful.
7. Create or update the entry.
8. Confirm what was recorded.

## Candidate detection

If an event appears potentially valuable but is ambiguous,
create a candidate or ask the user whether it should be saved.

Candidates may become:

- confirmed
- dismissed
- edited and confirmed

## Retrieval

Support natural-language retrieval by:

- date
- project
- skill
- type
- keyword
- semantic meaning
- evidence

## Brag documents

Generate brag documents exclusively from recorded evidence.

Group related evidence and emphasize:

- impact
- ownership
- technical contribution
- leadership
- collaboration
- growth

Never fabricate missing metrics or outcomes.

## Performance reviews

Generate structured performance reviews using recorded evidence.

Clearly distinguish:

- facts
- patterns
- interpretations
- gaps

## Promotion cases

Compare recorded evidence with the user's target role or level.

Do not make unsupported promotion decisions.

Identify:

- demonstrated strengths
- supporting evidence
- recurring patterns
- missing evidence
- potential gaps

## Resume

Convert factual career entries into concise resume bullets.

Metrics may only be used when present in the source data or mathematically
derived from source data.

## Interview stories

Convert relevant entries into structured interview stories.

Use factual events and clearly identify the user's actions and results.

## Daily Summary Mode

When the user asks for a daily, standup, daily update, or similar summary:

1. Retrieve relevant recent entries.
2. Identify yesterday's completed work.
3. Identify today's current or planned work.
4. Identify relevant blockers.
5. Produce a concise spoken summary.
6. Never convert planned work into completed work.
7. Prefer a 30–90 second spoken update.
8. Keep unnecessary details out of the summary.

Canonical format:

Yesterday:

- ...

Today:

- ...

Blockers:

- ...

## Data

Use the career-memory directory as the persistent source of truth.

Prefer Markdown files and human-readable metadata.

Do not require a database.

## Interfaces

The skill should work independently of any specific interface.

Supported or planned interfaces may include:

- Claude Code
- GitHub Copilot
- Telegram
- CLI
- Web
- Mobile

Telegram is an optional interface and must not become a separate source of truth.

## Privacy

Treat career data as private user information.

Prefer local storage and minimize external transmission.

## Quality

The goal is not to make the user sound impressive.

The goal is to accurately preserve what the user actually did,
why it mattered, and what evidence exists.
```

---

# 53. Version 0.1 Scope

The first implementation should focus on four capabilities:

```text
1. Capture
2. Search / Retrieval
3. Brag Document
4. Daily Summary
```

Performance Review, Promotion Case, Resume and Interview Stories should be supported by the data model and templates, but can initially be implemented as secondary generation modes.

---

# 54. Version Roadmap

## v0.1 — Foundation

- Markdown storage
- Entry schema
- Natural-language capture
- Candidate detection
- Search
- Brag generation
- Daily Summary Mode
- Basic profile
- Project context
- Evidence references

## v0.2 — GitHub

- PR discovery
- Issue discovery
- Commit discovery
- Review discovery
- Candidate generation from GitHub activity
- Evidence linking

## v0.3 — Proactive Memory

- Detect potential career evidence automatically
- Periodic review prompts
- Weekly summary
- Monthly summary
- Missing-evidence detection

## v0.4 — Interfaces

- Telegram
- CLI
- additional agent integrations

## v0.5 — Career Intelligence

- Career trends
- competency evolution
- recurring impact patterns
- promotion-gap analysis
- evidence graphs
- longitudinal career summaries

---

# 55. Example End-to-End Flow

## Step 1 — User works

The user fixes a production problem.

## Step 2 — User tells the agent

> "Fixed the race condition in the payment flow. It was causing intermittent failures."

## Step 3 — Skill captures

```text
Type: problem-solving
Project: payments
Topic: race condition
Impact: intermittent payment failures addressed
Evidence: none
Status: confirmed
```

## Step 4 — Later, user provides evidence

> "Here's the PR: #1234."

The skill updates the existing entry.

## Step 5 — Daily

User:

> "Prepare my daily."

The skill produces:

> Yesterday: I fixed the race condition in the payment flow and added the corresponding changes to the payment service.
>
> Today: I'll continue working on payment reliability.
>
> Blockers: None.

## Step 6 — Months later

User:

> "Prepare my performance review."

The same entry contributes evidence to the review.

## Step 7 — Promotion

User:

> "What evidence do I have for Staff Engineer?"

The system identifies this event alongside other examples of:

- ownership;
- technical depth;
- reliability;
- cross-team impact;
- leadership.

One small work event therefore becomes useful across multiple contexts.

---

# 56. Design Principle

The most important architectural principle of Career Memory is:

```text
Capture once.
Use many times.
```

A single piece of evidence should not need to be rewritten for:

- daily;
- weekly summary;
- brag document;
- performance review;
- promotion case;
- resume;
- interview preparation.

The system should transform the same underlying evidence into different narratives depending on the user's needs.

---

# 57. Final Product Definition

Career Memory is a portable, agent-agnostic professional memory skill.

It continuously transforms informal descriptions of work into structured career evidence and later transforms that evidence into useful professional communication.

The system connects:

```text
                    ┌── Daily Summary
                    │
                    ├── Brag Document
                    │
Work → Evidence → Memory ── Performance Review
                    │
                    ├── Promotion Case
                    │
                    ├── Resume
                    │
                    └── Interview Stories
```

The core promise is:

> **Never forget the work you've done.**

And the core product loop is:

> **Capture → Organize → Preserve → Retrieve → Communicate**
