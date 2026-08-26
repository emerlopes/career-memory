#!/usr/bin/env bash
# Smoke tests for career_memory.py. No dependencies beyond python3.
# Dates are computed relative to today so the suite stays valid over time.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CM="$ROOT/skills/career-memory/scripts/career_memory.py"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

export CAREER_MEMORY_HOME="$WORK/store"

day() { python3 -c "import datetime,sys; print(datetime.date.today()-datetime.timedelta(days=int(sys.argv[1])))" "$1"; }
TODAY="$(day 0)"; YESTERDAY="$(day 1)"; LAST_WEEK="$(day 6)"; NEXT_YEAR="$(( ${TODAY%%-*} + 1 ))-01-01"

PASS=0
FAIL=0

check() { # check <name> <expected-substring> <command...>
  local name="$1" expect="$2"; shift 2
  local out; out="$("$@" 2>&1)"
  if [[ "$out" == *"$expect"* ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$name"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s\n       expected to contain: %s\n       got: %s\n' "$name" "$expect" "$out"
  fi
}

check_absent() { # check_absent <name> <forbidden-substring> <command...>
  local name="$1" forbid="$2"; shift 2
  local out; out="$("$@" 2>&1)"
  if [[ "$out" != *"$forbid"* ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$name"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s\n       should not contain: %s\n       got: %s\n' "$name" "$forbid" "$out"
  fi
}

check_status() { # check_status <name> <expected-exit-code> <command...>
  local name="$1" expect="$2"; shift 2
  "$@" >/dev/null 2>&1
  local code=$?
  if [[ "$code" == "$expect" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$name"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (exit %s, expected %s)\n' "$name" "$code" "$expect"
  fi
}

run() { python3 "$CM" "$@"; }

echo "career_memory.py smoke tests"

# --- setup -----------------------------------------------------------------
check "init creates the store" "store ready" run init
check_status "entries/ exists" 0 test -d "$WORK/store/entries"
check_status "profile.md created" 0 test -f "$WORK/store/profile.md"

# --- bootstrap and settings ------------------------------------------------
STORE2="$WORK/bootstrapped"
fill_profile() { # rewrite profile.md placeholders so the profile reads complete
  python3 - "$STORE2/profile.md" <<'FILL'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = t.replace("<!-- e.g. Senior Software Engineer -->", "Senior Software Engineer")
t = t.replace("<!-- e.g. Backend systems, distributed systems, technical leadership -->", "Backend")
t = t.replace("- <!-- e.g. Grow toward Staff Engineer -->", "- Staff Engineer")
p.write_text(t)
FILL
}
blank_role() { # put the Role placeholder back
  python3 - "$STORE2/profile.md" <<'FILL'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text().replace("Senior Software Engineer", "<!-- placeholder -->"))
FILL
}

check "status creates a store from nothing" "created now:" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status
check_status "status created entries/" 0 test -d "$STORE2/entries"
check_status "status created config.json" 0 test -f "$STORE2/config.json"
check_absent "status is idempotent" "created now:" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status
check "a fresh profile reads as incomplete" "missing Role, Focus, Current Goals" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status
check "an incomplete profile blocks documents by default" "blocked: documents" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status

fill_profile
check "a filled profile reads as complete" "profile: complete" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status
check "a complete profile blocks nothing" "blocked: nothing" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status
check "status --format json is parseable" '"blocked": "nothing"' \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status --format json

check "config shows defaults" "language" env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config
check "config --set persists" "Updated" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --set language=pt
check "config --get reads it back" "pt" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --get language
check "an invalid value is refused" "must be one of" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --set language=klingon
check_status "an invalid value exits 1" 1 \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --set language=klingon
check "an unknown setting is refused" "unknown setting" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --set idioma=pt
check "a bad assignment is refused" "expected key=value" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --set language

# The hard gate is opt-in, and must actually bite when chosen.
blank_role
env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --set profile_gate=all >/dev/null
check "profile_gate=all blocks everything" "blocked: everything" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status
env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" config --set profile_gate=remind >/dev/null
check "profile_gate=remind blocks nothing" "blocked: nothing" \
  env CAREER_MEMORY_HOME="$STORE2" python3 "$CM" status

mkdir -p "$WORK/corrupt" && printf '{ nope' > "$WORK/corrupt/config.json"
check "a corrupt config falls back to defaults" "language" \
  env CAREER_MEMORY_HOME="$WORK/corrupt" python3 "$CM" config

# --- add -------------------------------------------------------------------
check "add writes an entry" "Recorded:" run add "Resolved payment race condition" \
  --date "$TODAY" --type problem-solving --project payments \
  --tags debugging,reliability --evidence 'github_pr:#1234' \
  --body "Fixed a race condition in payment processing."
check_status "entry file exists" 0 test -f "$WORK/store/entries/$TODAY-resolved-payment-race-condition.md"

check "bare relative date resolves" "date: $YESTERDAY" run add "Relative date entry" \
  --date 1d --type learning --id relative-date-entry
check "show confirms the relative date" "date: $YESTERDAY" run show relative-date-entry
check "an unusable date is rejected clearly" "unrecognised date" run add "Bad date" --date "ontem-ish"

check "add reports missing impact" "impact: not documented" run add "Shipped the new dashboard" \
  --date "$YESTERDAY" --type delivery --project dashboard

check "duplicate detection blocks a near-identical add" "Possible duplicates" \
  run add "Resolved the payment race condition" --date "$TODAY" --project payments
check_status "duplicate add exits 2" 2 run add "Resolved the payment race condition" \
  --date "$TODAY" --project payments
check_absent "blocked duplicate wrote nothing" "Recorded:" \
  run add "Resolved the payment race condition" --date "$TODAY" --project payments
check "force overrides duplicate detection" "Recorded:" run add "Separate payments incident" \
  --date "$TODAY" --project payments --force --id forced-entry

check "candidates land in candidates/" "candidates/" run add "Helped Joao with auth" \
  --date "$YESTERDAY" --type collaboration --people Joao --status candidate
check "feedback lands in feedback/" "feedback/" run add "Positive feedback on facilitation" \
  --date "$LAST_WEEK" --type feedback --source "manager 1:1"

# --- retrieval -------------------------------------------------------------
check "list shows confirmed entries" "Resolved payment race condition" run list
check "candidates are hidden by default" "No entries matched" run list --status candidate
check "include-candidates surfaces them" "Helped Joao with auth" run list --include-candidates
check "today window includes today" "Resolved payment race condition" run list --window today
check_absent "today window excludes yesterday" "Shipped the new dashboard" run list --window today
check "week window includes yesterday" "Shipped the new dashboard" run list --window 7d
check "future range matches nothing" "No entries matched" run list --from "$NEXT_YEAR"
check "type filter works" "Shipped the new dashboard" run list --type delivery
check_absent "type filter excludes other types" "Resolved payment race condition" run list --type delivery
check "project filter works" "payments" run list --project payments
check "limit is respected" "1 entry" run list --limit 1
check "json output is parseable" '"type": "problem-solving"' run list --format json

check "search finds by body text" "Resolved payment race condition" run search "race condition"
check "search finds by tag" "Resolved payment race condition" run search "reliability"
check "search finds by person" "Helped Joao with auth" run search "Joao" --include-candidates
check "search reports no match honestly" "No entries matched" run search "kubernetes operator"

# --- update ----------------------------------------------------------------
ENTRY="$TODAY-resolved-payment-race-condition"
check "update attaches evidence" "evidence metric" run update "$ENTRY" \
  --add-evidence 'metric:latency dashboard:800ms -> 300ms'
check "update records impact" "impact recorded" run update "$ENTRY" \
  --set-impact "Addressed intermittent payment failures"
check "update adds skills" "skills: +ownership" run update "$ENTRY" --add-skill ownership
check "repeat evidence is not duplicated" "Nothing to update" run update "$ENTRY" \
  --add-evidence 'metric:latency dashboard:800ms -> 300ms'
check "show renders front matter" "type: problem-solving" run show "$ENTRY"
check "evidence survives a round trip" "800ms -> 300ms" run show "$ENTRY"
check "original evidence is preserved" "#1234" run show "$ENTRY"

# --- candidates ------------------------------------------------------------
CAND="$YESTERDAY-helped-joao-auth"
check "promote confirms a candidate" "Confirmed:" run promote "$CAND"
check_status "promoted file moved into entries/" 0 test -f "$WORK/store/entries/$CAND.md"
check_status "promoted file left candidates/" 1 test -f "$WORK/store/candidates/$CAND.md"
check "dismiss refuses a confirmed entry" "not a candidate" run dismiss "$CAND"
run add "Throwaway candidate" --date "$TODAY" --status candidate --id tmp-candidate >/dev/null 2>&1
check "dismiss removes a candidate" "Dismissed:" run dismiss tmp-candidate
check_status "dismissed file is gone" 1 test -f "$WORK/store/candidates/tmp-candidate.md"

# --- integrity -------------------------------------------------------------
check "stats counts entries" "By type" run stats
check "stats tracks evidence coverage" "Evidence attached:" run stats
check "validate passes on generated entries" "valid" run validate
check_status "validate exits 0" 0 run validate
check "where prints the store path" "$WORK/store" run where

printf -- '---\nid: broken\ndate: not-a-date\ntype: nonsense\n---\n\n# Broken\n' \
  > "$WORK/store/entries/broken.md"
check "validate flags a bad date" "date is not YYYY-MM-DD" run validate
check "validate flags an unknown type" "unknown type" run validate
check_status "validate exits 1 on problems" 1 run validate
rm "$WORK/store/entries/broken.md"

# The mini YAML parser must give the same answers when PyYAML is absent.
mkdir -p "$WORK/noyaml/yaml"
echo 'raise ImportError("simulated")' > "$WORK/noyaml/yaml/__init__.py"
check "show works without PyYAML" "800ms -> 300ms" \
  env PYTHONPATH="$WORK/noyaml" python3 "$CM" show "$ENTRY"
check "nested impact parses without PyYAML" "Addressed intermittent payment failures" \
  env PYTHONPATH="$WORK/noyaml" python3 "$CM" show "$ENTRY"
check "search works without PyYAML" "Resolved payment race condition" \
  env PYTHONPATH="$WORK/noyaml" python3 "$CM" search "race condition"
check "validate works without PyYAML" "valid" \
  env PYTHONPATH="$WORK/noyaml" python3 "$CM" validate

# An uninitialised store should say so rather than failing obscurely.
check "uninitialised store gives a clear message" "No Career Memory store" \
  env CAREER_MEMORY_HOME="$WORK/nowhere" python3 "$CM" list

# --- github (v0.2) ---------------------------------------------------------
# A fake `gh` on PATH answers from tests/fixtures/github, so discovery is
# exercised end to end without a network or an account.
mkdir -p "$WORK/bin"
ln -s "$ROOT/tests/fake-gh.sh" "$WORK/bin/gh"
export PATH="$WORK/bin:$PATH"
export FAKE_GH_FIXTURES="$ROOT/tests/fixtures/github"
export CAREER_MEMORY_HOME="$WORK/gh-store"
run init >/dev/null
RANGE=(--from 2026-01-01 --to 2026-01-31)
ALL_KINDS=(--kinds pr,issue,review,commit)

check "github check resolves the account" "reachable as @testuser" run github check
check "github check names the backend" "backend: gh" run github check

check "discover finds pull requests" "acme/payments#123" run github discover "${RANGE[@]}"
check "discover finds issues" "acme/payments#45" run github discover "${RANGE[@]}"
check "discover finds reviews" "acme/ledger#77" run github discover "${RANGE[@]}"
check_absent "commits are opt-in" "abc1234" run github discover "${RANGE[@]}"
check "discover finds commits when asked" "acme/payments@abc1234" \
  run github discover "${RANGE[@]}" "${ALL_KINDS[@]}"
check "discover marks unrecorded signals as new" "5 new" \
  run github discover "${RANGE[@]}" "${ALL_KINDS[@]}"
check "refs format prints bare references" "acme/payments#123" \
  run github discover "${RANGE[@]}" --format refs
check "json format carries the evidence type" '"evidence_type": "github_review"' \
  run github discover "${RANGE[@]}" --format json

check "dry-run reports without writing" "Would import" \
  run github import "${RANGE[@]}" "${ALL_KINDS[@]}" --dry-run
check_status "dry-run wrote nothing" 1 test -f "$WORK/gh-store/candidates/2026-01-15-pr-acme-payments-123.md"

check "import writes candidates" "Imported 5 candidate" \
  run github import "${RANGE[@]}" "${ALL_KINDS[@]}"
check_status "imported entry landed in candidates/" 0 \
  test -f "$WORK/gh-store/candidates/2026-01-15-pr-acme-payments-123.md"
check_absent "import never writes confirmed entries" "status: confirmed" \
  run show 2026-01-15-pr-acme-payments-123
check "imported PR keeps the merge date" "date: 2026-01-15" run show 2026-01-15-pr-acme-payments-123
check "imported PR links the pull request" 'reference: "acme/payments#123"' \
  run show 2026-01-15-pr-acme-payments-123
check "labels become tags" "- reliability" run show 2026-01-15-pr-acme-payments-123
check_absent "process labels are dropped" "size/l" run show 2026-01-15-pr-acme-payments-123
check "reviews use the review evidence type" "type: github_review" \
  run show 2026-01-18-review-acme-ledger-77
check "reviews credit the pull request author" "- colleague" run show 2026-01-18-review-acme-ledger-77
check "review dates are labelled as a proxy" "does not report when the review" \
  run show 2026-01-18-review-acme-ledger-77
check "issues are titled as opened" "# Opened issue:" run show 2026-01-16-issue-acme-payments-45
check "imported entries validate" "valid" run validate

check "re-import skips what is already recorded" "already recorded" \
  run github import "${RANGE[@]}" "${ALL_KINDS[@]}"
check "re-import writes nothing new" "Imported 0 candidate" \
  run github import "${RANGE[@]}" "${ALL_KINDS[@]}"
check "discover marks recorded signals as saved" "saved" \
  run github discover "${RANGE[@]}" "${ALL_KINDS[@]}"
check "new-only hides recorded signals" "Nothing found" \
  run github discover "${RANGE[@]}" "${ALL_KINDS[@]}" --new-only

# A GitHub signal that duplicates a hand-written entry should be linked, not imported.
export CAREER_MEMORY_HOME="$WORK/gh-store2"
run init >/dev/null
run add "Fix race condition in payment capture" --date 2026-01-14 \
  --type problem-solving --project payments >/dev/null
check "import suggests linking over duplicating" "link the evidence instead" \
  run github import "${RANGE[@]}" --kinds pr
check "the suggestion names the existing entry" \
  "github link 2026-01-14-fix-race-condition-payment-capture acme/payments#123" \
  run github import "${RANGE[@]}" --kinds pr

LINKED="2026-01-14-fix-race-condition-payment-capture"
check "link attaches a pull request from a URL" "evidence github_pr acme/payments#123" \
  run github link "$LINKED" "https://github.com/acme/payments/pull/123"
check "link fetches the title" "title: Fix race condition in payment capture" run show "$LINKED"
check "link treats a URL and its shorthand as one reference" "already linked" \
  run github link "$LINKED" "acme/payments#123"
check "link accepts a commit sha" "evidence github_commit acme/payments@abc1234" \
  run github link "$LINKED" "acme/payments@abc1234def5678" --no-fetch
check "link rejects a reference it cannot parse" "unrecognised GitHub reference" \
  run github link "$LINKED" "not a reference"
check "linked entries still validate" "valid" run validate
check "linked evidence survives without PyYAML" "acme/payments#123" \
  env PYTHONPATH="$WORK/noyaml" python3 "$CM" show "$LINKED"
check "a linked pull request is not imported again" "already recorded" \
  run github import "${RANGE[@]}" --kinds pr

run add "Manual evidence URL" --date 2026-03-01 --id manual-url --force \
  --evidence 'github_pr:https://github.com/acme/payments/pull/130' >/dev/null
check "a URL passed to --evidence stays whole" \
  "reference: https://github.com/acme/payments/pull/130" run show manual-url
check "a manually pasted URL blocks a duplicate import" "2 signal(s) already recorded" \
  run github import "${RANGE[@]}" --kinds pr

# Without a backend the failure must be obvious and distinguishable (exit 3).
check "missing GitHub access is explained" "no GitHub access" \
  env -u GITHUB_TOKEN -u GH_TOKEN PATH="/usr/bin:/bin" python3 "$CM" github check
check_status "missing GitHub access exits 3" 3 \
  env -u GITHUB_TOKEN -u GH_TOKEN PATH="/usr/bin:/bin" python3 "$CM" github check
check "the api backend asks for a token" "GITHUB_TOKEN" \
  env -u GITHUB_TOKEN -u GH_TOKEN python3 "$CM" github check --backend api

printf '#!/usr/bin/env bash\necho "To get started with GitHub CLI, please run: gh auth login" >&2\nexit 4\n' \
  > "$WORK/bin/gh-unauthenticated"
chmod +x "$WORK/bin/gh-unauthenticated"
mkdir -p "$WORK/unauth"
cp "$WORK/bin/gh-unauthenticated" "$WORK/unauth/gh"
check "an unauthenticated gh says how to fix it" "run \`gh auth login\`" \
  env PATH="$WORK/unauth:/usr/bin:/bin" python3 "$CM" github check
check_status "an unauthenticated gh exits 3" 3 \
  env PATH="$WORK/unauth:/usr/bin:/bin" python3 "$CM" github check

# --- proactive memory (v0.3) -----------------------------------------------
# Anchored on calendar weeks rather than "N days ago", so the suite gives the
# same answers whatever weekday it runs on.
export CAREER_MEMORY_HOME="$WORK/proactive"
run init >/dev/null

iso() { python3 -c "import datetime as d,sys; x=d.date.fromisoformat(sys.argv[1]); y,w,_=x.isocalendar(); print(f'{y}-W{w:02d}')" "$1"; }
offset() { python3 -c "import datetime as d,sys; t=d.date.today(); print(t-d.timedelta(days=t.weekday())+d.timedelta(days=int(sys.argv[1])))" "$1"; }

THIS_MON="$(offset 0)"
LAST_MON="$(offset -7)"; LAST_WED="$(offset -5)"
LAST_WEEK_LABEL="$(iso "$LAST_MON")"
THIS_WEEK_LABEL="$(iso "$THIS_MON")"
LONG_AGO="$(day 70)"

run add "Shipped the payments dashboard" --date "$THIS_MON" --type delivery \
  --project payments --tags reliability --evidence 'github_pr:#12' \
  --impact "Support stopped exporting CSVs by hand" >/dev/null
run add "Mentored Ana through her first migration" --date "$LAST_WED" \
  --type leadership --project platform --people Ana >/dev/null
run add "Older caching work" --date "$LONG_AGO" --type delivery --project cache >/dev/null
run add "Reviewed the auth rewrite" --date "$(day 30)" --type collaboration \
  --project auth --status candidate --id stale-candidate >/dev/null

check_status "init creates outputs/summaries" 0 test -d "$WORK/proactive/outputs/summaries"

# --- summary ---------------------------------------------------------------
check "summary names the current week" "Week $THIS_WEEK_LABEL (in progress)" run summary
check "summary counts what was recorded" "1 entry recorded" run summary
check "summary compares with the same slice of the previous week" \
  "previous period $LAST_WEEK_LABEL" run summary
check "summary reports evidence coverage" "Evidence attached: 1/1" run summary
check "summary suggests the period file" "outputs/summaries/$THIS_WEEK_LABEL.md" run summary
check "summary of a past week finds its entry" "Mentored Ana" run summary --window last-week
check "summary flags entries without impact" "without a documented impact" \
  run summary --window last-week
check "summary names pending candidates" "candidate(s) awaiting confirmation" \
  run summary --from "$LONG_AGO" --to "$THIS_MON"
check "an empty period is reported as empty" "Nothing was recorded in this period" \
  run summary --from 2020-01-06 --to 2020-01-12
check "an empty period does not read as an idle week" "not about the work" \
  run summary --from 2020-01-06 --to 2020-01-12
check "period shorthand selects the month" "Month" run summary --period month
check "explicit ranges still work" "2020-01-06 → 2020-01-12" \
  run summary --from 2020-01-06 --to 2020-01-12
check "project filter narrows the summary" "project: platform" \
  run summary --window last-week --project platform

check "markdown output is a document" "# Weekly summary" run summary --window last-week --format markdown
check "markdown output warns against invention" "Do not add anything" \
  run summary --window last-week --format markdown
check "markdown records missing impact honestly" "Impact: not documented" \
  run summary --window last-week --format markdown
check "monthly markdown is labelled monthly" "# Monthly summary" \
  run summary --window this-month --format markdown
check "json output carries the period label" "\"label\": \"$THIS_WEEK_LABEL\"" \
  run summary --format json
check "json output carries the suggested path" '"output_path"' run summary --format json

# --- gaps ------------------------------------------------------------------
check "gaps finds entries with no evidence" "No evidence attached" run gaps
check "gaps names the entry, not just the id" "Mentored Ana through her first migration" run gaps
check "gaps prints the command that fixes it" "--add-evidence" run gaps
check "gaps finds entries with no impact" "No impact documented" run gaps
check_absent "a complete entry is not a gap" "Shipped the payments dashboard" run gaps
check "gaps finds candidates left waiting" "Candidate still awaiting" run gaps
check "stale-days controls what counts as waiting" "Nothing missing in this window" \
  run gaps --kind stale-candidate --stale-days 90
check "gaps finds stretches with nothing recorded" "consecutive weeks with nothing recorded" \
  run gaps --kind quiet-period
check "a quiet stretch suggests looking at GitHub" "github discover --from" \
  run gaps --kind quiet-period
check "kind filter narrows the report" "No evidence attached" run gaps --kind no-evidence
check_absent "kind filter excludes other kinds" "No impact documented" run gaps --kind no-evidence
check "gaps is about the record, not the work" "record cannot prove" run gaps
check "gaps json is parseable" '"kind": "no-evidence"' run gaps --kind no-evidence --format json

printf '\n## Competencies\n\n- payments\n- quantum tunnelling\n' >> "$WORK/proactive/profile.md"
check "an unevidenced competency is reported" "quantum tunnelling" \
  run gaps --kind uncovered-competency
check_absent "an evidenced competency is not" "payments" run gaps --kind uncovered-competency
check "the competency check points at a search" 'search "quantum tunnelling"' \
  run gaps --kind uncovered-competency
printf '\n## Compet\xc3\xaancias\n\n- design de sistemas\n' >> "$WORK/proactive/profile.md"
check "an accented competency heading is read too" "design de sistemas" \
  run gaps --kind uncovered-competency

# --- checkup ---------------------------------------------------------------
check "checkup reports the last capture" "Last capture:" run checkup
check "checkup compares this week with last" "this week: 1   last week: 1" run checkup
check "checkup lists the week that has no summary" "$LAST_WEEK_LABEL" run checkup
check "checkup lists pending candidates" "stale-candidate" run checkup
check "checkup counts gaps by kind" "No evidence attached" run checkup
check "checkup suggests a next step" "--format markdown" run checkup
check_absent "checkup never writes" "Recorded:" run checkup
check "checkup json is parseable" '"summaries_due"' run checkup --format json

printf '# Weekly summary\n' > "$WORK/proactive/outputs/summaries/$LAST_WEEK_LABEL.md"
check_absent "a written summary stops being due" "$LAST_WEEK_LABEL" run checkup
check "months are checked as well as weeks" "month " run checkup --months 6 --weeks 0

run promote stale-candidate >/dev/null
check "a confirmed candidate stops being pending" "none" run checkup

# GitHub discovery reaches the checkup through the same fake gh.
export CAREER_MEMORY_HOME="$WORK/gh-store2"
check "checkup can look for uncaptured GitHub work" "not in the record yet" \
  run checkup --github --github-days 400
check "checkup shows the reference it found" "acme/ledger#77" \
  run checkup --github --github-days 400
check_absent "already-linked work is not offered again" "acme/payments#123" \
  run checkup --github --github-days 400
check "checkup asks to show the user before importing" "show the user" \
  run checkup --github --github-days 400
check "no GitHub access degrades instead of failing" "unavailable" \
  env -u GITHUB_TOKEN -u GH_TOKEN PATH="/usr/bin:/bin" CAREER_MEMORY_HOME="$WORK/proactive" \
  python3 "$CM" checkup --github
check_status "no GitHub access still exits 0" 0 \
  env -u GITHUB_TOKEN -u GH_TOKEN PATH="/usr/bin:/bin" CAREER_MEMORY_HOME="$WORK/proactive" \
  python3 "$CM" checkup --github

# The proactive commands must survive without PyYAML like everything else.
check "summary works without PyYAML" "Mentored Ana" \
  env PYTHONPATH="$WORK/noyaml" CAREER_MEMORY_HOME="$WORK/proactive" \
  python3 "$CM" summary --window last-week
check "gaps works without PyYAML" "No evidence attached" \
  env PYTHONPATH="$WORK/noyaml" CAREER_MEMORY_HOME="$WORK/proactive" python3 "$CM" gaps
check "checkup works without PyYAML" "Last capture:" \
  env PYTHONPATH="$WORK/noyaml" CAREER_MEMORY_HOME="$WORK/proactive" python3 "$CM" checkup

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
