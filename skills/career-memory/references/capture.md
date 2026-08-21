# Capture in detail

## What is worth recording

The test is whether the user would want this in front of them a year from now,
when they are staring at an empty self-review form.

Usually yes:

- a hard problem diagnosed or fixed
- something shipped, released, migrated
- a decision made or driven
- helping, unblocking, mentoring or reviewing for someone
- feedback received, positive or critical
- a non-obvious thing learned about the system or the domain
- taking ownership of something nobody owned
- customer or stakeholder interactions with an outcome

Usually no:

- routine tickets with no story
- attending a meeting with no role in it
- work in progress with nothing established yet (unless the user asks)
- anything the user is clearly just thinking out loud about

When in doubt, make it a candidate rather than dropping it. A candidate costs
the user one word to confirm; a lost month of work costs them a promotion cycle.

## Extraction

Take only what is in what the user said.

> "Finally fixed that payment race condition. It was causing intermittent
> failures for like two weeks."

| Field    | Value                                         | Why                         |
| -------- | --------------------------------------------- | --------------------------- |
| date     | today, unless they said otherwise             |                             |
| type     | `problem-solving`                             | a diagnosis and a fix       |
| project  | `payments`                                    | named                       |
| title    | Fixed payment race condition                  | their words                 |
| impact   | intermittent failures over ~2 weeks addressed | they said it                |
| evidence | none                                          | they did not give one       |
| tags     | debugging, reliability                        | descriptive, not flattering |

What must **not** appear: a percentage, a revenue figure, a customer count, a
"critical production incident" framing they never used.

## Dates

"Yesterday" means yesterday, not today. "Last week" without a day is
ambiguous — use the entry's `--date` to the best supported value and mention it
in the confirmation so a wrong guess is easy to correct.

## The one question

Ask only when the answer changes the record materially:

- "Did that fix hold?" → turns an attempt into an outcome
- "Was that the migration you were leading, or supporting?" → changes the type
- "Do you have the PR handy?" → turns a claim into evidence

Do not ask for tags, type, or a title. Those are your job.

## Candidates

Create with `--status candidate` when the event is real but its value is
unclear, or when you inferred it rather than being told.

```bash
python3 "$CM" add "Helped João debug authentication" \
  --date yesterday --type collaboration --project auth \
  --people "João" --status candidate
```

Then: `promote <id>` to confirm, `dismiss <id>` to drop it, or `update` first if
the user wants it worded differently. Do not let candidates pile up silently —
when the user asks for a brag document or review, mention any pending ones.

## Duplicates

`add` compares the title and body against entries within three weeks and refuses
on a likely match, printing what it found. Read the match before overriding:

- Same event, more detail → `update <id> --append "..."`
- Same event, now with a PR → `update <id> --add-evidence 'github_pr:#1234'`
- Genuinely distinct event with a similar name → `add --force`

Updating beats duplicating: one entry that accumulates evidence over time is
stronger than three thin ones saying nearly the same thing.

## Confirmation

Short, factual, no celebration:

> **Recorded** — Fixed intermittent payment-processing race condition.
> Type: problem-solving · Project: payments · Evidence: PR #1234
> Impact: not documented — tell me if you have numbers.

That last clause is doing real work: it invites the evidence without demanding it.

## Worked examples

**Weak signal, offer instead of saving:**

> User: "Spent the morning helping João with the auth thing."
>
> You: Possible career evidence — collaboration, unblocking João on
> authentication. Save it? (I'd file it under the auth project.)

**Feedback:**

> User: "My manager said the planning meeting went really well because I
> facilitated it."

```bash
python3 "$CM" add "Positive feedback on facilitating planning meeting" \
  --type feedback --date today --source "manager, 1:1" \
  --body "Manager said the project planning meeting went well and attributed it to my facilitation."
```

Record the wording the user reported. Do not upgrade "went really well" into
"outstanding leadership".

**Learning, not achievement:**

> User: "TIL our retry strategy can double-charge people."

```bash
python3 "$CM" add "Discovered retry strategy can cause duplicate payment attempts" \
  --type learning --project payments --tags "reliability,payments"
```

This is not yet an accomplishment. If they fix it later, that is a second entry
that references this one.
