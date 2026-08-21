#!/usr/bin/env python3
"""career_memory.py — deterministic storage layer for the Career Memory skill.

Career Memory is plain Markdown with YAML front matter. This CLI exists so the
agent never has to hand-write front matter, guess an id, or grep its way through
a growing store: those parts are mechanical and deserve to be exact.

No third-party dependencies. PyYAML is used when installed, otherwise a small
built-in parser handles the subset of YAML this schema uses.

Store resolution order:
  1. --dir
  2. $CAREER_MEMORY_HOME
  3. ./career-memory  (when it looks like a store)
  4. ~/career-memory
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

VERSION = "0.3.0"

ENTRY_TYPES = [
    "achievement",
    "delivery",
    "impact",
    "problem-solving",
    "feedback",
    "learning",
    "leadership",
    "collaboration",
]

EVIDENCE_TYPES = [
    "github_pr",
    "github_issue",
    "github_commit",
    "github_review",
    "document",
    "metric",
    "dashboard",
    "feedback",
    "email",
    "slack_message",
    "meeting",
    "ticket",
    "external_link",
]

CONFIDENCE = ["factual", "inferred", "uncertain"]

STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "de", "do", "da", "for", "from", "in",
    "into", "it", "of", "on", "or", "que", "the", "that", "this", "to", "with",
    "was", "were", "my", "i",
}


# ---------------------------------------------------------------------------
# Minimal YAML (only what the entry schema uses)
# ---------------------------------------------------------------------------

def _yaml_load(text: str) -> dict:
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        return _mini_yaml_load(text)


def _scalar(raw: str):
    raw = raw.strip()
    if not raw:
        return ""
    if raw[0] in "\"'" and raw[-1] == raw[0] and len(raw) > 1:
        return raw[1:-1]
    low = raw.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw


def _mini_yaml_load(text: str) -> dict:
    """Parse the flat maps, string lists, and lists-of-maps used by entries."""
    root: dict = {}
    # stack of (indent, container, kind) where kind is "map" or "list"
    stack = [(-1, root, "map")]
    pending_list_item = None  # dict being filled by "- key: value" continuation

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
            pending_list_item = None
        container = stack[-1][1]

        if line.startswith("- "):
            item = line[2:].strip()
            if not isinstance(container, list):
                continue
            if ":" in item and not item.startswith(("\"", "'")):
                key, _, value = item.partition(":")
                pending_list_item = {key.strip(): _scalar(value)}
                container.append(pending_list_item)
            else:
                container.append(_scalar(item))
                pending_list_item = None
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if pending_list_item is not None and isinstance(container, list):
                pending_list_item[key] = _scalar(value)
                continue
            if not isinstance(container, dict):
                continue
            if value == "":
                # Could open either a list or a nested map; decide lazily.
                child: dict = {}
                container[key] = child
                stack.append((indent, child, "map"))
            else:
                container[key] = _scalar(value)
        # Anything else is ignored on purpose: entries stay readable, not clever.

    # Empty nested maps that only ever received "- " children were turned into
    # lists by the branch above; normalise leftovers.
    return _normalise_empty(root)


def _normalise_empty(node):
    if isinstance(node, dict):
        return {k: _normalise_empty(v) for k, v in node.items()}
    return node


def _mini_yaml_load_lists(text: str) -> dict:
    """Second pass: attach list children to their parent key."""
    data = _mini_yaml_load(text)
    lines = text.splitlines()
    for idx, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped.endswith(":") or stripped.startswith("- "):
            continue
        key_path = stripped[:-1].strip()
        indent = len(raw_line) - len(raw_line.lstrip())
        items = []
        item = None
        for follow in lines[idx + 1:]:
            if not follow.strip():
                continue
            f_indent = len(follow) - len(follow.lstrip())
            if f_indent <= indent:
                break
            body = follow.strip()
            if body.startswith("- "):
                content = body[2:].strip()
                if ":" in content and not content.startswith(("\"", "'")):
                    k, _, v = content.partition(":")
                    item = {k.strip(): _scalar(v)}
                    items.append(item)
                else:
                    items.append(_scalar(content))
                    item = None
            elif item is not None and ":" in body:
                k, _, v = body.partition(":")
                item[k.strip()] = _scalar(v)
        if items:
            _set_path(data, key_path, items)
    return data


def _set_path(data: dict, key: str, value) -> None:
    if key in data:
        data[key] = value
        return
    for v in data.values():
        if isinstance(v, dict):
            _set_path(v, key, value)


def _yaml_dump(data: dict) -> str:
    out = []

    def fmt(value) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return '""'
        text = str(value)
        if text == "":
            return '""'
        if re.search(r"^[-?:,\[\]{}#&*!|>'\"%@`]|: |#|\n|^\s|\s$", text) or text.lower() in (
            "true", "false", "yes", "no", "null", "~"
        ):
            return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'
        return text

    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            out.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        if v in (None, ""):
                            continue
                        prefix = "  - " if first else "    "
                        out.append(f"{prefix}{k}: {fmt(v)}")
                        first = False
                else:
                    out.append(f"  - {fmt(item)}")
        elif isinstance(value, dict):
            out.append(f"{key}:")
            for k, v in value.items():
                if v in (None, ""):
                    continue
                out.append(f"  {k}: {fmt(v)}")
        else:
            out.append(f"{key}: {fmt(value)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

SUBDIRS = ["entries", "candidates", "projects", "feedback", "outputs"]


def resolve_store(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("CAREER_MEMORY_HOME")
    if env:
        return Path(env).expanduser().resolve()
    local = Path.cwd() / "career-memory"
    if (local / "entries").is_dir() or (local / "profile.md").is_file():
        return local.resolve()
    return (Path.home() / "career-memory").resolve()


def require_store(path: Path) -> Path:
    if not (path / "entries").is_dir():
        die(
            f"No Career Memory store at {path}.\n"
            f"Run: career_memory.py init --dir {path}"
        )
    return path


def die(message: str, code: int = 1):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# Entry model
# ---------------------------------------------------------------------------

class Entry:
    def __init__(self, path: Path, meta: dict, body: str):
        self.path = path
        self.meta = meta
        self.body = body

    @property
    def id(self) -> str:
        return str(self.meta.get("id") or self.path.stem)

    @property
    def date(self) -> str:
        return str(self.meta.get("date") or "")

    @property
    def title(self) -> str:
        for line in self.body.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return self.id

    def field_list(self, key: str) -> list:
        value = self.meta.get(key) or []
        if isinstance(value, str):
            return [value]
        return list(value) if isinstance(value, list) else []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "title": self.title,
            "type": self.meta.get("type"),
            "project": self.meta.get("project"),
            "status": self.meta.get("status", "confirmed"),
            "tags": self.field_list("tags"),
            "skills": self.field_list("skills"),
            "people": self.field_list("people"),
            "evidence": self.meta.get("evidence") or [],
            "impact": self.meta.get("impact") or {},
            "path": str(self.path),
        }

    def render(self) -> str:
        return f"---\n{_yaml_dump(self.meta)}\n---\n\n{self.body.strip()}\n"


def read_entry(path: Path) -> Entry | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return Entry(path, {}, text)
    parts = text.split("---", 2)
    if len(parts) < 3:
        return Entry(path, {}, text)
    meta = _yaml_load(parts[1])
    if not meta or not any(isinstance(v, list) for v in meta.values()):
        # The mini parser needs its list pass; PyYAML already handled lists.
        try:
            import yaml  # noqa: F401
        except ImportError:
            meta = _mini_yaml_load_lists(parts[1])
    return Entry(path, meta or {}, parts[2])


def load_entries(store: Path, include_candidates: bool = False) -> list[Entry]:
    dirs = [store / "entries", store / "feedback"]
    if include_candidates:
        dirs.append(store / "candidates")
    entries = []
    for directory in dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.md")):
            entry = read_entry(path)
            if entry and entry.meta:
                entries.append(entry)
    entries.sort(key=lambda e: (e.date, e.id), reverse=True)
    return entries


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

def today() -> dt.date:
    return dt.date.today()


def parse_date(value: str | None) -> dt.date:
    if not value:
        return today()
    value = value.strip().lower()
    if value in ("today", "hoje"):
        return today()
    if value in ("yesterday", "ontem"):
        return today() - dt.timedelta(days=1)
    match = re.fullmatch(r"-?(\d+)([dwmy])", value)
    if match:
        return shift(today(), int(match.group(1)), match.group(2))
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        die(f"unrecognised date: {value!r} (use YYYY-MM-DD, today, yesterday, or 7d for 7 days ago)")


def shift(base: dt.date, amount: int, unit: str) -> dt.date:
    if unit == "d":
        return base - dt.timedelta(days=amount)
    if unit == "w":
        return base - dt.timedelta(weeks=amount)
    if unit == "m":
        return base - dt.timedelta(days=30 * amount)
    return base - dt.timedelta(days=365 * amount)


def parse_window(value: str | None) -> tuple[str | None, str | None]:
    """Turn a natural window ('last-quarter', '30d') into an ISO date range."""
    if not value:
        return None, None
    v = value.strip().lower().replace("_", "-").replace(" ", "-")
    now = today()
    if v in ("today", "hoje"):
        return now.isoformat(), now.isoformat()
    if v in ("yesterday", "ontem"):
        d = now - dt.timedelta(days=1)
        return d.isoformat(), d.isoformat()
    if v in ("this-week", "week"):
        start = now - dt.timedelta(days=now.weekday())
        return start.isoformat(), now.isoformat()
    if v == "last-week":
        start = now - dt.timedelta(days=now.weekday() + 7)
        return start.isoformat(), (start + dt.timedelta(days=6)).isoformat()
    if v in ("this-month", "month"):
        return now.replace(day=1).isoformat(), now.isoformat()
    if v == "last-month":
        first = now.replace(day=1)
        end = first - dt.timedelta(days=1)
        return end.replace(day=1).isoformat(), end.isoformat()
    if v in ("this-quarter", "quarter"):
        start_month = 3 * ((now.month - 1) // 3) + 1
        return now.replace(month=start_month, day=1).isoformat(), now.isoformat()
    if v == "last-quarter":
        start_month = 3 * ((now.month - 1) // 3) + 1
        this_start = now.replace(month=start_month, day=1)
        end = this_start - dt.timedelta(days=1)
        s_month = 3 * ((end.month - 1) // 3) + 1
        return end.replace(month=s_month, day=1).isoformat(), end.isoformat()
    if v in ("this-year", "year"):
        return now.replace(month=1, day=1).isoformat(), now.isoformat()
    if v == "last-year":
        return (
            now.replace(year=now.year - 1, month=1, day=1).isoformat(),
            now.replace(year=now.year - 1, month=12, day=31).isoformat(),
        )
    match = re.fullmatch(r"(\d+)([dwmy])", v)
    if match:
        return shift(now, int(match.group(1)), match.group(2)).isoformat(), now.isoformat()
    die(f"unrecognised window: {value!r} (try 7d, this-week, last-quarter; "
        f"for an exact range use --from/--to)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str, max_words: int = 6) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    words = [w for w in re.split(r"[^a-z0-9]+", text) if w]
    kept = [w for w in words if w not in STOPWORDS] or words
    return "-".join(kept[:max_words]) or "entry"


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_evidence(items: list[str]) -> list[dict]:
    """'github_pr:#1234', 'github_pr:https://...' or 'metric:latency:800ms -> 300ms'."""
    parsed = []
    for item in items:
        kind, _, rest = item.partition(":")
        kind = kind.strip()
        rest = rest.strip()
        if re.match(r"^https?://", rest):
            # A URL is one reference, not a reference plus a value.
            record = {"type": kind, "reference": rest}
        else:
            reference, _, value = rest.partition(":")
            record = {"type": kind, "reference": reference.strip()}
            if value.strip():
                record["value"] = value.strip()
        if kind not in EVIDENCE_TYPES:
            print(
                f"warning: evidence type {kind!r} is outside the known list "
                f"({', '.join(EVIDENCE_TYPES)})",
                file=sys.stderr,
            )
        parsed.append(record)
    return parsed


def tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 2 and t not in STOPWORDS}


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def find_duplicates(store: Path, title: str, date: dt.date, project: str | None,
                    window_days: int = 21,
                    entries: list[Entry] | None = None) -> list[tuple[float, Entry]]:
    hits = []
    if entries is None:
        entries = load_entries(store, include_candidates=True)
    for entry in entries:
        try:
            entry_date = dt.date.fromisoformat(entry.date)
        except ValueError:
            continue
        if abs((entry_date - date).days) > window_days:
            continue
        score = similarity(title, entry.title + " " + entry.body[:400])
        if project and entry.meta.get("project") == project:
            score += 0.1
        if score >= 0.3:
            hits.append((round(min(score, 1.0), 2), entry))
    return sorted(hits, key=lambda pair: pair[0], reverse=True)[:5]


def compose_entry(meta: dict, title: str, body: str = "") -> Entry:
    sections = [f"# {title}", ""]
    if body:
        sections += [body.strip(), ""]
    return Entry(Path(), meta, "\n".join(sections))


# ---------------------------------------------------------------------------
# GitHub (v0.2)
# ---------------------------------------------------------------------------

def github_module():
    """career_github.py lives next to this file; import it without side effects."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import career_github  # type: ignore
    except ImportError:
        die("career_github.py is missing next to career_memory.py")
    return career_github


