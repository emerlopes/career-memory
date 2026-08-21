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

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
