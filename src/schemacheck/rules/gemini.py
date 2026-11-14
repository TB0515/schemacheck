"""Gemini function-declaration `parameters` rules.

Primary sources (read raw, 2026-11-13):
- https://aistudio.google.com/docs/function-calling: "Only a subset of the OpenAPI schema is
  supported." It never names `$schema`, `$ref`, `const` or `oneOf` as rejected.
- https://aistudio.google.com/docs/structured-output: supports `anyOf`, type
  arrays with "null" and `prefixItems`; strips `minLength` etc. instead of rejecting.
- https://aistudio.google.com/api-reference/caching (Schema reference, the field list GEM006 relies on).
Third-party reports of real rejections (not provider docs; the reason GEM001-GEM004 exist):
- https://github.com/livekit/agents/issues/4334 (GEM001)
- https://github.com/anomalyco/opencode/pull/12911 (GEM002-GEM005)
No Gemini rule is an error: none has a primary source that says the keyword is rejected.

Not implemented: GEM007/GEM008 (notes), GEM009 (no sourced complexity threshold).
`additionalProperties` is deliberately not flagged by GEM006: OpenAI strict requires
`additionalProperties: false`, and whether Gemini rejects it is unverified.
"""

from __future__ import annotations

from schemacheck.rules import Ctx, Rule, register

LIVEKIT = "https://github.com/livekit/agents/issues/4334"
OPENCODE = "https://github.com/anomalyco/opencode/pull/12911"
GC = "https://aistudio.google.com/api-reference/caching"
FC = "https://aistudio.google.com/docs/function-calling"
SOUT = "https://aistudio.google.com/docs/structured-output"
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
    "dependentSchemas", "$id",
)


def _gem006(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    out = [(f"{path}/{k}", k) for k in _NOT_IN_SCHEMA if k in node]
    if isinstance(node.get("type"), list):
        out.append((f"{path}/type", "type array"))
    return out


UNV = "Unverified: "
register(Rule(
    "GEM001", P, "warning",
    UNV + "$schema may be rejected by Gemini in function parameters "
    "(only a third-party report; the docs say only a subset of the OpenAPI schema is supported)",
    FC, True, False, _gem001,
))
register(Rule(
    "GEM002", P, "warning",
    UNV + "$ref / $defs may be rejected by Gemini in function declarations; inline them "
    "(only a third-party report; the structured-output guide shows $defs/$ref working)",
    FC, True, False, _gem002,
))
register(Rule(
    "GEM003", P, "warning",
    UNV + "Gemini may reject const, and the Schema reference documents enum only for STRING "
    "(only a third-party report; the structured-output guide lists numeric enums)",
    GC, True, False, _gem003,
))
register(Rule(
    "GEM004", P, "warning",
    UNV + "oneOf may be rejected by Gemini (only a third-party report; oneOf is absent from "
    "the documented Schema field list)",
    GC, True, False, _gem004,
))
register(Rule(
    "GEM005", P, "warning",
    UNV + "anyOf is documented as supported by Gemini but adds branching that can exceed "
    "complexity limits; third-party reports of rejection exist",
    SOUT, False, False, _gem005,
))
register(Rule(
    "GEM006", P, "warning",
    UNV + "Keyword is not in Gemini's documented Schema field list (the docs say only a subset "
    "of the OpenAPI schema is supported); type arrays are accepted by the structured-output guide",
    FC, True, False, _gem006,
))
