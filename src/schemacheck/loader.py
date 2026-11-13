"""Envelope-aware loader: find every tool JSON Schema in a parsed document."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_KEYWORDS = frozenset(
    {"type", "properties", "$ref", "anyOf", "oneOf", "allOf", "$defs", "definitions", "items", "enum"}
)


class UnrecognizedShape(ValueError):
    """The document is neither a known tool envelope nor a bare schema."""


@dataclass(frozen=True)
class ToolSchema:
    name: str | None
    schema: dict
    pointer: str
    envelope: str


def escape(key: str | int) -> str:
    """Escape one reference token per RFC 6901."""
    return str(key).replace("\x7e", "\x7e0").replace("/", "\x7e1")


def _name(v: Any) -> str | None:
    return v if isinstance(v, str) else None


def _from_element(el: Any, base: str) -> list[ToolSchema]:
    """Extract tool schemas from one element of a tools list (pointer `base`)."""
    if isinstance(el, dict):
        decls = el.get("functionDeclarations")
        if isinstance(decls, list):
            return _gemini_decls(decls, base + "/functionDeclarations")
        if isinstance(el.get("inputSchema"), dict):
            return [ToolSchema(_name(el.get("name")), el["inputSchema"], base + "/inputSchema", "mcp")]
        if isinstance(el.get("input_schema"), dict):
            return [ToolSchema(_name(el.get("name")), el["input_schema"], base + "/input_schema", "anthropic")]
        if el.get("type") == "function":
            fn = el.get("function")
            if isinstance(fn, dict):
                params = fn.get("parameters")
                if params is None:
                    return []
                if isinstance(params, dict):
                    return [ToolSchema(_name(fn.get("name")), params, base + "/function/parameters", "openai-chat")]
            elif "name" in el:
                params = el.get("parameters")
                if params is None:
                    return []
                if isinstance(params, dict):
                    return [ToolSchema(_name(el.get("name")), params, base + "/parameters", "openai-responses")]
    raise UnrecognizedShape(f"no tool schema found at element {base or '/'}")


def _gemini_decls(decls: list, base: str) -> list[ToolSchema]:
    out: list[ToolSchema] = []
    for i, d in enumerate(decls):
        p = f"{base}/{i}"
        if not isinstance(d, dict) or "name" not in d:
            raise UnrecognizedShape(f"no tool schema found at element {p}")
        for key in ("parameters", "parametersJsonSchema"):
            if isinstance(d.get(key), dict):
                out.append(ToolSchema(_name(d.get("name")), d[key], f"{p}/{key}", "gemini"))
                break
        else:
            if "parameters" in d or "parametersJsonSchema" in d:
                raise UnrecognizedShape(f"no tool schema found at element {p}")
            # declaration with no parameters at all: valid, nothing to lint
    return out


def _from_list(items: list, base: str) -> list[ToolSchema]:
    out: list[ToolSchema] = []
    for i, el in enumerate(items):
        out.extend(_from_element(el, f"{base}/{i}"))
    return out


def load_tools(doc: Any) -> list[ToolSchema]:
    """Return every tool schema in `doc` with its JSON Pointer.

    Raises UnrecognizedShape if nothing matches or a tools-list element has no schema field.
    """
    if isinstance(doc, list):
        return _from_list(doc, "")
    if isinstance(doc, dict):
        result = doc.get("result")
        if doc.get("jsonrpc") == "2.0" and isinstance(result, dict) and isinstance(result.get("tools"), list):
            tools = _from_list(result["tools"], "/result/tools")
            return [
                ToolSchema(t.name, t.schema, t.pointer, "mcp-jsonrpc") if t.envelope == "mcp" else t
                for t in tools
            ]
        if isinstance(doc.get("tools"), list):
            return _from_list(doc["tools"], "/tools")
        if isinstance(doc.get("functionDeclarations"), list):
            return _gemini_decls(doc["functionDeclarations"], "/functionDeclarations")
        if SCHEMA_KEYWORDS & doc.keys():
            return [ToolSchema(None, doc, "", "bare")]
    raise UnrecognizedShape("document is not a recognized tool envelope or JSON Schema")
