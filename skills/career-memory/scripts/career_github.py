#!/usr/bin/env python3
"""career_github.py — read-only GitHub discovery for Career Memory.

v0.2 of the skill turns GitHub activity into *candidate* evidence. Nothing in
this module writes to GitHub, and nothing here writes to the store: it only
finds signals and normalises them. Whether a signal becomes career memory stays
the user's decision, which is why imports always land as candidates.

Two backends, both dependency-free:

  gh   the GitHub CLI, using whatever account `gh auth login` set up (default)
  api  https://api.github.com with $GITHUB_TOKEN / $GH_TOKEN

$GITHUB_API_URL overrides the REST base URL (GitHub Enterprise); with the `gh`
backend the host comes from gh's own configuration instead.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API = "https://api.github.com"
USER_AGENT = "career-memory"
TIMEOUT = 30
MAX_PAGES = 10

KINDS = ("pr", "issue", "review", "commit")
# Commits are opt-in: a week of commits is not a week of career evidence.
DEFAULT_KINDS = ("pr", "issue", "review")

EVIDENCE_TYPE = {
    "pr": "github_pr",
    "issue": "github_issue",
    "review": "github_review",
    "commit": "github_commit",
}

BY_FIELDS = ("created", "updated", "merged", "closed")


class GitHubError(RuntimeError):
    """GitHub is unreachable, unauthenticated, or refused the request."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class Client:
    def __init__(self, backend: str = "auto", base_url: str | None = None,
                 token: str | None = None):
        self.base_url = (
            base_url or os.environ.get("GITHUB_API_URL") or DEFAULT_API
        ).rstrip("/")
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.backend = self._pick(backend)
        self._login: str | None = None

    def _pick(self, backend: str) -> str:
        if backend == "gh":
            if not shutil.which("gh"):
                raise GitHubError(
                    "the GitHub CLI (`gh`) is not on PATH; install it or use --backend api"
                )
            return "gh"
        if backend == "api":
            if not self.token:
                raise GitHubError(
                    "--backend api needs a token in $GITHUB_TOKEN or $GH_TOKEN"
                )
            return "api"
        if shutil.which("gh"):
            return "gh"
        if self.token:
            return "api"
        raise GitHubError(
            "no GitHub access. Either install the GitHub CLI and run `gh auth login`, "
            "or export GITHUB_TOKEN with a read-only token."
        )

    # -- transport ----------------------------------------------------------

    def get(self, path: str, params: dict | None = None):
        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(
                params, quote_via=urllib.parse.quote, safe=":"
            )
        if self.backend == "gh":
            return self._get_gh(path + query)
        return self._get_api(path + query)

    def _get_gh(self, path: str):
        try:
            proc = subprocess.run(
                ["gh", "api", path],
                capture_output=True, text=True, timeout=TIMEOUT,
            )
        except FileNotFoundError:
            raise GitHubError("the GitHub CLI (`gh`) disappeared from PATH")
        except subprocess.TimeoutExpired:
            raise GitHubError(f"gh api {path} timed out after {TIMEOUT}s")
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            message = detail[0] if detail else f"exit {proc.returncode}"
            if re.search(r"auth|logged in|credential", message, re.I):
                raise GitHubError(
                    "the GitHub CLI is not authenticated — run `gh auth login`"
                )
            raise GitHubError(f"gh api {path}: {message}")
        try:
            return json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            raise GitHubError(f"gh api {path}: response was not JSON")

    def _get_api(self, path: str):
        url = f"{self.base_url}/{path.lstrip('/')}"
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {self.token}",
        })
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            hint = ""
            if exc.code in (401, 403):
                hint = " — check the token's scopes, or that it has not expired"
            if exc.code == 403 and "rate" in str(exc.headers.get("X-RateLimit-Remaining", "")):
                hint = " — rate limited; try again later"
            raise GitHubError(f"GET {url} failed: {exc.code} {exc.reason}{hint}")
        except urllib.error.URLError as exc:
            raise GitHubError(f"GET {url} failed: {exc.reason}")

    # -- identity -----------------------------------------------------------

    def login(self) -> str:
        if self._login is None:
            data = self.get("user")
            login = str((data or {}).get("login") or "").strip()
            if not login:
                raise GitHubError("could not resolve the authenticated GitHub user")
            self._login = login
        return self._login

    def describe(self) -> str:
        where = "gh CLI" if self.backend == "gh" else self.base_url
        return f"backend: {self.backend} ({where})"


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def _range(field: str, since: str | None, until: str | None) -> str:
    if since and until:
        return f"{field}:{since}..{until}"
    if since:
        return f"{field}:>={since}"
    if until:
        return f"{field}:<={until}"
    return ""


