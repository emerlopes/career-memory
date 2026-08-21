#!/usr/bin/env bash
# A stand-in for the GitHub CLI, so the discovery path is testable offline.
# Answers exactly the endpoints career_github.py asks for, from tests/fixtures.
set -euo pipefail

if [[ "${1:-}" != "api" ]]; then
  echo "fake gh: unsupported command: $*" >&2
  exit 1
fi

path="${2:-}"
fixtures="${FAKE_GH_FIXTURES:?FAKE_GH_FIXTURES is not set}"

case "$path" in
  user) cat "$fixtures/user.json" ;;
  search/commits*) cat "$fixtures/commits.json" ;;
  search/issues*reviewed-by*) cat "$fixtures/reviews.json" ;;
  search/issues*is:issue*) cat "$fixtures/issues.json" ;;
  search/issues*is:pr*) cat "$fixtures/prs.json" ;;
  repos/*/issues/*) cat "$fixtures/issue-detail.json" ;;
  *) echo "fake gh: unexpected path: $path" >&2; exit 1 ;;
esac