def evidence_index(store: Path, entries: list[Entry] | None = None) -> dict[str, Entry]:
    """Every evidence reference already in the store, keyed by normalised form.

    A pull request recorded as a URL and the same pull request recorded as
    owner/repo#123 are the same evidence; discovery must not offer either twice.
    """
    gh = github_module()
    index: dict[str, Entry] = {}
    if entries is None:
        entries = load_entries(store, include_candidates=True)
    for entry in entries:
        evidence = entry.meta.get("evidence") or []
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            if not isinstance(item, dict):
                continue
            for key in ("reference", "url", "value"):
                raw = str(item.get(key) or "").strip()
                if raw:
                    index.setdefault(gh.normalise_reference(raw), entry)
    return index


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    store = resolve_store(args.dir)
    store.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (store / sub).mkdir(exist_ok=True)
    summaries_dir(store).mkdir(exist_ok=True)
    templates = Path(__file__).resolve().parent.parent / "templates"

    created = []
    profile = store / "profile.md"
    if not profile.exists():
        source = templates / "profile.md"
        profile.write_text(
            source.read_text(encoding="utf-8") if source.exists() else "# Career Profile\n",
            encoding="utf-8",
        )
        created.append("profile.md")
    readme = store / "README.md"
    if not readme.exists():
        readme.write_text(STORE_README, encoding="utf-8")
        created.append("README.md")

    print(f"Career Memory store ready at {store}")
    print("  " + "  ".join(f"{s}/" for s in SUBDIRS))
    if created:
        print("  created: " + ", ".join(created))
    if not args.dir and not os.environ.get("CAREER_MEMORY_HOME"):
        print(f"\nTip: export CAREER_MEMORY_HOME={store} to pin this location.")
    return 0


def cmd_add(args) -> int:
    store = require_store(resolve_store(args.dir))
    date = parse_date(args.date)
    status = args.status
    entry_id = args.id or f"{date.isoformat()}-{slugify(args.title)}"

    if args.type and args.type not in ENTRY_TYPES:
        print(
            f"warning: type {args.type!r} is outside the known list "
            f"({', '.join(ENTRY_TYPES)})",
            file=sys.stderr,
        )

    duplicates = find_duplicates(store, args.title, date, args.project)
    if duplicates and not args.force:
        print("Possible duplicates of an existing entry:")
        for score, entry in duplicates:
            print(f"  [{score}] {entry.id}  ({entry.date})  {entry.title}")
        print(
            "\nNothing was written. Update one of those with `update`, "
            "or re-run `add --force` if this really is a separate event."
        )
        return 2

    body = args.body
    if body == "-":
        body = sys.stdin.read()

    meta = {
        "id": entry_id,
        "date": date.isoformat(),
        "type": args.type or "achievement",
        "project": args.project,
        "status": status,
        "tags": split_csv(args.tags),
        "skills": split_csv(args.skills),
        "people": split_csv(args.people),
        "evidence": parse_evidence(args.evidence or []),
    }
    if args.impact:
        meta["impact"] = {
            "statement": args.impact,
            "confidence": args.impact_confidence,
        }
    if args.context:
        meta["context"] = args.context
    if args.source:
        meta["source"] = args.source

    entry = compose_entry(meta, args.title, body)

    folder = "candidates" if status == "candidate" else (
        "feedback" if args.type == "feedback" else "entries"
    )
    path = store / folder / f"{entry_id}.md"
    if path.exists() and not args.force:
        die(f"{path} already exists (use --force to overwrite or `update` to amend)")
    path.write_text(entry.render(), encoding="utf-8")

    print(f"Recorded: {path}")
    print(f"  type: {meta['type']}   date: {meta['date']}   status: {status}")
    if meta["evidence"]:
        print("  evidence: " + ", ".join(
            f"{e['type']} {e.get('reference', '')}".strip() for e in meta["evidence"]
        ))
    else:
        print("  evidence: none recorded")
    if "impact" not in meta:
        print("  impact: not documented")
    return 0


def _filter(entries: list[Entry], args) -> list[Entry]:
    date_from, date_to = (None, None)
    if getattr(args, "window", None):
        date_from, date_to = parse_window(args.window)
    if getattr(args, "date_from", None):
        date_from = parse_date(args.date_from).isoformat()
    if getattr(args, "date_to", None):
        date_to = parse_date(args.date_to).isoformat()

    result = []
    for entry in entries:
        if date_from and entry.date and entry.date < date_from:
            continue
        if date_to and entry.date and entry.date > date_to:
            continue
        if getattr(args, "type", None) and entry.meta.get("type") != args.type:
            continue
        if getattr(args, "project", None) and entry.meta.get("project") != args.project:
            continue
        if getattr(args, "status", None) and str(entry.meta.get("status", "confirmed")) != args.status:
            continue
        if getattr(args, "tag", None) and args.tag not in entry.field_list("tags"):
            continue
        if getattr(args, "skill", None) and args.skill not in entry.field_list("skills"):
            continue
        if getattr(args, "person", None) and args.person not in entry.field_list("people"):
            continue
        result.append(entry)
    return result


def _output(entries: list[Entry], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2, ensure_ascii=False))
        return
    if fmt == "paths":
        for entry in entries:
            print(entry.path)
        return
    if fmt == "full":
        for entry in entries:
            print(f"===== {entry.path}")
            print(entry.render().strip())
            print()
        return
    if not entries:
        print("No entries matched.")
        return
    for entry in entries:
        meta = entry.meta
        bits = [entry.date, f"[{meta.get('type', '?')}]"]
        if meta.get("project"):
            bits.append(f"({meta['project']})")
        bits.append(entry.title)
        if str(meta.get("status", "confirmed")) != "confirmed":
            bits.append(f"<{meta.get('status')}>")
        print("  ".join(b for b in bits if b))
    print(f"\n{entry_count(len(entries))}")


