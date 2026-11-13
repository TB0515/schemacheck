"""Command-line interface for schemacheck."""

from __future__ import annotations

import argparse
import json
import sys

from schemacheck import __version__

PROFILES = ("openai-strict", "gemini", "anthropic", "all")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="schemacheck",
        description="Check LLM/MCP tool JSON Schemas against provider rules.",
    )
    p.add_argument("--profile", choices=PROFILES, default="all", help="provider profile (default: all)")
    p.add_argument("--fix", action="store_true", help="write a fixed document to stdout")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("FILE", nargs="+", help="JSON file to check ('-' reads stdin)")
    return p


def _load(path: str):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for path in args.FILE:
        try:
            _load(path)
        except OSError as e:
            print(f"schemacheck: cannot read {path}: {e.strerror or e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"schemacheck: invalid JSON in {path}: {e}", file=sys.stderr)
            return 2
    if args.json:
        print('{"issues":[]}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
