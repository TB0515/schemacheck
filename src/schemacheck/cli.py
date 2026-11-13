"""Command-line interface for schemacheck."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from schemacheck import __version__
from schemacheck.fix import fix_document
from schemacheck.loader import UnrecognizedShape, load_tools
from schemacheck.rules import Issue, lint

PROFILES = ("openai-strict", "gemini", "anthropic", "anthropic-strict", "all")
ALL = ("openai-strict", "gemini", "anthropic")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="schemacheck",
        description="Check LLM/MCP tool JSON Schemas against provider rules.",
    )
    p.add_argument(
        "--profile", choices=PROFILES, default="all",
        help="provider profile (default: all = openai-strict + gemini + anthropic)",
    )
    p.add_argument("--fix", action="store_true", help="write a fixed document to stdout")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("FILE", nargs="+", help="JSON file to check ('-' reads stdin)")
    return p


def _load(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_document(doc: Any, profiles: tuple[str, ...]) -> list[Issue]:
    issues: list[Issue] = []
    for t in load_tools(doc):
        issues += lint(t.schema, profiles, t.name, t.pointer)
    return issues


def _issue_dict(file: str, i: Issue) -> dict:
    return {
        "file": file, "tool": i.tool, "path": i.path, "profile": i.profile, "rule": i.rule,
        "message": i.message, "doc_url": i.doc_url, "fixable": i.fixable,
    }


def _text(file: str, i: Issue) -> str:
    return f"{file}:{i.path or '/'}: [{i.profile}] {i.rule} {i.message} ({i.doc_url})"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    profiles = ALL if args.profile == "all" else (args.profile,)

    docs: list[tuple[str, Any]] = []
    for path in args.FILE:
        try:
            doc = _load(path)
            load_tools(doc)
        except OSError as e:
            print(f"schemacheck: cannot read {path}: {e.strerror or e}", file=sys.stderr)
            return 2
        except UnrecognizedShape as e:
            print(f"schemacheck: unrecognized input shape in {path}: {e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"schemacheck: invalid JSON in {path}: {e}", file=sys.stderr)
            return 2
        docs.append((path, doc))

    if args.fix:
        return _run_fix(docs, profiles)

    found: list[tuple[str, Issue]] = [(f, i) for f, d in docs for i in check_document(d, profiles)]
    if args.json:
        print(json.dumps({"issues": [_issue_dict(f, i) for f, i in found]}, separators=(",", ":")))
    else:
        for f, i in found:
            print(_text(f, i))
    return 1 if any(i.severity == "error" for _, i in found) else 0


def _run_fix(docs: list[tuple[str, Any]], profiles: tuple[str, ...]) -> int:
    sel = set(profiles)
    if "anthropic-strict" in sel:
        sel.add("anthropic")
    fixed: dict[str, Any] = {}
    failed = False
    for path, doc in docs:
        out, notes = fix_document(doc, sel)
        for n in notes:
            print(f"{path}: note: {n}", file=sys.stderr)
        for i in check_document(out, profiles):
            print(f"{path}: unfixed: {_text(path, i)}", file=sys.stderr)
            failed = failed or i.severity == "error"
        fixed[path] = out
    result = fixed[docs[0][0]] if len(docs) == 1 else fixed
    print(json.dumps(result, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
