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

# --- add -------------------------------------------------------------------
check "add writes an entry" "Recorded:" run add "Resolved payment race condition" \
  --date "$TODAY" --type problem-solving --project payments \
  --tags debugging,reliability --evidence 'github_pr:#1234' \
  --body "Fixed a race condition in payment processing."
check_status "entry file exists" 0 test -f "$WORK/store/entries/$TODAY-resolved-payment-race-condition.md"

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

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
