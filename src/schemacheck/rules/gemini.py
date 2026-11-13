"""Gemini function-declaration `parameters` rules.

Cited URLs:
- https://github.com/livekit/agents/issues/4334 (GEM001, real failing case)
- https://github.com/anomalyco/opencode/pull/12911 (GEM002-GEM005, real failing cases)
- https://aistudio.google.com/api-reference/caching (Gemini Schema / FunctionDeclaration
  reference; the field list GEM005/GEM006 rely on; also corroborates GEM001-GEM004)

Not implemented: GEM007/GEM008 (notes), GEM009 (no sourced complexity threshold).
`additionalProperties` is deliberately not flagged by GEM006: OpenAI strict requires
`additionalProperties: false`, and whether Gemini rejects it is unverified.
"""

from __future__ import annotations

from schemacheck.rules import Ctx, Rule, register

LIVEKIT = "https://github.com/livekit/agents/issues/4334"
OPENCODE = "https://github.com/anomalyco/opencode/pull/12911"
GC = "https://aistudio.google.com/api-reference/caching"
P = "gemini"


def _gem001(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    return [(f"{path}/$schema", "")] if "$schema" in node else []


def _gem002(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    return [(f"{path}/{k}", k) for k in ("$ref", "$defs") if k in node]


def _gem003(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    out = []
    if "const" in node:
        out.append((f"{path}/const", "const"))
    t = node.get("type")
    if "enum" in node and t is not None and t != "string":
        out.append((f"{path}/enum", f"enum on type {t!r}"))
    return out


def _gem004(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    return [(f"{path}/oneOf", "")] if "oneOf" in node else []


def _gem005(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    return [(f"{path}/anyOf", "")] if "anyOf" in node else []


# JSON Schema keywords absent from the documented Gemini Schema field list
_NOT_IN_SCHEMA = (
    "allOf", "not", "if", "then", "else", "exclusiveMinimum", "exclusiveMaximum",
    "multipleOf", "patternProperties", "uniqueItems", "dependentRequired",
    "dependentSchemas", "prefixItems", "$id",
)


def _gem006(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    out = [(f"{path}/{k}", k) for k in _NOT_IN_SCHEMA if k in node]
    if isinstance(node.get("type"), list):
        out.append((f"{path}/type", "type array"))
    return out


register(Rule(
    "GEM001", P, "error",
    "$schema is rejected by Gemini in function parameters",
    LIVEKIT, True, True, _gem001,
))
register(Rule(
    "GEM002", P, "error",
    "$ref / $defs are rejected by Gemini in function declarations; inline them",
    OPENCODE, True, True, _gem002,
))
register(Rule(
    "GEM003", P, "error",
    "Gemini rejects const, and enum is only allowed for STRING type",
    OPENCODE, True, True, _gem003,
))
register(Rule(
    "GEM004", P, "error",
    "oneOf is rejected by Gemini",
    OPENCODE, True, True, _gem004,
))
register(Rule(
    "GEM005", P, "warning",
    "anyOf is in Gemini's Schema field list but reported rejected or limited in practice",
    OPENCODE, False, False, _gem005,
))
register(Rule(
    "GEM006", P, "warning",
    "Keyword is not in Gemini's documented Schema field list and may be rejected or ignored",
    GC, True, False, _gem006,
))
