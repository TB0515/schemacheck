"""``--fix``: rewrite a document into a form every selected profile accepts.

Only rules marked fixable are touched, and nothing is invented: a fix adds a keyword the rule
demands, inlines a ``$ref``, renames to a legal name, or drops a keyword the provider rejects.
Lossy drops are reported as notes. Recursive ``$ref``s are left alone.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable
from typing import Any

from schemacheck.loader import load_tools
from schemacheck.rules import resolve_ref
from schemacheck.rules.anthropic import FORMATS, NAME_RE
from schemacheck.rules.gemini import _NOT_IN_SCHEMA
from schemacheck.rules.openai_strict import is_object
from schemacheck.walk import unescape, walk

MAX_PASSES = 10


def _local_refs(node: Any) -> list[str]:
    return [
        r for sub, _, _ in walk(node) if isinstance(r := sub.get("$ref"), str) and r.startswith("#")
    ]


def _is_recursive(root: Any, ref: str) -> bool:
    """True if ``ref`` can be reached again from inside its own target."""
    hit = resolve_ref(root, ref)
    if hit is None:
        return False
    seen: set[str] = set()
    todo = _local_refs(hit[1])
    while todo:
        r = todo.pop()
        if r == ref:
            return True
        if r in seen:
            continue
        seen.add(r)
        nxt = resolve_ref(root, r)
        if nxt is not None:
            todo += _local_refs(nxt[1])
    return False


def _inline_refs(root: dict, want: Callable[[str], bool], notes: list[str]) -> None:
    """Replace each non-recursive local ``$ref`` accepted by ``want`` with a copy of its target."""
    for _ in range(100):
        changed = False
        for node, ptr, _d in list(walk(root)):
            ref = node.get("$ref")
            if not isinstance(ref, str) or not want(ref) or _is_recursive(root, ref):
                continue
            hit = resolve_ref(root, ref)
            if hit is None or not isinstance(hit[1], dict):
                continue
            merged = copy.deepcopy(hit[1])
            merged.update({k: v for k, v in node.items() if k != "$ref"})
            node.clear()
            node.update(merged)
            changed = True
        if not changed:
            return


def _drop(node: dict, key: str, ptr: str, notes: list[str]) -> None:
    del node[key]
    notes.append(f"dropped {key!r} at {ptr or '/'}")


def _openai_object(node: dict, ptr: str, depth: int, notes: list[str]) -> None:
    ap = node.get("additionalProperties")
    if is_object(node) and (ap is None or ap is True):
        node["additionalProperties"] = False
    props = node.get("properties")
    req = node.get("required")
    if isinstance(props, dict) and (req is None or isinstance(req, list)):
        missing = [k for k in props if k not in (req or [])]
        if missing:
            node["required"] = [*(req or []), *missing]


def _gemini_node(node: dict, ptr: str, depth: int, notes: list[str]) -> None:
    if "$schema" in node:
        _drop(node, "$schema", ptr, notes)
    if "const" in node:
        c = node.pop("const")
        if isinstance(c, str) and "enum" not in node:
            node["enum"] = [c]
        else:
            notes.append(f"dropped 'const' at {ptr or '/'}")
    t = node.get("type")
    if "enum" in node and t is not None and t != "string":
        _drop(node, "enum", ptr, notes)
    if "oneOf" in node and "anyOf" not in node:
        node["anyOf"] = node.pop("oneOf")
    for k in _NOT_IN_SCHEMA:
        if k in node:
            _drop(node, k, ptr, notes)
    if isinstance(t, list):
        non_null = [x for x in t if x != "null"]
        if len(non_null) == 1:
            node["type"] = non_null[0]
            if "null" in t:
                node["nullable"] = True


def _anthropic_root(node: dict, ptr: str, depth: int, notes: list[str]) -> None:
    if depth == 0 and "type" not in node:
        node["type"] = "object"


def _anthropic_strict(node: dict, ptr: str, depth: int, notes: list[str]) -> None:
    for k in ("minimum", "maximum", "multipleOf", "minLength", "maxLength"):
        if k in node:
            _drop(node, k, ptr, notes)
    if "minItems" in node and node["minItems"] not in (0, 1):
        _drop(node, "minItems", ptr, notes)
    fmt = node.get("format")
    if isinstance(fmt, str) and fmt not in FORMATS:
        _drop(node, "format", ptr, notes)


def _fix_schema(schema: dict, sel: set[str], notes: list[str]) -> None:
    node_fixers: list[Callable[[dict, str, int, list[str]], None]] = []
    if "gemini" in sel:
        node_fixers.append(_gemini_node)
    if "openai-strict" in sel or "anthropic-strict" in sel:
        node_fixers.append(_openai_object)
    if "anthropic" in sel:
        node_fixers.append(_anthropic_root)
    if "anthropic-strict" in sel:
        node_fixers.append(_anthropic_strict)
    for _ in range(MAX_PASSES):
        before = json.dumps(schema, sort_keys=True)
        if "gemini" in sel:
            _inline_refs(schema, lambda r: True, notes)
        elif "openai-strict" in sel:
            _inline_refs(schema, lambda r: not re.fullmatch(r"#(/(\$defs|definitions)/[^/]+)?", r), notes)
        for node, ptr, depth in list(walk(schema)):
            for fx in node_fixers:
                fx(node, ptr, depth, notes)
        if "gemini" in sel and not _local_refs(schema):
            for key in ("$defs", "definitions"):
                schema.pop(key, None)
        if json.dumps(schema, sort_keys=True) == before:
            return


def _legal_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:128] or "tool"


def _set_name(doc: Any, pointer: str, old: str, new: str) -> bool:
    node = doc
    for raw in pointer[1:].split("/") if pointer else []:
        tok = unescape(raw)
        node = node[int(tok)] if isinstance(node, list) else node[tok]
    if isinstance(node, dict) and node.get("name") == old:
        node["name"] = new
        return True
    return False


def fix_document(doc: Any, sel: set[str]) -> tuple[Any, list[str]]:
    """Return ``(fixed_copy, notes)``; ``doc`` is not modified. Raises UnrecognizedShape."""
    out = copy.deepcopy(doc)
    notes: list[str] = []
    for t in load_tools(out):
        _fix_schema(t.schema, sel, notes)
        if "anthropic" in sel and t.name is not None and not NAME_RE.match(t.name):
            new = _legal_name(t.name)
            name_ptr = t.pointer.rsplit("/", 1)[0]
            if _set_name(out, name_ptr, t.name, new):
                notes.append(f"renamed tool {t.name!r} to {new!r}")
    return out, notes