def cmd_list(args) -> int:
    store = require_store(resolve_store(args.dir))
    entries = _filter(load_entries(store, args.include_candidates), args)
    if args.limit:
        entries = entries[: args.limit]
    _output(entries, args.format)
    return 0


def cmd_search(args) -> int:
    store = require_store(resolve_store(args.dir))
    entries = _filter(load_entries(store, args.include_candidates), args)
    query = args.query.lower()
    query_tokens = tokens(query)

    scored = []
    for entry in entries:
        haystack = " ".join([
            entry.title,
            entry.body,
            str(entry.meta.get("project") or ""),
            " ".join(entry.field_list("tags")),
            " ".join(entry.field_list("skills")),
            " ".join(entry.field_list("people")),
            str(entry.meta.get("type") or ""),
        ]).lower()
        score = 0.0
        if query in haystack:
            score += 1.0
        hits = sum(1 for token in query_tokens if token in haystack)
        if query_tokens:
            score += hits / len(query_tokens)
        if score > 0.15:
            scored.append((score, entry))

    scored.sort(key=lambda pair: (pair[0], pair[1].date), reverse=True)
    matched = [entry for _, entry in scored]
    if args.limit:
        matched = matched[: args.limit]
    _output(matched, args.format)
    return 0


def cmd_show(args) -> int:
    store = require_store(resolve_store(args.dir))
    for entry in load_entries(store, include_candidates=True):
        if entry.id == args.id or entry.path.stem == args.id:
            print(entry.render().strip())
            return 0
    die(f"no entry with id {args.id!r}")


def _locate(store: Path, entry_id: str) -> Entry:
    for entry in load_entries(store, include_candidates=True):
        if entry.id == entry_id or entry.path.stem == entry_id:
            return entry
    die(f"no entry with id {entry_id!r}")


def cmd_update(args) -> int:
    store = require_store(resolve_store(args.dir))
    entry = _locate(store, args.id)
    meta = entry.meta
    changes = []

    if args.add_evidence:
        existing = meta.get("evidence") or []
        if not isinstance(existing, list):
            existing = []
        new_items = parse_evidence(args.add_evidence)
        for item in new_items:
            if item not in existing:
                existing.append(item)
                changes.append(f"evidence {item['type']} {item.get('reference', '')}".strip())
        meta["evidence"] = existing

    for field, values in (("tags", args.add_tag), ("skills", args.add_skill),
                          ("people", args.add_person)):
        if values:
            current = entry.field_list(field)
            for value in values:
                if value not in current:
                    current.append(value)
                    changes.append(f"{field}: +{value}")
            meta[field] = current

    if args.set_status:
        meta["status"] = args.set_status
        changes.append(f"status: {args.set_status}")
    if args.set_project:
        meta["project"] = args.set_project
        changes.append(f"project: {args.set_project}")
    if args.set_impact:
        meta["impact"] = {
            "statement": args.set_impact,
            "confidence": args.impact_confidence,
        }
        changes.append("impact recorded")

    body = entry.body
    if args.append:
        text = sys.stdin.read() if args.append == "-" else args.append
        body = body.rstrip() + "\n\n" + text.strip() + "\n"
        changes.append("body appended")

    if not changes:
        print("Nothing to update.")
        return 0

    updated = Entry(entry.path, meta, body)
    entry.path.write_text(updated.render(), encoding="utf-8")
    print(f"Updated: {entry.path}")
    for change in changes:
        print(f"  {change}")
    return 0


def cmd_promote(args) -> int:
    store = require_store(resolve_store(args.dir))
    entry = _locate(store, args.id)
    if entry.path.parent.name != "candidates":
        die(f"{entry.id} is not a candidate")
    entry.meta["status"] = "confirmed"
    target_dir = store / ("feedback" if entry.meta.get("type") == "feedback" else "entries")
    target = target_dir / entry.path.name
    target.write_text(Entry(target, entry.meta, entry.body).render(), encoding="utf-8")
    entry.path.unlink()
    print(f"Confirmed: {target}")
    return 0


def cmd_dismiss(args) -> int:
    store = require_store(resolve_store(args.dir))
    entry = _locate(store, args.id)
    if entry.path.parent.name != "candidates":
        die(f"{entry.id} is not a candidate; delete the file manually if you mean it")
    entry.path.unlink()
    print(f"Dismissed: {entry.id}")
    return 0


def cmd_stats(args) -> int:
    store = require_store(resolve_store(args.dir))
    entries = _filter(load_entries(store, include_candidates=False), args)
    if not entries:
        print("No entries in this window.")
        return 0

    print(f"{len(entries)} entries  ({entries[-1].date} → {entries[0].date})")
    for label, getter in (
        ("By type", lambda e: [e.meta.get("type")]),
        ("By project", lambda e: [e.meta.get("project")]),
        ("Top skills", lambda e: e.field_list("skills")),
        ("Top tags", lambda e: e.field_list("tags")),
        ("People", lambda e: e.field_list("people")),
    ):
        rows = tally(entries, getter)[:10]
        if rows:
            print(f"\n{label}:")
            for name, count in rows:
                print(f"  {count:>3}  {name}")

    with_evidence = sum(1 for e in entries if e.meta.get("evidence"))
    with_impact = sum(1 for e in entries if e.meta.get("impact"))
    print(f"\nEvidence attached: {with_evidence}/{len(entries)}")
    print(f"Impact documented: {with_impact}/{len(entries)}")
    return 0


def cmd_validate(args) -> int:
    store = require_store(resolve_store(args.dir))
    problems = 0
    seen_ids: dict[str, Path] = {}
    for entry in load_entries(store, include_candidates=True):
        issues = []
        if not entry.meta.get("id"):
            issues.append("missing id")
        if not entry.meta.get("date"):
            issues.append("missing date")
        else:
            try:
                dt.date.fromisoformat(entry.date)
            except ValueError:
                issues.append(f"date is not YYYY-MM-DD: {entry.date!r}")
        entry_type = entry.meta.get("type")
        if entry_type and entry_type not in ENTRY_TYPES:
            issues.append(f"unknown type: {entry_type!r}")
        status = str(entry.meta.get("status", "confirmed"))
        if status not in ("confirmed", "candidate", "dismissed"):
            issues.append(f"unknown status: {status!r}")
        impact = entry.meta.get("impact")
        if isinstance(impact, dict) and impact.get("statement"):
            if impact.get("confidence") not in CONFIDENCE:
                issues.append("impact.statement without a valid confidence")
        if entry.id in seen_ids:
            issues.append(f"duplicate id, also in {seen_ids[entry.id]}")
        else:
            seen_ids[entry.id] = entry.path
        if issues:
            problems += 1
            print(f"{entry.path}")
            for issue in issues:
                print(f"  - {issue}")
    if problems:
        print(f"\n{problems} file(s) need attention.")
        return 1
    print(f"All {len(seen_ids)} entries valid.")
    return 0


def cmd_where(args) -> int:
    store = resolve_store(args.dir)
    exists = (store / "entries").is_dir()
    print(store)
    if not exists:
        print("(not initialised — run `init`)", file=sys.stderr)
        return 1
    return 0


# ---------------------------------------------------------------------------
# GitHub commands (v0.2)
# ---------------------------------------------------------------------------

# Mechanical defaults. They are a starting point for the agent and the user to
# correct, never a claim about what the work meant.
GITHUB_ENTRY_TYPE = {
    "pr": "delivery",
    "commit": "delivery",
    "issue": "problem-solving",
    "review": "collaboration",
}

GITHUB_KIND_LABEL = {
    "pr": "pull requests",
    "issue": "issues",
    "review": "reviews",
    "commit": "commits",
}


def github_die(exc) -> None:
    """GitHub problems are environmental, so they get their own exit code."""
    print(f"error: {exc}", file=sys.stderr)
    sys.exit(3)


def _github_client(args):
    gh = github_module()
    try:
        return gh, gh.Client(backend=args.backend)
    except gh.GitHubError as exc:
        github_die(exc)


def _github_range(args) -> tuple[str | None, str | None]:
    # The default window applies only when no explicit range was given, so
    # `--to 2026-01-31` on its own does not silently start 30 days ago.
    return _range_from_args(args, "30d")


def _github_kinds(gh, raw: str) -> list[str]:
    kinds = split_csv(raw) or list(gh.DEFAULT_KINDS)
    unknown = [k for k in kinds if k not in gh.KINDS]
    if unknown:
        die(f"unknown kind(s): {', '.join(unknown)} (known: {', '.join(gh.KINDS)})")
    return kinds


def _github_signals(gh, client, args) -> tuple[str, list[dict], str | None, str | None]:
    since, until = _github_range(args)
    kinds = _github_kinds(gh, args.kinds)
    try:
        login = args.user or client.login()
        signals = gh.discover(
            client, login, since, until, kinds=kinds, repo=args.repo, org=args.org,
            visibility=args.visibility, by=args.by, limit=args.limit,
        )
    except gh.GitHubError as exc:
        github_die(exc)
    return login, signals, since, until