def _scope(repo: str | None, org: str | None, visibility: str) -> list[str]:
    bits = []
    if repo:
        bits.append(f"repo:{repo}")
    if org:
        bits.append(f"org:{org}")
    if visibility == "public":
        bits.append("is:public")
    elif visibility == "private":
        bits.append("is:private")
    return bits


def _search(client: Client, path: str, query: str, limit: int) -> list[dict]:
    items: list[dict] = []
    per_page = max(1, min(100, limit))
    for page in range(1, MAX_PAGES + 1):
        payload = client.get(path, {
            "q": query, "per_page": per_page, "page": page,
            "sort": "updated", "order": "desc",
        })
        batch = (payload or {}).get("items") or []
        items.extend(batch)
        if len(items) >= limit or len(batch) < per_page:
            break
    return items[:limit]


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

def _repo_from_api_url(url: str) -> str:
    parts = [p for p in str(url or "").rstrip("/").split("/") if p]
    return "/".join(parts[-2:]) if len(parts) >= 2 else ""


def _labels(item: dict) -> list[str]:
    out = []
    for label in item.get("labels") or []:
        name = label.get("name") if isinstance(label, dict) else label
        if name:
            out.append(str(name))
    return out


def _day(value) -> str:
    return str(value or "")[:10]


def _signal(kind: str, repo: str, ref: str, title: str, url: str, date: str,
            state: str, **extra) -> dict:
    signal = {
        "kind": kind,
        "repo": repo,
        "ref": ref,
        "title": title.strip(),
        "url": url,
        "date": date,
        "state": state,
        "evidence_type": EVIDENCE_TYPE[kind],
        "labels": [],
        "author": "",
    }
    signal.update(extra)
    return signal


def find_pulls(client, login, since, until, repo, org, visibility, by, limit):
    field = by if by in BY_FIELDS else "created"
    query = " ".join(filter(None, [
        "is:pr", f"author:{login}", _range(field, since, until),
        *_scope(repo, org, visibility),
    ]))
    signals = []
    for item in _search(client, "search/issues", query, limit):
        repo_full = _repo_from_api_url(item.get("repository_url"))
        number = item.get("number")
        pull = item.get("pull_request") or {}
        merged = _day(pull.get("merged_at"))
        state = "merged" if merged else ("draft" if item.get("draft") else str(item.get("state") or ""))
        signals.append(_signal(
            "pr", repo_full, f"{repo_full}#{number}",
            str(item.get("title") or ""), str(item.get("html_url") or ""),
            merged or _day(item.get("closed_at")) or _day(item.get("created_at")),
            state,
            number=number,
            labels=_labels(item),
            author=str((item.get("user") or {}).get("login") or ""),
            body=str(item.get("body") or ""),
            merged_at=merged,
            created_at=_day(item.get("created_at")),
        ))
    return signals


def find_issues(client, login, since, until, repo, org, visibility, by, limit):
    field = by if by in ("created", "updated", "closed") else "created"
    query = " ".join(filter(None, [
        "is:issue", f"author:{login}", _range(field, since, until),
        *_scope(repo, org, visibility),
    ]))
    signals = []
    for item in _search(client, "search/issues", query, limit):
        repo_full = _repo_from_api_url(item.get("repository_url"))
        number = item.get("number")
        signals.append(_signal(
            "issue", repo_full, f"{repo_full}#{number}",
            str(item.get("title") or ""), str(item.get("html_url") or ""),
            _day(item.get("closed_at")) or _day(item.get("created_at")),
            str(item.get("state") or ""),
            number=number,
            labels=_labels(item),
            author=str((item.get("user") or {}).get("login") or ""),
            body=str(item.get("body") or ""),
            created_at=_day(item.get("created_at")),
        ))
    return signals


def find_reviews(client, login, since, until, repo, org, visibility, by, limit):
    """Pull requests the user reviewed, excluding their own.

    The search index knows *that* the user reviewed a PR, not when. The date
    recorded is therefore the PR's last update inside the window — honest, and
    the entry body says so.
    """
    query = " ".join(filter(None, [
        "is:pr", f"reviewed-by:{login}", f"-author:{login}",
        _range("updated", since, until), *_scope(repo, org, visibility),
    ]))
    signals = []
    for item in _search(client, "search/issues", query, limit):
        repo_full = _repo_from_api_url(item.get("repository_url"))
        number = item.get("number")
        pull = item.get("pull_request") or {}
        signals.append(_signal(
            "review", repo_full, f"{repo_full}#{number}",
            str(item.get("title") or ""), str(item.get("html_url") or ""),
            _day(item.get("updated_at")) or _day(item.get("created_at")),
            "merged" if pull.get("merged_at") else str(item.get("state") or ""),
            number=number,
            labels=_labels(item),
            author=str((item.get("user") or {}).get("login") or ""),
            date_is_proxy=True,
        ))
    return signals


