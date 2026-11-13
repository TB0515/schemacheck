"""Subschema walker. Yields every subschema with its RFC 6901 JSON Pointer and depth.

It never follows ``$ref``, so recursive schemas cannot make it loop.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

# keywords whose value maps names -> subschemas
_MAP_KEYS = ("properties", "$defs", "definitions")
# keywords whose value is a list of subschemas
_LIST_KEYS = ("prefixItems", "anyOf", "oneOf", "allOf")
# keywords whose value is a single subschema
_ONE_KEYS = ("not", "if", "then", "else")


def escape(token: str) -> str:
    """Escape one reference token per RFC 6901."""
    return token.replace("~", "~0").replace("/", "~1")


def unescape(token: str) -> str:
    """Inverse of escape()."""
    return token.replace("~1", "/").replace("~0", "~")


def walk(schema: Any, pointer: str = "") -> Iterator[tuple[dict, str, int]]:
    """Yield ``(node, json_pointer, depth)`` for ``schema`` and each subschema (root depth 0).

    ``pointer`` is a prefix prepended to every yielded pointer. Boolean subschemas are skipped.
    """
    stack: list[tuple[Any, str, int]] = [(schema, pointer, 0)]
    while stack:
        node, ptr, depth = stack.pop()
        if not isinstance(node, dict):
            continue
        yield node, ptr, depth
        children: list[tuple[Any, str]] = []
        for key in _MAP_KEYS:
            sub = node.get(key)
            if isinstance(sub, dict):
                children += [(v, f"{ptr}/{key}/{escape(str(k))}") for k, v in sub.items()]
        for key in _LIST_KEYS:
            sub = node.get(key)
            if isinstance(sub, list):
                children += [(v, f"{ptr}/{key}/{i}") for i, v in enumerate(sub)]
        items = node.get("items")
        if isinstance(items, dict):
            children.append((items, f"{ptr}/items"))
        elif isinstance(items, list):
            children += [(v, f"{ptr}/items/{i}") for i, v in enumerate(items)]
        for key in _ONE_KEYS:
            if isinstance(node.get(key), dict):
                children.append((node[key], f"{ptr}/{key}"))
        if isinstance(node.get("additionalProperties"), dict):
            children.append((node["additionalProperties"], f"{ptr}/additionalProperties"))
        # reversed so the stack pops in document order
        stack.extend((c, p, depth + 1) for c, p in reversed(children))
