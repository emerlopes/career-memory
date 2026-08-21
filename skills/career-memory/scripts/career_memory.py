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

VERSION = "0.1.0"

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
    match = re.fullmatch(r"-(\d+)([dwmy])", value)
    if match:
        return shift(today(), int(match.group(1)), match.group(2))
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        die(f"unrecognised date: {value!r} (use YYYY-MM-DD, today, yesterday, -7d)")


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
    die(f"unrecognised window: {value!r} (try 7d, this-week, last-quarter, 2026-01-01:2026-03-31)")


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
                    window_days: int = 21) -> list[tuple[float, Entry]]:
    hits = []
    for entry in load_entries(store, include_candidates=True):
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


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    store = resolve_store(args.dir)
    store.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (store / sub).mkdir(exist_ok=True)
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

    sections = [f"# {args.title}", ""]
    if body:
        sections += [body.strip(), ""]
    entry = Entry(Path(), meta, "\n".join(sections))

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
    print(f"\n{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")


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

    def tally(getter):
        counts: dict[str, int] = {}
        for entry in entries:
            for value in getter(entry):
                if value:
                    counts[str(value)] = counts.get(str(value), 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    print(f"{len(entries)} entries  ({entries[-1].date} → {entries[0].date})")
    for label, getter in (
        ("By type", lambda e: [e.meta.get("type")]),
        ("By project", lambda e: [e.meta.get("project")]),
        ("Top skills", lambda e: e.field_list("skills")),
        ("Top tags", lambda e: e.field_list("tags")),
        ("People", lambda e: e.field_list("people")),
    ):
        rows = tally(getter)[:10]
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


STORE_README = """# Career Memory

This directory is your professional memory. It is plain Markdown — readable,
editable and portable without any agent.

- `profile.md` — stable career context (role, focus, goals)
- `entries/` — confirmed career evidence, one file per event
- `candidates/` — possible evidence awaiting your confirmation
- `feedback/` — feedback received
- `projects/` — per-project context
- `outputs/` — generated documents (brag, review, promotion case, daily)

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
    p.add_argument("--date", help="YYYY-MM-DD, today, yesterday, -3d")
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

    p = sub.add_parser("validate", help="check every file against the schema")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("where", help="print the resolved store path")
    p.set_defaults(func=cmd_where)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