def find_commits(client, login, since, until, repo, org, visibility, by, limit):
    query = " ".join(filter(None, [
        f"author:{login}", _range("committer-date", since, until),
        *_scope(repo, org, visibility),
    ]))
    signals = []
    for item in _search(client, "search/commits", query, limit):
        repo_full = str((item.get("repository") or {}).get("full_name") or "")
        commit = item.get("commit") or {}
        sha = str(item.get("sha") or "")[:7]
        message = str(commit.get("message") or "").strip().splitlines()
        signals.append(_signal(
            "commit", repo_full, f"{repo_full}@{sha}",
            message[0] if message else sha,
            str(item.get("html_url") or ""),
            _day((commit.get("author") or {}).get("date")),
            "",
            sha=sha,
            author=str((item.get("author") or {}).get("login") or login),
        ))
    return signals


FINDERS = {
    "pr": find_pulls,
    "issue": find_issues,
    "review": find_reviews,
    "commit": find_commits,
}


def discover(client: Client, login: str, since: str | None, until: str | None,
             kinds=DEFAULT_KINDS, repo=None, org=None, visibility="all",
             by="created", limit=50) -> list[dict]:
    signals: list[dict] = []
    for kind in kinds:
        finder = FINDERS.get(kind)
        if not finder:
            raise GitHubError(f"unknown kind {kind!r} (known: {', '.join(KINDS)})")
        signals.extend(
            finder(client, login, since, until, repo, org, visibility, by, limit)
        )
    signals.sort(key=lambda s: (s.get("date") or "", s.get("ref") or ""), reverse=True)
    return signals


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------

URL_RE = re.compile(
    r"^https?://[^/]+/([^/\s]+)/([^/\s]+)/(pull|issues|commit|commits)/([^/?#\s]+)(.*)$",
    re.I,
)
SHORT_RE = re.compile(r"^([\w.-]+)/([\w.-]+)(#(\d+)|@([0-9a-f]{7,40}))$", re.I)


def parse_reference(value: str) -> dict | None:
    """Turn a GitHub URL or owner/repo#123 / owner/repo@sha into an evidence stub."""
    text = str(value or "").strip()
    if not text:
        return None

    match = URL_RE.match(text)
    if match:
        owner, repo, kind, ident, tail = match.groups()
        repo_full = f"{owner}/{repo}"
        if kind.lower().startswith("commit"):
            sha = ident[:7]
            return {
                "kind": "commit", "repo": repo_full, "ref": f"{repo_full}@{sha}",
                "url": text.split("#")[0], "sha": ident,
            }
        kind_name = "pr" if kind.lower() == "pull" else "issue"
        if kind_name == "pr" and re.search(r"#(pullrequestreview|discussion_r)", tail or "", re.I):
            kind_name = "review"
        return {
            "kind": kind_name, "repo": repo_full, "ref": f"{repo_full}#{ident}",
            "url": text.split("#")[0], "number": ident,
        }

    match = SHORT_RE.match(text)
    if match:
        owner, repo, _, number, sha = match.groups()
        repo_full = f"{owner}/{repo}"
        if number:
            return {
                "kind": "pr", "repo": repo_full, "ref": f"{repo_full}#{number}",
                "url": f"https://github.com/{repo_full}/pull/{number}",
                "number": number, "ambiguous": True,
            }
        short = sha[:7]
        return {
            "kind": "commit", "repo": repo_full, "ref": f"{repo_full}@{short}",
            "url": f"https://github.com/{repo_full}/commit/{sha}", "sha": sha,
        }
    return None


def normalise_reference(value: str) -> str:
    """Collapse a URL and its owner/repo#123 form to the same key."""
    text = str(value or "").strip().lower().rstrip("/")
    parsed = parse_reference(text)
    if parsed:
        return parsed["ref"].lower()
    return text


def fetch_title(client: Client, parsed: dict) -> tuple[str, dict]:
    """Look up the title of a referenced PR/issue/commit. Returns (title, meta)."""
    repo = parsed.get("repo")
    if parsed["kind"] == "commit":
        data = client.get(f"repos/{repo}/commits/{parsed.get('sha')}")
        message = str(((data or {}).get("commit") or {}).get("message") or "")
        first = message.strip().splitlines()
        return (first[0] if first else ""), {"url": str((data or {}).get("html_url") or "")}
    data = client.get(f"repos/{repo}/issues/{parsed.get('number')}")
    title = str((data or {}).get("title") or "")
    meta = {"url": str((data or {}).get("html_url") or "")}
    if parsed.get("ambiguous"):
        # /issues/N answers for both; the payload says which one it really is.
        meta["kind"] = "pr" if (data or {}).get("pull_request") else "issue"
    return title, meta
