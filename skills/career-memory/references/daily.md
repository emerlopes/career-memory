# Daily standup mode

## What this is for

The user has to speak for about a minute in front of their team. They want to
sound clear and prepared, not to read a changelog. This is a different job from
career memory: career memory preserves detail, the daily throws most of it away.

Read from the store; never replace it. A daily is an output, not a record.

## Building it

```bash
python3 "$CM" list --window 3d --format full
```

Three days rather than one, because Monday's "yesterday" is Friday and because
work in flight usually started earlier. Then sort what you find into:

- **Yesterday** — what is actually finished or meaningfully advanced
- **Today** — what is in progress or planned
- **Blockers** — only things genuinely blocking, and only if the team can help

If the store says nothing about today's plan — it usually will not, since plans
are not evidence — ask one question: "What are you picking up today?" Better a
short question than an invented plan.

## Format

```text
Yesterday:
- Fixed the race condition in the payment flow.
- Reviewed João's authentication PR.

Today:
- Continuing payment reliability work.
- Starting the database migration.

Blockers:
- None.
```

Spoken form is fine too when the user prefers it:

> Yesterday I fixed the race condition in the payment flow and reviewed João's
> authentication PR. Today I'll keep going on payment reliability and start the
> database migration. No blockers.

## Rules that matter

**Never move planned work into "Yesterday".** "I'm planning to migrate the
database" is not "Migrated the database". This is the single most damaging thing
this mode can get wrong: the user says it out loud to people who will notice.

**Three to five bullets total.** Everything beyond that is detail the team will
not retain. Drop the small stuff; the store keeps it either way.

**Blockers are not complaints.** "The staging environment has been down since
Tuesday and I need infra to look at it" is a blocker. "This code is messy" is
not. If there are none, say so in three words.

**No impact claims.** Standups are for coordination. Save "this reduced latency
by 60%" for the review.

**Match their register.** If the user writes in Portuguese, produce the daily in
Portuguese. Keep the technical terms they actually use with their team.

## Capture from dailies

Dailies are an excellent capture surface — the user is already recounting their
work. When something comes up that is not in the store:

> That migration finishing isn't in your career memory yet. Want me to add it?

Ask once, do not nag, and never save silently just because they said it during a
daily.