def _github_labels_to_tags(labels: list[str]) -> list[str]:
    tags = []
    for label in labels:
        name = str(label).strip().lower().replace(" ", "-")
        # size/L, status/blocked and friends describe the process, not the work.
        if not name or "/" in name or name in tags:
            continue
        tags.append(name)
    return tags[:6]


def _github_entry(signal: dict, project: str | None, with_body: bool) -> tuple[dict, str, str]:
    kind = signal["kind"]
    repo = signal.get("repo") or ""
    ref = signal.get("ref") or ""
    date = signal.get("date") or today().isoformat()
    state = signal.get("state") or ""
    url = signal.get("url") or ""
    title = (signal.get("title") or ref).strip()

    if kind == "review":
        title = f"Reviewed: {title}"
    elif kind == "issue":
        title = f"Opened issue: {title}"

    if kind == "pr":
        if state == "merged":
            line = f"Pull request {ref} — merged on {date}."
        else:
            opened = signal.get("created_at") or date
            line = f"Pull request {ref} — {state or 'open'}, opened {opened}."
    elif kind == "issue":
        opened = signal.get("created_at") or date
        line = f"Issue {ref} — {state or 'open'}, opened {opened}."
    elif kind == "review":
        author = signal.get("author")
        line = f"Reviewed pull request {ref}" + (f", opened by @{author}." if author else ".")
    else:
        line = f"Commit {ref} — {date}."

    body_lines = [line]
    if url:
        body_lines.append(url)
    if signal.get("date_is_proxy"):
        body_lines += [
            "",
            "GitHub search does not report when the review was submitted; this "
            "entry is dated from the pull request's last update in the window.",
        ]
    if with_body and signal.get("body"):
        excerpt = str(signal["body"]).strip()
        if len(excerpt) > 800:
            excerpt = excerpt[:800].rstrip() + "…"
        body_lines += ["", "## Context", "", excerpt, "",
                       "_(from the GitHub description, written by the user)_"]

    identifier = signal.get("number") or signal.get("sha") or slugify(ref)
    entry_id = f"{date}-{kind}-{slugify(repo.replace('/', '-'), max_words=4)}-{identifier}"

    meta = {
        "id": entry_id,
        "date": date,
        "type": GITHUB_ENTRY_TYPE.get(kind, "achievement"),
        "project": project or (repo.split("/")[-1] if repo else None),
        "status": "candidate",
        "tags": _github_labels_to_tags(signal.get("labels") or []),
        "people": [signal["author"]] if kind == "review" and signal.get("author") else [],
        "evidence": [{
            "type": signal.get("evidence_type") or "external_link",
            "reference": ref,
            "url": url,
            "title": (signal.get("title") or "").strip(),
        }],
        "source": "github",
    }
    return meta, title, "\n".join(body_lines)


def cmd_github_check(args) -> int:
    gh, client = _github_client(args)
    try:
        login = args.user or client.login()
    except gh.GitHubError as exc:
        github_die(exc)
    print(f"GitHub reachable as @{login}")
    print(f"  {client.describe()}")
    print("  read-only: discovery never writes to GitHub")
    store = resolve_store(args.dir)
    if not (store / "entries").is_dir():
        print(f"  store: not initialised at {store} (run `init` before importing)")
    else:
        print(f"  store: {store}")
    return 0


def cmd_github_discover(args) -> int:
    store = require_store(resolve_store(args.dir))
    gh, client = _github_client(args)
    login, signals, since, until = _github_signals(gh, client, args)
    captured = evidence_index(store)

    for signal in signals:
        match = captured.get(gh.normalise_reference(signal["ref"]))
        signal["captured_by"] = match.id if match else None

    if args.new_only:
        signals = [s for s in signals if not s["captured_by"]]

    if args.format == "json":
        print(json.dumps(signals, indent=2, ensure_ascii=False))
        return 0
    if args.format == "refs":
        for signal in signals:
            print(signal["ref"])
        return 0

    if since and until:
        window = f"{since} → {until}"
    elif since:
        window = f"since {since}"
    elif until:
        window = f"up to {until}"
    else:
        window = "all time"
    print(f"GitHub activity for @{login}  ({window})")
    if not signals:
        print("\nNothing found in this window.")
        return 0

    fresh = 0
    for kind in gh.KINDS:
        group = [s for s in signals if s["kind"] == kind]
        if not group:
            continue
        print(f"\n{GITHUB_KIND_LABEL[kind]}")
        for signal in group:
            marker = "saved" if signal["captured_by"] else "new"
            if not signal["captured_by"]:
                fresh += 1
            line = (f"  {marker:<5}  {signal['ref']:<34}  {signal['date']}  "
                    f"{(signal.get('state') or ''):<7}  {signal['title']}")
            if signal["captured_by"]:
                line += f"\n         → {signal['captured_by']}"
            print(line)

    print(f"\n{len(signals)} signal(s): {fresh} new, {len(signals) - fresh} already recorded.")
    if fresh:
        print("Import the new ones as candidates with `github import`, "
              "then confirm each with `promote`.")
    return 0


def cmd_github_import(args) -> int:
    store = require_store(resolve_store(args.dir))
    gh, client = _github_client(args)
    login, signals, _, _ = _github_signals(gh, client, args)
    known = load_entries(store, include_candidates=True)
    captured = evidence_index(store, known)

    imported, skipped, matches, failed = [], [], [], []
    for signal in signals:
        if gh.normalise_reference(signal["ref"]) in captured:
            skipped.append(signal)
            continue
        meta, title, body = _github_entry(signal, args.project, args.with_body)
        try:
            date = dt.date.fromisoformat(meta["date"])
        except ValueError:
            date = today()
        if not args.force:
            duplicates = find_duplicates(store, title, date, meta.get("project"),
                                         entries=known)
            if duplicates:
                matches.append((signal, duplicates[0][1]))
                continue
        path = store / "candidates" / f"{meta['id']}.md"
        if path.exists():
            skipped.append(signal)
            continue
        entry = compose_entry(meta, title, body)
        if not args.dry_run:
            try:
                path.write_text(entry.render(), encoding="utf-8")
            except OSError as exc:
                failed.append((signal, exc))
                continue
        # Two pull requests in one batch can describe the same work.
        known.append(Entry(path, meta, entry.body))
        imported.append((signal, meta, path))

    verb = "Would import" if args.dry_run else "Imported"
    print(f"{verb} {len(imported)} candidate(s) from @{login}'s GitHub activity.")
    for signal, meta, path in imported:
        print(f"  {meta['id']}  [{meta['type']}]  {signal['ref']}")
    if matches:
        print(f"\n{len(matches)} signal(s) look like work you already recorded — "
              f"link the evidence instead of duplicating the entry:")
        for signal, entry in matches:
            print(f"  {signal['ref']}  ~  {entry.id}")
            print(f"    github link {entry.id} {signal['ref']}")
    if skipped:
        print(f"\n{len(skipped)} signal(s) already recorded; left alone.")
    if failed:
        print(f"\n{len(failed)} signal(s) could not be written:", file=sys.stderr)
        for signal, exc in failed:
            print(f"  {signal['ref']}: {exc}", file=sys.stderr)
    if imported and not args.dry_run:
        print("\nThese are candidates, not career memory yet. Review each one with "
              "the user, then `promote <id>` or `dismiss <id>`.")
    return 1 if failed else 0


def cmd_github_link(args) -> int:
    store = require_store(resolve_store(args.dir))
    gh = github_module()
    entry = _locate(store, args.id)

    existing = entry.meta.get("evidence") or []
    if not isinstance(existing, list):
        existing = []
    known = {
        gh.normalise_reference(str(item.get("reference") or item.get("url") or ""))
        for item in existing if isinstance(item, dict)
    }

    client = None
    if not args.no_fetch:
        try:
            client = gh.Client(backend=args.backend)
        except gh.GitHubError as exc:
            print(f"warning: linking without titles ({exc})", file=sys.stderr)

    changes = []
    for raw in args.reference:
        parsed = gh.parse_reference(raw)
        if not parsed:
            die(f"unrecognised GitHub reference: {raw!r} "
                f"(use a URL, owner/repo#123 or owner/repo@sha)")
        kind = args.kind or parsed["kind"]
        title, url = "", parsed.get("url", "")
        if client is not None:
            try:
                title, meta = gh.fetch_title(client, parsed)
                url = meta.get("url") or url
                if not args.kind and meta.get("kind"):
                    kind = meta["kind"]
            except gh.GitHubError as exc:
                print(f"warning: could not read {parsed['ref']} ({exc})", file=sys.stderr)
        key = gh.normalise_reference(parsed["ref"])
        if key in known:
            print(f"  already linked: {parsed['ref']}")
            continue
        known.add(key)
        existing.append({
            "type": gh.EVIDENCE_TYPE.get(kind, "external_link"),
            "reference": parsed["ref"],
            "url": url,
            "title": title,
        })
        changes.append(f"evidence {gh.EVIDENCE_TYPE.get(kind, 'external_link')} {parsed['ref']}")

    if not changes:
        print("Nothing to link.")
        return 0

    entry.meta["evidence"] = existing
    entry.path.write_text(Entry(entry.path, entry.meta, entry.body).render(), encoding="utf-8")
    print(f"Updated: {entry.path}")
    for change in changes:
        print(f"  {change}")
    return 0


# ---------------------------------------------------------------------------
# Proactive memory (v0.3)
# ---------------------------------------------------------------------------

