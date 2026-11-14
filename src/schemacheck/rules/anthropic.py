"""Anthropic tool `input_schema` rules. `anthropic` = non-strict; `anthropic-strict` = strict tools.

Cited URLs:
- https://platform.claude.com/docs/en/api/messages/create (ANT001: `input_schema` has `type: "object"`)
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools (ANT002)
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs (ANT003-ANT006,
  ANT010-ANT011: "JSON Schema limitations" and "Schema complexity limits")

Not implemented: ANT007 (numeric limits unverified), ANT008 (unverified), ANT009 (a note:
unsupported features return 400, nothing separate to check).
"""

from __future__ import annotations

import re

from schemacheck.rules import Ctx, Rule, register, resolve_ref
from schemacheck.rules.openai_strict import is_object
from schemacheck.walk import walk

API = "https://platform.claude.com/docs/en/api/messages/create"
TU = "https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools"
SO = "https://platform.claude.com/docs/en/build-with-claude/structured-outputs"
NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")
FORMATS = {
    "date-time", "time", "date", "duration", "email", "hostname", "uri", "ipv4", "ipv6", "uuid",
}


def _ant001(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    if ctx.depth != 0:
        return []
    if "type" not in node:
        return [(path, "root has no type")]
    if node["type"] != "object":
        return [(f"{path}/type", f"root type is {node['type']!r}")]
    return []


def _ant002(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    if ctx.depth == 0 and ctx.name is not None and not NAME_RE.match(ctx.name):
        return [(path, f"name {ctx.name!r}")]
    return []


def _ant003(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    if is_object(node) and node.get("additionalProperties") is not False:
        return [(path, "")]
    return []


def _ant004(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    out = [
        (f"{path}/{k}", k)
        for k in ("minimum", "maximum", "multipleOf", "minLength", "maxLength")
        if k in node
    ]
    if "minItems" in node and node["minItems"] not in (0, 1):
        out.append((f"{path}/minItems", "minItems"))
    return out


def _local_refs(node: object) -> list[str]:
    return [
        r
        for sub, _, _ in walk(node)
        if isinstance(r := sub.get("$ref"), str) and r.startswith("#")
    ]


def _is_recursive(ctx: Ctx, path: str, ref: str) -> bool:
    """True if following ``ref`` can lead back to the ref's own target or to an ancestor of it."""
    here = path[len(ctx.prefix):]  # pointer of this node relative to the schema root
    start = resolve_ref(ctx.root, ref)
    if start is None:
        return False
    seen: set[str] = set()
    todo = _local_refs(start[1])
    while todo:
        r = todo.pop()
        if r in seen:
            continue
        seen.add(r)
        hit = resolve_ref(ctx.root, r)
        if hit is None:
            continue
        rel = hit[0]
        if rel == start[0] or here == rel or here.startswith(rel + "/"):
            return True
        todo += _local_refs(hit[1])
    return False


def _ant005(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    out = []
    ref = node.get("$ref")
    if isinstance(ref, str):
        if not ref.startswith("#"):
            out.append((f"{path}/$ref", "external $ref"))
        elif _is_recursive(ctx, path, ref):
            out.append((f"{path}/$ref", "recursive schema"))
    allof = node.get("allOf")
    if isinstance(allof, list) and any(isinstance(b, dict) and "$ref" in b for b in allof):
        out.append((f"{path}/allOf", "allOf with $ref"))
    return out


MAX_OPTIONAL = 24
MAX_UNION = 16


def _ant010(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    if ctx.depth != 0:
        return []
    n = 0
    for sub, _, _ in walk(node):
        props = sub.get("properties")
        if isinstance(props, dict):
            req = sub.get("required")
            req = req if isinstance(req, list) else []
            n += sum(1 for k in props if k not in req)
    return [(path, f"{n} optional parameters in this schema")] if n > MAX_OPTIONAL else []


def _ant011(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    if ctx.depth != 0:
        return []
    n = sum(1 for sub, _, _ in walk(node) if "anyOf" in sub or isinstance(sub.get("type"), list))
    return [(path, f"{n} union-typed parameters in this schema")] if n > MAX_UNION else []


def _ant006(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    fmt = node.get("format")
    if isinstance(fmt, str) and fmt not in FORMATS:
        return [(f"{path}/format", f"format {fmt!r}")]
    return []


register(Rule(
    "ANT001", "anthropic", "error",
    "input_schema must be a JSON Schema object (type: object at the root)",
    API, True, True, _ant001,
))
register(Rule(
    "ANT002", "anthropic", "error",
    "Tool name must match ^[a-zA-Z0-9_-]{1,128}$",
    TU, True, True, _ant002,
))
register(Rule(
    "ANT003", "anthropic-strict", "error",
    "Strict tools require additionalProperties: false on every object",
    SO, True, True, _ant003,
))
register(Rule(
    "ANT004", "anthropic-strict", "error",
    "Strict tools do not support numeric/string/array size constraints",
    SO, True, True, _ant004,
))
register(Rule(
    "ANT005", "anthropic-strict", "error",
    "Strict tools do not support recursive schemas, external $ref, or allOf with $ref",
    SO, False, True, _ant005,
))
register(Rule(
    "ANT006", "anthropic-strict", "error",
    "Strict tools only support a fixed list of string formats",
    SO, True, True, _ant006,
))
register(Rule(
    "ANT010", "anthropic-strict", "error",
    f"More than {MAX_OPTIONAL} optional parameters (not in required); the limit is a total across "
    "all strict schemas in one request, and this checks one schema",
    SO, False, True, _ant010,
))
register(Rule(
    "ANT011", "anthropic-strict", "error",
    f"More than {MAX_UNION} parameters use anyOf or type arrays; the limit is a total across "
    "all strict schemas in one request, and this checks one schema",
    SO, False, True, _ant011,
))
