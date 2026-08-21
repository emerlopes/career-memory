# GitHub discovery

GitHub knows a lot about what the user shipped, and nothing about what it meant.
That split is the whole design: GitHub supplies **references**, the user supplies
**significance**. Discovery is read-only, and everything it finds arrives as a
candidate.

## Access

```bash
python3 "$CM" github check
```

Prints the account discovery will run as, and which backend it found:

- **`gh`** — the GitHub CLI, using whatever `gh auth login` already set up. This
  is the default and the one to prefer: no token ever touches the store.
- **`api`** — `https://api.github.com` with `$GITHUB_TOKEN` or `$GH_TOKEN`.
  `$GITHUB_API_URL` points it at a GitHub Enterprise host.

Exit code 3 means "no GitHub access", not "nothing found". Say which one it was:
the fix ("run `gh auth login`") is the user's, and everything else in the skill
keeps working without it.

## Discover before you import

```bash
python3 "$CM" github discover --window last-month
python3 "$CM" github discover --window 7d --repo acme/payments
python3 "$CM" github discover --window this-quarter --org acme --new-only
```

Each line is marked `new` or `saved` — `saved` meaning that reference is already
attached to an entry, matched whether it was recorded as a URL or as
`owner/repo#123`. Show the user this list before writing anything; it is short,
scannable, and lets them point at what actually mattered.

| Flag                | Default        | Notes                                             |
| ------------------- | -------------- | ------------------------------------------------- |
| `--window`          | `30d`          | Same vocabulary as `list` / `search`               |
| `--from` / `--to`   | —              | Explicit range, overrides `--window`               |
| `--kinds`           | `pr,issue,review` | Add `commit` explicitly when you want commits  |
| `--repo` / `--org`  | —              | `owner/name`, or a whole organisation             |
| `--visibility`      | `all`          | `public` when the user's work is confidential     |
| `--by`              | `created`      | Which date the window filters on (`merged` is often what the user means) |
| `--limit`           | `50`           | Per kind                                          |
| `--format`          | `table`        | `json` for full signals, `refs` for bare references |

Commits are opt-in on purpose. A week of commits is not a week of career
evidence, and importing them wholesale buries the three entries that matter
under forty that do not.

## What each signal becomes

| Signal   | Entry type        | Title                | Evidence type    |
| -------- | ----------------- | -------------------- | ---------------- |
| PR       | `delivery`        | the PR title         | `github_pr`      |
| Issue    | `problem-solving` | `Opened issue: …`    | `github_issue`   |
| Review   | `collaboration`   | `Reviewed: …`        | `github_review`  |
| Commit   | `delivery`        | the commit subject   | `github_commit`  |

These are mechanical defaults, not judgments. A PR that was really a migration
the user led is `leadership`; fix it with `update` (or edit the file) before
promoting. The project defaults to the repository name, labels become tags
(process labels like `size/L` are dropped), and the reviewed PR's author is
recorded under `people`.

Dates come from the event: a PR is dated when it merged, otherwise when it
closed, otherwise when it was opened. Reviews are the exception — GitHub's
search index does not say when a review was submitted, so the entry is dated
from the PR's last update and says so in its body. Do not quietly present that
as the review date.

## Import as candidates

```bash
python3 "$CM" github import --window last-month --dry-run
python3 "$CM" github import --window last-month
```

Import only ever writes to `candidates/`. There is no flag to write a confirmed
entry, because the spec's rule is absolute: an automatically discovered signal
becomes career memory only when the user says so. After importing, walk the list
with them and `promote` or `dismiss` each one — in one message, not fifteen.

Two things are skipped rather than duplicated:

- **Already-recorded references** — reported as "already recorded", left alone.
  Re-running an import is safe.
- **Signals that look like an existing entry** — printed with the matching entry
  id and a ready-made `github link` command. This is the common case for a user
  who told you about the work in the morning and merged the PR in the afternoon:
  one entry, now with its evidence attached. `--force` overrides it when the
  events really are separate.

`--with-body` copies the PR or issue description into a Context section. It is
the user's own writing, so it is not an invention — but it is often a template
full of checkboxes. Use it when the description is real prose.

## Link evidence to what is already recorded

```bash
python3 "$CM" github link 2026-08-20-payment-race-condition https://github.com/acme/payments/pull/1234
python3 "$CM" github link <id> acme/payments#1234 acme/payments@9f3c1ab
```

Accepts PR, issue, commit and review URLs, plus the `owner/repo#123` and
`owner/repo@sha` shorthands. It fetches the title so the entry carries something
readable a year from now, resolves whether `#123` is a PR or an issue, and never
adds the same reference twice. `--no-fetch` links offline, without titles.

This is the highest-value command in v0.2 and the easiest to forget: when a user
mentions a PR number in conversation, link it to the entry you just wrote.

## A workflow that works

Weekly, or whenever the user asks what they have been doing:

1. `github discover --window 7d` — show the list.
2. Ask which of them are worth remembering. Most weeks it is one or two.
3. `github import` the ones they picked (or import all and dismiss the rest, if
   they prefer to prune).
4. For each imported candidate, ask the question GitHub cannot answer: *what did
   this change for anyone?* Record the answer with `update --set-impact`.
5. `promote` the ones they confirm.

Step 4 is the point of the whole feature. A candidate that reaches `entries/`
carrying only a PR title is a bookmark, not career evidence.

## What not to do

- **Do not infer impact from a diff.** Lines changed, files touched and review
  count are not outcomes. `Impact: not documented` remains the honest answer
  until the user gives you one.
- **Do not read a merged PR as a success.** Merged means merged. Whether it
  worked is a separate fact, and only the user has it.
- **Do not import a whole year "to be safe".** Hundreds of candidates nobody
  reviews is the failure mode this skill exists to avoid.
- **Mind private work.** Discovery reads private repositories the account can
  see, and imported titles land in plain files. If the user's repository names
  or PR titles are confidential, use `--visibility public`, or import with an
  explicit `--project` and edit titles before promoting.
