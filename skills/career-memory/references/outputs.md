# Generating career documents

Five documents, one body of evidence, five different readers. Start from the
matching file in `templates/`, write the result into the store's `outputs/`, and
tell the user the path.

Before writing any of them, pull the evidence:

```bash
python3 "$CM" list --window last-quarter --format full
python3 "$CM" stats --window 6m          # recurring themes, and where evidence is thin
python3 "$CM" gaps --window last-quarter # what the record cannot prove yet
python3 "$CM" trends --window 12m        # how those themes moved across periods
```

Any weekly or monthly summaries already in `outputs/summaries/` are a shortcut:
they are the same evidence, already grouped. Read them, but quote the entries —
a summary is an output, not a source.

## Rules for all five

1. Every claim traces to an entry. If you cannot point at the entry, cut the claim.
2. Metrics appear only when the user recorded them, or when they follow
   arithmetically from numbers the user recorded (800ms → 300ms is a 62.5%
   reduction; that calculation is allowed, inventing the 800ms is not).
3. Group related entries. Six small payments entries make one strong paragraph
   about payment reliability, not six weak bullets.
4. Facts and interpretations stay visually separate.
5. Name the gaps. A short "not documented" section is more useful to the user
   than another paragraph of filler, and it is what they will act on.
6. Keep the user's voice and their technical vocabulary.

## Brag document

Audience: the user, and whoever they choose to show. Purpose: nothing gets
forgotten.

Group by theme (technical impact, delivery, leadership, collaboration,
learning), most substantial first. Include evidence links inline. Close with
patterns from `stats` and `trends` — labelled as observation, e.g. "Cross-team
coordination appears in 12 entries over three quarters" — and a short list of
work the user mentioned but never documented. `graph --format mermaid` gives the
clusters the sections can be organized around, and a figure if the document
wants one.

## Performance review

Audience: the user's manager and the calibration process. Purpose: survive
scrutiny.

Follow the template's sections. Two things carry it: an executive summary the
manager could paste into a form, and an evidence table at the end. Where a
section has no support in the record — business impact is the usual one — write
that plainly rather than reaching. A review with one honest gap reads as
trustworthy; a review with five padded sections reads as noise.

If `profile.md` names the company's ladder or values, organize against those.

## Promotion case

Audience: a skeptical committee. Purpose: show the pattern, not the highlight.

1. Read `profile.md` for the target role.
2. Run `promotion --role "<target>"`: it retrieves the evidence per criterion of
   that level and sorts the criteria into recorded repeatedly, thin in the
   record, and nothing in the record mentions it. `references/intelligence.md`
   covers where the criteria come from and how to record a company ladder.
3. For each criterion: what is demonstrated, which entries show it, how often,
   and across how many periods.
4. Name what is thin or missing, specifically.
5. Suggest what evidence to collect next.

Do not deliver a verdict. "You are ready for Staff" is not yours to assert
unless the user explicitly asks your opinion. What helps is:

> Your record shows repeated cross-team technical leadership — five entries
> across three quarters. Evidence of organization-level strategy is thinner:
> two entries, both from the same project.

Those two sentences are exactly what `promotion` computes; the judgement it
refuses to make is the one the committee is paid to make.

That sentence tells the user what to do next; a verdict does not.

## Resume bullets

Audience: recruiters and hiring managers scanning for eight seconds.

One line each: strong verb, what, measurable result when recorded. Compress
aggressively — a resume bullet is the smallest useful form of an entry.

> Entry: "Reduced API latency from 800ms to 300ms by redesigning the caching strategy."
>
> Bullet: "Cut API latency 62% (800ms → 300ms) by redesigning the caching layer."

## Interview stories

Audience: an interviewer probing for depth. Purpose: recall under pressure.

STAR, one story per entry cluster: Situation, Task, Action, Result, Evidence.
The Action section is what interviewers actually probe, so make it specific
about what *the user* did, not what the team did. If the result was never
measured, write "not measured" — the user can say that out loud without risk,
and it is far better than being caught inventing a number in the room.
