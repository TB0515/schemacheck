"""Rule engine: provider-rejection rules, each citing an official doc or a real failing case."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from schemacheck.walk import unescape, walk

PROFILES = ("openai-strict", "gemini", "anthropic", "anthropic-strict")


@dataclass
class Ctx:
    """What a rule check can see besides the node itself."""

    root: Any  # the whole schema passed to lint()
    prefix: str  # JSON Pointer of the schema root inside the original document
    depth: int  # depth of the node (root = 0)
    name: str | None  # tool name, if known


# A check returns (json_pointer, detail) pairs; detail may be "".
Check = Callable[[dict, str, Ctx], list[tuple[str, str]]]


@dataclass
class Rule:
    id: str
    profile: str
    severity: str  # "error" | "warning"
    message: str
    doc_url: str
    fixable: bool
    verified: bool  # False = the rulebook quote is summary-only (grade S) or the rule is inferred
    check: Check


@dataclass
class Issue:
    tool: str | None
    path: str
    profile: str
    rule: str
    severity: str
    message: str
    doc_url: str
    fixable: bool


RULES: list[Rule] = []


def register(rule: Rule) -> Rule:
    assert rule.profile in PROFILES and rule.id not in {r.id for r in RULES}
    RULES.append(rule)
    return rule


def resolve_ref(root: Any, ref: str) -> tuple[str, Any] | None:
    """Resolve a local ``#...`` ref against ``root``; returns (pointer relative to root, node)."""
    if not ref.startswith("#"):
        return None
    rel = ref[1:]
    node = root
    if rel:
        if not rel.startswith("/"):
            return None
        for raw in rel[1:].split("/"):
            tok = unescape(raw)
            if isinstance(node, dict) and tok in node:
                node = node[tok]
            elif isinstance(node, list) and tok.isdigit() and int(tok) < len(node):
                node = node[int(tok)]
            else:
                return None
    return rel, node


def lint(
    schema: Any,
    profiles: str | Iterable[str],
    name: str | None = None,
    pointer: str = "",
) -> list[Issue]:
    """Report every place ``schema`` would be rejected under the given profiles.

    ``anthropic-strict`` also applies the plain ``anthropic`` rules. ``name`` is the tool name
    (used by ANT002). ``pointer`` prefixes every reported path.
    """
    wanted = {profiles} if isinstance(profiles, str) else set(profiles)
    unknown = wanted - set(PROFILES)
    if unknown:
        raise ValueError(f"unknown profile(s): {sorted(unknown)}")
    if "anthropic-strict" in wanted:
        wanted.add("anthropic")
    rules = [r for r in RULES if r.profile in wanted]
    issues: list[Issue] = []
    for node, ptr, depth in walk(schema, pointer):
        ctx = Ctx(schema, pointer, depth, name)
        for r in rules:
            for path, detail in r.check(node, ptr, ctx):
                msg = f"{r.message} ({detail})" if detail else r.message
                issues.append(
                    Issue(name, path, r.profile, r.id, r.severity, msg, r.doc_url, r.fixable)
                )
    return issues


# Importing the modules registers their rules (order = registry order).
from schemacheck.rules import openai_strict, gemini, anthropic  # noqa: F401, I001