# Everything below reports on the record, never on the work. "No evidence
# attached" is a statement about a file, not about what the user did.

GAP_KINDS = (
    "no-evidence",
    "no-impact",
    "unverified-impact",
    "stale-candidate",
    "quiet-period",
    "uncovered-competency",
)

GAP_LABEL = {
    "no-evidence": "No evidence attached",
    "no-impact": "No impact documented",
    "unverified-impact": "Impact recorded but not confirmed",
    "stale-candidate": "Candidate still awaiting your confirmation",
    "quiet-period": "Stretch with nothing recorded",
    "uncovered-competency": "Competency with no matching entry",
}


def entry_count(n: int) -> str:
    return f"{n} entr{'y' if n == 1 else 'ies'}"


def week_range(day: dt.date) -> tuple[dt.date, dt.date]:
    start = day - dt.timedelta(days=day.weekday())
    return start, start + dt.timedelta(days=6)


def month_range(day: dt.date) -> tuple[dt.date, dt.date]:
    start = day.replace(day=1)
    following = (start.replace(year=start.year + 1, month=1) if start.month == 12
                 else start.replace(month=start.month + 1))
    return start, following - dt.timedelta(days=1)


def iso_week_label(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def month_label(day: dt.date) -> str:
    return f"{day.year}-{day.month:02d}"


def classify_period(since: str | None, until: str | None) -> dict:
    """Name a date range: a calendar week, a calendar month, or neither.

    A week that has not finished yet is still that week — labelled in progress,
    so a Wednesday summary never reads as a report on the whole week.
    """
    try:
        start = dt.date.fromisoformat(since or "")
        end = dt.date.fromisoformat(until or "")
    except ValueError:
        label = f"{since or '…'}_{until or '…'}"
        return {"label": label, "kind": "range", "partial": False,
                "title": f"{since or '…'} → {until or '…'}"}

    week_start, week_end = week_range(start)
    month_start, month_end = month_range(start)
    if start == week_start and end == week_end:
        kind, label, partial = "week", iso_week_label(start), False
    elif start == month_start and end == month_end:
        kind, label, partial = "month", month_label(start), False
    elif start == week_start and end < week_end and (end - start).days <= 6:
        kind, label, partial = "week", iso_week_label(start), True
    elif start == month_start and end < month_end:
        kind, label, partial = "month", month_label(start), True
    else:
        return {"label": f"{start.isoformat()}_{end.isoformat()}", "kind": "range",
                "partial": False,
                "title": f"{start.isoformat()} → {end.isoformat()}"}

    title = f"{'Week' if kind == 'week' else 'Month'} {label}"
    if partial:
        title += " (in progress)"
    return {"label": label, "kind": kind, "partial": partial, "title": title}


def previous_range(period: dict, since: str | None,
                   until: str | None) -> tuple[str | None, str | None]:
    """The comparable slice before this one.

    A half-finished week is compared with the same half of the week before, not
    with the four days that happen to precede it — otherwise Wednesday's summary
    reports a drop that only means the week is not over.
    """
    if not (since and until):
        return None, None
    start = dt.date.fromisoformat(since)
    end = dt.date.fromisoformat(until)
    if period["kind"] == "week":
        return ((start - dt.timedelta(days=7)).isoformat(),
                (end - dt.timedelta(days=7)).isoformat())
    if period["kind"] == "month":
        previous_start = (start.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
        _, previous_end = month_range(previous_start)
        return (previous_start.isoformat(),
                min(previous_start + (end - start), previous_end).isoformat())
    span = (end - start).days + 1
    return ((start - dt.timedelta(days=span)).isoformat(),
            (start - dt.timedelta(days=1)).isoformat())


def tally(entries: list[Entry], getter) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for entry in entries:
        for value in getter(entry):
            if value:
                counts[str(value)] = counts.get(str(value), 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def entry_evidence(entry: Entry) -> list[dict]:
    value = entry.meta.get("evidence") or []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def evidence_refs(entry: Entry) -> list[str]:
    refs = []
    for item in entry_evidence(entry):
        reference = str(item.get("reference") or item.get("url") or "").strip()
        kind = str(item.get("type") or "").strip()
        joined = " ".join(part for part in (kind, reference) if part)
        if joined:
            refs.append(joined)
    return refs


def entry_impact(entry: Entry) -> tuple[str, str]:
    """(statement, confidence); an empty statement means nothing was documented."""
    impact = entry.meta.get("impact")
    if isinstance(impact, dict):
        return (str(impact.get("statement") or "").strip(),
                str(impact.get("confidence") or "").strip())
    if isinstance(impact, str):
        return impact.strip(), ""
    return "", ""


def split_by_status(entries: list[Entry]) -> tuple[list[Entry], list[Entry]]:
    """(confirmed, candidates) — candidates are the ones in candidates/."""
    candidates = [e for e in entries if e.path.parent.name == "candidates"]
    confirmed = [e for e in entries if e.path.parent.name != "candidates"]
    return confirmed, candidates


def in_range(entries: list[Entry], since: str | None, until: str | None) -> list[Entry]:
    kept = []
    for entry in entries:
        if not entry.date:
            continue
        if since and entry.date < since:
            continue
        if until and entry.date > until:
            continue
        kept.append(entry)
    return kept


def _range_from_args(args, default_window: str) -> tuple[str | None, str | None]:
    """Resolve --window/--from/--to; the default applies only when none is given."""
    date_from = getattr(args, "date_from", None)
    date_to = getattr(args, "date_to", None)
    window = getattr(args, "window", None) or (
        None if (date_from or date_to) else default_window
    )
    since, until = parse_window(window) if window else (None, None)
    if date_from:
        since = parse_date(date_from).isoformat()
    if date_to:
        until = parse_date(date_to).isoformat()
    return since, until


def _bounded_range(entries: list[Entry], since: str | None,
                   until: str | None) -> tuple[str, str]:
    """Fill in an open-ended range: today at the top, the first entry at the bottom."""
    until = until or today().isoformat()
    if not since:
        dates = sorted(e.date for e in entries if e.date)
        since = dates[0] if dates else until
    return since, until


def summaries_dir(store: Path) -> Path:
    return store / "outputs" / "summaries"


def summary_path(store: Path, period: dict) -> Path:
    return summaries_dir(store) / f"{period['label']}.md"


def profile_competencies(store: Path) -> list[str]:
    """Competencies the user listed in profile.md, ignoring template placeholders."""
    profile = store / "profile.md"
    if not profile.is_file():
        return []
    try:
        text = profile.read_text(encoding="utf-8")
    except OSError:
        return []
    items, inside = [], False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            # "Competencies", "Core competencies" and "Competências" all count.
            heading = unicodedata.normalize("NFKD", stripped.lower())
            inside = "competenc" in heading.encode("ascii", "ignore").decode("ascii")
            continue
        if not inside or not stripped.startswith("- "):
            continue
        value = re.sub(r"<!--.*?-->", "", stripped[2:], flags=re.S).strip()
        if value:
            items.append(value)
    return items


def _haystack(entry: Entry) -> str:
    return " ".join([
        entry.title,
        entry.body,
        str(entry.meta.get("project") or ""),
        " ".join(entry.field_list("tags")),
        " ".join(entry.field_list("skills")),
    ]).lower()


def _covers(entry: Entry, phrase: str) -> bool:
    haystack = _haystack(entry)
    if phrase.lower() in haystack:
        return True
    words = tokens(phrase)
    return bool(words) and all(word in haystack for word in words)


def quiet_periods(confirmed: list[Entry], since: str | None, until: str | None,
                  min_weeks: int = 2) -> list[dict]:
    """Completed weeks inside the range with nothing recorded, merged into stretches.

    Only weeks after the first entry count: the user's record cannot have a hole
    before it starts.
    """
    dates = sorted(e.date for e in confirmed if e.date)
    if not dates:
        return []
    try:
        first = dt.date.fromisoformat(dates[0])
    except ValueError:
        return []
    now = today()
    start = max(dt.date.fromisoformat(since), first) if since else first
    end = min(dt.date.fromisoformat(until), now) if until else now

    recorded = {e.date for e in confirmed}
    current_week_start, _ = week_range(now)
    week_start, week_end = week_range(start)
    if week_start < start:  # only judge weeks that lie fully inside the range
        week_start += dt.timedelta(days=7)
        week_end += dt.timedelta(days=7)

    quiet: list[tuple[dt.date, dt.date]] = []
    while week_end <= end and week_start < current_week_start:
        days = {(week_start + dt.timedelta(days=i)).isoformat() for i in range(7)}
        if not (days & recorded):
            quiet.append((week_start, week_end))
        week_start += dt.timedelta(days=7)
        week_end += dt.timedelta(days=7)

    stretches: list[dict] = []
    for start_day, end_day in quiet:
        if stretches and stretches[-1]["_end"] + dt.timedelta(days=1) == start_day:
            stretches[-1]["_end"] = end_day
            stretches[-1]["weeks"] += 1
        else:
            stretches.append({"_start": start_day, "_end": end_day, "weeks": 1})
    return [
        {"since": s["_start"].isoformat(), "until": s["_end"].isoformat(),
         "weeks": s["weeks"]}
        for s in stretches if s["weeks"] >= min_weeks
    ]


def collect_gaps(store: Path, entries: list[Entry], since: str | None,
                 until: str | None, stale_days: int = 14, quiet_weeks: int = 2,
                 kinds: list[str] | None = None,
                 project: str | None = None) -> list[dict]:
    wanted = list(kinds or GAP_KINDS)
    confirmed, candidates = split_by_status(entries)
    if project:
        confirmed = [e for e in confirmed if e.meta.get("project") == project]
        candidates = [e for e in candidates if e.meta.get("project") == project]
    scoped = in_range(confirmed, since, until)
    gaps: list[dict] = []

    def record(kind, subject, fix, detail="", date="", entry_id=""):
        gaps.append({"kind": kind, "id": entry_id, "subject": subject,
                     "detail": detail, "fix": fix, "date": date})

    if "no-evidence" in wanted:
        for entry in scoped:
            if not entry_evidence(entry):
                record("no-evidence", entry.title,
                       f"update {entry.id} --add-evidence 'github_pr:#…'",
                       date=entry.date, entry_id=entry.id)

    if "no-impact" in wanted:
        for entry in scoped:
            statement, _ = entry_impact(entry)
            if not statement:
                record("no-impact", entry.title,
                       f'update {entry.id} --set-impact "…"',
                       date=entry.date, entry_id=entry.id)

    if "unverified-impact" in wanted:
        for entry in scoped:
            statement, confidence = entry_impact(entry)
            if statement and confidence in ("inferred", "uncertain"):
                record("unverified-impact", entry.title,
                       f'update {entry.id} --set-impact "…" --impact-confidence factual',
                       detail=f"recorded as {confidence}: {statement}",
                       date=entry.date, entry_id=entry.id)

    if "stale-candidate" in wanted:
        now = today()
        for entry in in_range(candidates, since, until):
            try:
                age = (now - dt.date.fromisoformat(entry.date)).days
            except ValueError:
                continue
            if age >= stale_days:
                record("stale-candidate", f"{entry.title} ({age} days old)",
                       f"promote {entry.id}   # or: dismiss {entry.id}",
                       date=entry.date, entry_id=entry.id)

    if "quiet-period" in wanted:
        for stretch in quiet_periods(confirmed, since, until, quiet_weeks):
            record("quiet-period", f"{stretch['since']} → {stretch['until']}",
                   f"github discover --from {stretch['since']} --to {stretch['until']}",
                   detail=f"{stretch['weeks']} consecutive weeks with nothing recorded",
                   date=stretch["since"])

    if "uncovered-competency" in wanted:
        for competency in profile_competencies(store):
            if not any(_covers(entry, competency) for entry in scoped):
                record("uncovered-competency", competency, f'search "{competency}"',
                       detail="listed in profile.md, nothing in this window mentions it")

    order = {kind: index for index, kind in enumerate(GAP_KINDS)}
    gaps.sort(key=lambda g: (order.get(g["kind"], 99), g["date"] or "", g["subject"]),
              reverse=False)
    return gaps


def summary_data(store: Path, entries: list[Entry], since: str | None,
                 until: str | None, project: str | None = None,
                 limit: int = 0) -> dict:
    confirmed, candidates = split_by_status(entries)
    if project:
        confirmed = [e for e in confirmed if e.meta.get("project") == project]
        candidates = [e for e in candidates if e.meta.get("project") == project]

    period = classify_period(since, until)
    scoped = in_range(confirmed, since, until)

    previous_since, previous_until = previous_range(period, since, until)
    previous = in_range(confirmed, previous_since, previous_until)
    previous_period = classify_period(previous_since, previous_until)

    projects_now = {str(e.meta.get("project")) for e in scoped if e.meta.get("project")}
    projects_before = {str(e.meta.get("project")) for e in previous if e.meta.get("project")}

    listed = scoped[:limit] if limit else scoped
    rows = []
    for entry in listed:
        statement, confidence = entry_impact(entry)
        rows.append({
            "id": entry.id,
            "date": entry.date,
            "type": entry.meta.get("type") or "",
            "project": entry.meta.get("project") or "",
            "title": entry.title,
            "evidence": evidence_refs(entry),
            "impact": statement,
            "impact_confidence": confidence,
        })

    return {
        "period": period,
        "since": since,
        "until": until,
        "project": project,
        "count": len(scoped),
        "by_type": tally(scoped, lambda e: [e.meta.get("type")]),
        "by_project": tally(scoped, lambda e: [e.meta.get("project")]),
        "skills": tally(scoped, lambda e: e.field_list("skills")),
        "tags": tally(scoped, lambda e: e.field_list("tags")),
        "people": tally(scoped, lambda e: e.field_list("people")),
        "entries": rows,
        "truncated": len(scoped) - len(listed),
        "with_evidence": sum(1 for e in scoped if entry_evidence(e)),
        "with_impact": sum(1 for e in scoped if entry_impact(e)[0]),
        "without_evidence": [e.id for e in scoped if not entry_evidence(e)],
        "without_impact": [e.id for e in scoped if not entry_impact(e)[0]],
        "previous": {
            "period": previous_period,
            "since": previous_since,
            "until": previous_until,
            "count": len(previous),
        },
        "new_projects": sorted(projects_now - projects_before),
        "quiet_projects": sorted(projects_before - projects_now),
        "pending_candidates": [
            {"id": e.id, "date": e.date, "title": e.title}
            for e in in_range(candidates, since, until)
        ],
        "output_path": str(summary_path(store, period)),
    }


def _print_tally(label: str, rows: list[tuple[str, int]], top: int = 8) -> None:
    if not rows:
        return
    print(f"\n{label}:")
    for name, count in rows[:top]:
        print(f"  {count:>3}  {name}")


def print_summary_table(data: dict) -> None:
    period = data["period"]
    header = period["title"]
    if period["kind"] != "range":  # a range already reads as its own dates
        header += f"  ({data['since']} → {data['until']})"
    print(header)
    if data["project"]:
        print(f"project: {data['project']}")

    previous = data["previous"]
    delta = data["count"] - previous["count"]
    line = f"\n{entry_count(data['count'])} recorded"
    if previous["since"]:
        line += (f"  (previous period {previous['period']['label']}: "
                 f"{previous['count']}, {delta:+d})")
    print(line)

    if not data["count"]:
        print("\nNothing was recorded in this period. That is a fact about the "
              "record, not about the work — check `github discover` for the same "
              "window before concluding the period was quiet.")
        return

    _print_tally("By type", data["by_type"])
    _print_tally("By project", data["by_project"])
    _print_tally("Recurring skills", data["skills"])
    _print_tally("Recurring tags", data["tags"])
    _print_tally("Worked with", data["people"])

    print("\nEntries:")
    for row in data["entries"]:
        bits = [row["date"], f"[{row['type'] or '?'}]"]
        if row["project"]:
            bits.append(f"({row['project']})")
        bits.append(row["title"])
        print("  " + "  ".join(bits))
        if row["evidence"]:
            print("      evidence: " + ", ".join(row["evidence"]))
    if data["truncated"]:
        print(f"  … and {data['truncated']} more")

    if data["new_projects"]:
        print("\nFirst appearance this period: " + ", ".join(data["new_projects"]))
    if data["quiet_projects"]:
        print("Nothing recorded this period for: " + ", ".join(data["quiet_projects"]))

    print(f"\nEvidence attached: {data['with_evidence']}/{data['count']}")
    print(f"Impact documented: {data['with_impact']}/{data['count']}")

    if data["without_evidence"] or data["without_impact"] or data["pending_candidates"]:
        print("\nNeeds attention:")
        if data["without_evidence"]:
            print(f"  {len(data['without_evidence'])} without evidence: "
                  + ", ".join(data["without_evidence"][:5]))
        if data["without_impact"]:
            print(f"  {len(data['without_impact'])} without a documented impact: "
                  + ", ".join(data["without_impact"][:5]))
        if data["pending_candidates"]:
            print(f"  {len(data['pending_candidates'])} candidate(s) awaiting "
                  f"confirmation: "
                  + ", ".join(c["id"] for c in data["pending_candidates"][:5]))

    print(f"\nSuggested output: {data['output_path']}")


def print_summary_markdown(data: dict) -> None:
    period = data["period"]
    kind = {"week": "Weekly", "month": "Monthly"}.get(period["kind"], "Period")
    heading = f"# {kind} summary — {period['title']}"
    if period["kind"] != "range":
        heading += f" ({data['since']} → {data['until']})"
    print(heading)
    print()
    print("<!-- Facts below come from recorded entries. Do not add anything that "
          "is not in the record. -->")

    if not data["count"]:
        print("\nNo entries were recorded in this period.")
        print(f"\n_Suggested path: {data['output_path']}_")
        return

    print("\n## What happened\n")
    for row in data["entries"]:
        head = f"- **{row['date']}** · {row['type'] or 'entry'}"
        if row["project"]:
            head += f" · {row['project']}"
        print(f"{head} — {row['title']}")
        if row["evidence"]:
            print(f"  - Evidence: {', '.join(row['evidence'])}")
        if row["impact"]:
            confidence = f" ({row['impact_confidence']})" if row["impact_confidence"] else ""
            print(f"  - Impact: {row['impact']}{confidence}")
        else:
            print("  - Impact: not documented")
    if data["truncated"]:
        print(f"- … and {data['truncated']} more")

    if data["by_type"] or data["skills"]:
        print("\n## Themes\n")
        for name, count in data["by_type"][:6]:
            print(f"- {name}: {entry_count(count)}")
        for name, count in data["skills"][:6]:
            print(f"- {name}: {entry_count(count)} (interpretation)")

    previous = data["previous"]
    if previous["since"]:
        print(f"\n## Compared with {previous['period']['label']}\n")
        print(f"- {entry_count(data['count'])} recorded, against "
              f"{previous['count']} in the previous period.")
        if data["new_projects"]:
            print("- First appearance this period: " + ", ".join(data["new_projects"]))
        if data["quiet_projects"]:
            print("- Nothing recorded this period for: "
                  + ", ".join(data["quiet_projects"]))

    print("\n## Evidence health\n")
    print(f"- Evidence attached: {data['with_evidence']}/{data['count']}")
    print(f"- Impact documented: {data['with_impact']}/{data['count']}")
    for label, ids in (("No evidence", data["without_evidence"]),
                       ("No documented impact", data["without_impact"])):
        if ids:
            print(f"- {label}: {', '.join(ids)}")
    if data["pending_candidates"]:
        print("- Awaiting your confirmation: "
              + ", ".join(c["id"] for c in data["pending_candidates"]))

    print(f"\n_Suggested path: {data['output_path']}_")


def cmd_summary(args) -> int:
    store = require_store(resolve_store(args.dir))
    if args.period and not (args.window or args.date_from or args.date_to):
        args.window = "this-week" if args.period == "week" else "this-month"
    entries = load_entries(store, include_candidates=True)
    since, until = _bounded_range(entries, *_range_from_args(args, "this-week"))
    data = summary_data(store, entries, since, until, args.project, args.limit)

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print_summary_markdown(data)
    else:
        print_summary_table(data)
    return 0


def cmd_gaps(args) -> int:
    store = require_store(resolve_store(args.dir))
    entries = load_entries(store, include_candidates=True)
    since, until = _bounded_range(entries, *_range_from_args(args, "6m"))
    gaps = collect_gaps(store, entries, since, until, stale_days=args.stale_days,
                        quiet_weeks=args.quiet_weeks, kinds=args.kind,
                        project=args.project)
    total = len(gaps)
    if args.limit:
        gaps = gaps[: args.limit]

    if args.format == "json":
        print(json.dumps(gaps, indent=2, ensure_ascii=False))
        return 0

    confirmed, _ = split_by_status(entries)
    scoped = in_range(confirmed, since, until)
    print(f"Gaps in the record  ({since} → {until}, {entry_count(len(scoped))})")
    if not gaps:
        print("\nNothing missing in this window.")
        return 0

    for kind in GAP_KINDS:
        group = [g for g in gaps if g["kind"] == kind]
        if not group:
            continue
        print(f"\n{GAP_LABEL[kind]} ({len(group)})")
        for gap in group:
            prefix = f"  {gap['date']}  " if gap["date"] else "  "
            print(f"{prefix}{gap['subject']}")
            if gap["detail"] and gap["detail"] != gap["subject"]:
                print(f"      {gap['detail']}")
            print(f"      fix: {gap['fix']}")

    shown = f"{len(gaps)} of {total}" if len(gaps) != total else str(total)
    print(f"\n{shown} gap(s). Each one is something the record cannot prove yet — "
          f"ask the user, do not fill it in.")
    return 0


def summaries_due(store: Path, confirmed: list[Entry], weeks: int = 4,
                  months: int = 2) -> list[dict]:
    """Finished weeks and months that hold entries but were never summarised."""
    written = set()
    for directory in (summaries_dir(store), store / "outputs"):
        if directory.is_dir():
            written.update(path.stem for path in directory.glob("*.md"))

    def already(label: str) -> bool:
        return any(stem == label or stem.startswith(label) for stem in written)

    dates = [e.date for e in confirmed if e.date]
    now = today()
    due: list[dict] = []

    monday, _ = week_range(now)
    for index in range(1, weeks + 1):
        start = monday - dt.timedelta(weeks=index)
        end = start + dt.timedelta(days=6)
        label = iso_week_label(start)
        count = sum(1 for d in dates if start.isoformat() <= d <= end.isoformat())
        if count and not already(label):
            due.append({"kind": "week", "label": label, "since": start.isoformat(),
                        "until": end.isoformat(), "entries": count})

    cursor = now.replace(day=1)
    for _ in range(months):
        end = cursor - dt.timedelta(days=1)
        start = end.replace(day=1)
        label = month_label(start)
        count = sum(1 for d in dates if start.isoformat() <= d <= end.isoformat())
        if count and not already(label):
            due.append({"kind": "month", "label": label, "since": start.isoformat(),
                        "until": end.isoformat(), "entries": count})
        cursor = start
    return due


def _checkup_github(store: Path, entries: list[Entry], days: int) -> dict:
    """Uncaptured GitHub signals, best effort: no access is not an error here."""
    gh = github_module()
    since, until = parse_window(f"{days}d")
    try:
        client = gh.Client(backend="auto")
        login = client.login()
        signals = gh.discover(client, login, since, until, kinds=list(gh.DEFAULT_KINDS))
    except gh.GitHubError as exc:
        return {"available": False, "reason": str(exc), "days": days}
    captured = evidence_index(store, entries)
    fresh = [s for s in signals
             if gh.normalise_reference(s["ref"]) not in captured]
    return {
        "available": True,
        "login": login,
        "days": days,
        "total": len(signals),
        "new": [{"ref": s["ref"], "kind": s["kind"], "date": s.get("date"),
                 "title": s.get("title")} for s in fresh],
    }


def checkup_data(args, store: Path, entries: list[Entry]) -> dict:
    confirmed, candidates = split_by_status(entries)
    dates = sorted(e.date for e in confirmed if e.date)
    now = today()

    def count_window(window: str) -> int:
        since, until = parse_window(window)
        return len(in_range(confirmed, since, until))

    last_entry = confirmed[0] if confirmed else None
    days_since = None
    if dates:
        try:
            days_since = (now - dt.date.fromisoformat(dates[-1])).days
        except ValueError:
            days_since = None

    aged = []
    for candidate in candidates:
        try:
            age = (now - dt.date.fromisoformat(candidate.date)).days
        except ValueError:
            age = None
        aged.append({"id": candidate.id, "date": candidate.date, "age": age,
                     "title": candidate.title})
    aged.sort(key=lambda c: (c["age"] is None, -(c["age"] or 0)))

    since, until = _bounded_range(entries, *_range_from_args(args, "6m"))
    gaps = collect_gaps(store, entries, since, until, stale_days=args.stale_days,
                        quiet_weeks=args.quiet_weeks)
    counts: dict[str, int] = {}
    for gap in gaps:
        counts[gap["kind"]] = counts.get(gap["kind"], 0) + 1
    gap_counts = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    data = {
        "store": str(store),
        "total": len(confirmed),
        "span": [dates[0], dates[-1]] if dates else [],
        "last_entry": {
            "id": last_entry.id, "date": last_entry.date, "title": last_entry.title,
        } if last_entry else None,
        "days_since_last": days_since,
        "cadence": {
            "this_week": count_window("this-week"),
            "last_week": count_window("last-week"),
            "this_month": count_window("this-month"),
            "last_month": count_window("last-month"),
        },
        "summaries_due": summaries_due(store, confirmed, args.weeks, args.months),
        "candidates": aged,
        "gap_window": [since, until],
        "gap_counts": gap_counts,
        "gap_total": len(gaps),
    }
    if getattr(args, "github", False):
        data["github"] = _checkup_github(store, entries, args.github_days)
    return data


def print_checkup(data: dict) -> None:
    print(f"Career Memory checkup  ({data['store']})")
    if data["span"]:
        print(f"  {entry_count(data['total'])}  ({data['span'][0]} → {data['span'][1]})")
    else:
        print("  no confirmed entries yet")

    print("\nLast capture:")
    if data["last_entry"]:
        days = data["days_since_last"]
        ago = "today" if days == 0 else f"{days} day{'s' if days != 1 else ''} ago"
        print(f"  {data['last_entry']['date']} ({ago}) — {data['last_entry']['title']}")
    else:
        print("  nothing recorded yet — `add` the first thing the user mentions")

    cadence = data["cadence"]
    print("\nCadence:")
    print(f"  this week: {cadence['this_week']}   last week: {cadence['last_week']}")
    print(f"  this month: {cadence['this_month']}   last month: {cadence['last_month']}")

    print("\nSummaries not written yet:")
    if data["summaries_due"]:
        for item in data["summaries_due"]:
            print(f"  {item['kind']:<5} {item['label']}  "
                  f"({item['since']} → {item['until']}, {entry_count(item['entries'])})")
    else:
        print("  none due")

    print("\nCandidates awaiting confirmation:")
    if data["candidates"]:
        for candidate in data["candidates"][:5]:
            age = f"{candidate['age']} days old" if candidate["age"] is not None else "undated"
            print(f"  {candidate['id']}  ({age})")
        if len(data["candidates"]) > 5:
            print(f"  … and {len(data['candidates']) - 5} more")
    else:
        print("  none")

    window = data["gap_window"]
    print(f"\nGaps ({window[0]} → {window[1]}):")
    if data["gap_counts"]:
        for kind, count in data["gap_counts"]:
            print(f"  {count:>3}  {GAP_LABEL.get(kind, kind)}")
        print("  details: `gaps`")
    else:
        print("  none")

    github = data.get("github")
    if github is not None:
        print(f"\nGitHub (last {github['days']} days):")
        if not github["available"]:
            print(f"  unavailable — {github['reason']}")
        elif github["new"]:
            print(f"  {len(github['new'])} signal(s) not in the record yet, "
                  f"of {github['total']} found:")
            for signal in github["new"][:5]:
                print(f"    {signal['ref']}  {signal['date']}  {signal['title']}")
            print("  import them with `github import` after showing the user")
        else:
            print(f"  nothing new ({github['total']} signal(s), all recorded)")

    print("\nNext:")
    actions = []
    for item in data["summaries_due"][:2]:
        actions.append(f"summary --from {item['since']} --to {item['until']} "
                       f"--format markdown   # {item['label']}")
    if data["candidates"]:
        actions.append(f"promote {data['candidates'][0]['id']}   # or dismiss")
    if github and github.get("new"):
        actions.append(f"github discover --window {github['days']}d   "
                       f"# show the user before importing")
    if data["gap_total"]:
        actions.append("gaps   # then ask the user, one gap at a time")
    if not actions:
        actions.append("nothing pending — the record is up to date")
    for action in actions:
        print(f"  {action}")


def cmd_checkup(args) -> int:
    store = require_store(resolve_store(args.dir))
    entries = load_entries(store, include_candidates=True)
    data = checkup_data(args, store, entries)
    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    print_checkup(data)
    return 0


STORE_README = """# Career Memory

This directory is your professional memory. It is plain Markdown — readable,
editable and portable without any agent.

- `profile.md` — stable career context (role, focus, goals)
- `entries/` — confirmed career evidence, one file per event
- `candidates/` — possible evidence awaiting your confirmation
- `feedback/` — feedback received
- `projects/` — per-project context
- `outputs/` — generated documents (brag, review, promotion case, daily)
- `outputs/summaries/` — weekly and monthly summaries, one file per period

Everything here is yours. Put it in a private git repository if you want history.
"""


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--window", help="7d, this-week, last-month, last-quarter, this-year")
    parser.add_argument("--from", dest="date_from", help="YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", help="YYYY-MM-DD")
    parser.add_argument("--type", help=f"one of: {', '.join(ENTRY_TYPES)}")
    parser.add_argument("--project")
    parser.add_argument("--tag")
    parser.add_argument("--skill")
    parser.add_argument("--person")
    parser.add_argument("--status", choices=["confirmed", "candidate", "dismissed"])
    parser.add_argument("--include-candidates", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--format", choices=["table", "json", "paths", "full"], default="table")


def add_github_args(parser: argparse.ArgumentParser, source: bool = True) -> None:
    parser.add_argument("--backend", choices=["auto", "gh", "api"], default="auto",
                        help="auto prefers the gh CLI, then $GITHUB_TOKEN")
    parser.add_argument("--user", help="GitHub login (default: the authenticated user)")
    if not source:
        return
    parser.add_argument("--window",
                        help="7d, this-week, last-month, last-quarter "
                             "(default: 30d, unless --from/--to are given)")
    parser.add_argument("--from", dest="date_from", help="YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", help="YYYY-MM-DD")
    parser.add_argument("--kinds", default="pr,issue,review",
                        help="pr, issue, review, commit (commits are opt-in)")
    parser.add_argument("--repo", help="owner/name")
    parser.add_argument("--org")
    parser.add_argument("--visibility", choices=["all", "public", "private"], default="all")
    parser.add_argument("--by", choices=["created", "updated", "merged", "closed"],
                        default="created", help="which date the window filters on")
    parser.add_argument("--limit", type=int, default=50, help="per kind")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="career_memory.py",
        description="Storage layer for the Career Memory skill.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--dir", help="store location (default: $CAREER_MEMORY_HOME or ~/career-memory)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create the store")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add", help="write a new entry")
    p.add_argument("title")
    p.add_argument("--body", default="", help="Markdown body, or - to read stdin")
    p.add_argument("--date", help="YYYY-MM-DD, today, yesterday, or 3d for 3 days ago")
    p.add_argument("--type", help=f"one of: {', '.join(ENTRY_TYPES)}")
    p.add_argument("--project")
    p.add_argument("--tags", help="comma separated")
    p.add_argument("--skills", help="comma separated")
    p.add_argument("--people", help="comma separated")
    p.add_argument("--evidence", action="append",
                   help="type:reference[:value], repeatable")
    p.add_argument("--impact", help="only what the user actually stated")
    p.add_argument("--impact-confidence", choices=CONFIDENCE, default="factual")
    p.add_argument("--context")
    p.add_argument("--source")
    p.add_argument("--status", choices=["confirmed", "candidate"], default="confirmed")
    p.add_argument("--id")
    p.add_argument("--force", action="store_true", help="skip the duplicate check")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list", help="list entries")
    add_filter_args(p)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("search", help="search entries")
    p.add_argument("query")
    add_filter_args(p)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("show", help="print one entry")
    p.add_argument("id")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("update", help="amend an existing entry")
    p.add_argument("id")
    p.add_argument("--add-evidence", action="append")
    p.add_argument("--add-tag", action="append")
    p.add_argument("--add-skill", action="append")
    p.add_argument("--add-person", action="append")
    p.add_argument("--set-status", choices=["confirmed", "candidate", "dismissed"])
    p.add_argument("--set-project")
    p.add_argument("--set-impact")
    p.add_argument("--impact-confidence", choices=CONFIDENCE, default="factual")
    p.add_argument("--append", help="text to append to the body, or - for stdin")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("promote", help="candidate -> confirmed entry")
    p.add_argument("id")
    p.set_defaults(func=cmd_promote)

    p = sub.add_parser("dismiss", help="delete a candidate")
    p.add_argument("id")
    p.set_defaults(func=cmd_dismiss)

    p = sub.add_parser("stats", help="counts and recurring themes")
    add_filter_args(p)
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("summary", help="what a week or a month actually holds")
    p.add_argument("--period", choices=["week", "month"],
                   help="shorthand for --window this-week / this-month")
    p.add_argument("--window",
                   help="this-week, last-week, this-month, last-month, 30d")
    p.add_argument("--from", dest="date_from", help="YYYY-MM-DD")
    p.add_argument("--to", dest="date_to", help="YYYY-MM-DD")
    p.add_argument("--project")
    p.add_argument("--limit", type=int, default=0, help="cap the entry listing")
    p.add_argument("--format", choices=["table", "markdown", "json"], default="table")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("gaps", help="what the record cannot prove yet")
    p.add_argument("--window", help="default: 6m")
    p.add_argument("--from", dest="date_from", help="YYYY-MM-DD")
    p.add_argument("--to", dest="date_to", help="YYYY-MM-DD")
    p.add_argument("--project")
    p.add_argument("--kind", action="append", choices=list(GAP_KINDS),
                   help="restrict to one gap kind, repeatable")
    p.add_argument("--stale-days", type=int, default=14,
                   help="age at which a pending candidate is worth raising")
    p.add_argument("--quiet-weeks", type=int, default=2,
                   help="consecutive empty weeks before a quiet period is reported")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--format", choices=["table", "json"], default="table")
    p.set_defaults(func=cmd_gaps)

    p = sub.add_parser("checkup",
                       help="summaries due, pending candidates and gaps, in one look")
    p.add_argument("--weeks", type=int, default=4, help="how many finished weeks to check")
    p.add_argument("--months", type=int, default=2, help="how many finished months to check")
    p.add_argument("--window", help="window for the gap counts (default: 6m)")
    p.add_argument("--from", dest="date_from", help="YYYY-MM-DD")
    p.add_argument("--to", dest="date_to", help="YYYY-MM-DD")
    p.add_argument("--stale-days", type=int, default=14)
    p.add_argument("--quiet-weeks", type=int, default=2)
    p.add_argument("--github", action="store_true",
                   help="also look for GitHub activity that is not in the record")
    p.add_argument("--github-days", type=int, default=7)
    p.add_argument("--format", choices=["table", "json"], default="table")
    p.set_defaults(func=cmd_checkup)

    p = sub.add_parser("validate", help="check every file against the schema")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("where", help="print the resolved store path")
    p.set_defaults(func=cmd_where)

    gh = sub.add_parser(
        "github",
        help="find GitHub work and turn it into candidate evidence (read-only)",
    )
    gh_sub = gh.add_subparsers(dest="github_command", required=True)

    p = gh_sub.add_parser("check", help="verify GitHub access and identity")
    add_github_args(p, source=False)
    p.set_defaults(func=cmd_github_check)

    p = gh_sub.add_parser("discover", help="list GitHub activity and what is already recorded")
    add_github_args(p)
    p.add_argument("--new-only", action="store_true", help="hide signals already in the store")
    p.add_argument("--format", choices=["table", "json", "refs"], default="table")
    p.set_defaults(func=cmd_github_discover)

    p = gh_sub.add_parser("import", help="write new GitHub signals as candidates")
    add_github_args(p)
    p.add_argument("--project", help="override the project (default: the repository name)")
    p.add_argument("--with-body", action="store_true",
                   help="include the PR/issue description as context")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="import even when an entry looks similar")
    p.set_defaults(func=cmd_github_import)

    p = gh_sub.add_parser("link", help="attach a PR, issue, review or commit to an entry")
    p.add_argument("id")
    p.add_argument("reference", nargs="+", help="URL, owner/repo#123 or owner/repo@sha")
    p.add_argument("--kind", choices=list(GITHUB_ENTRY_TYPE), help="force the reference kind")
    p.add_argument("--no-fetch", action="store_true", help="do not call GitHub for the title")
    p.add_argument("--backend", choices=["auto", "gh", "api"], default="auto")
    p.set_defaults(func=cmd_github_link)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
