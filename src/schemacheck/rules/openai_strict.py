"""OpenAI strict mode (Structured Outputs / strict function calling) rules.

Cited URLs:
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/guides/function-calling
- https://github.com/modelcontextprotocol/typescript-sdk/pull/1082 (OAI007, real failing case)

Not implemented: OAI003 (advice for the OAI002 fix), OAI006 (supported, no rule),
OAI009 (unlisted `format` rejection is unverified), OAI010 (fine-tuned models only),
OAI011/OAI012 (unverified).
"""

from __future__ import annotations

from schemacheck.rules import Ctx, Rule, register
from schemacheck.walk import escape

SO = "https://developers.openai.com/api/docs/guides/structured-outputs"
PR1082 = "https://github.com/modelcontextprotocol/typescript-sdk/pull/1082"
P = "openai-strict"


def is_object(node: dict) -> bool:
    t = node.get("type")
    return t == "object" or (isinstance(t, list) and "object" in t) or "properties" in node


def _oai001(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    if is_object(node) and node.get("additionalProperties") is not False:
        return [(path, "")]
    return []


def _oai002(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    props = node.get("properties")
    if not isinstance(props, dict):
        return []
    req = node.get("required")
    req = req if isinstance(req, list) else []
    return [(f"{path}/properties/{escape(k)}", f"'{k}'") for k in props if k not in req]


def _oai004(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    if ctx.depth != 0:
        return []
    t = node.get("type")
    if "anyOf" in node:
        return [(f"{path}/anyOf", "")]
    if t is not None and t != "object":
        return [(f"{path}/type", f"type is {t!r}")]
    return []


_UNSUPPORTED = ("allOf", "not", "dependentRequired", "dependentSchemas", "if", "then", "else")


def _oai005(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    return [(f"{path}/{k}", k) for k in _UNSUPPORTED if k in node]


def _oai007(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    ref = node.get("$ref")
    if not isinstance(ref, str) or ref == "#":
        return []
    parts = ref.split("/")
    if len(parts) == 3 and parts[0] == "#" and parts[1] in ("$defs", "definitions"):
        return []
    return [(f"{path}/$ref", ref)]


def _oai008(node: dict, path: str, ctx: Ctx) -> list[tuple[str, str]]:
    # root object = level 1, so an object at depth 10 is level 11
    if ctx.depth == 10 and is_object(node):
        return [(path, "level 11")]
    return []


register(Rule(
    "OAI001", P, "error",
    "Every object needs additionalProperties: false in OpenAI strict mode",
    SO, True, True, _oai001,
))
register(Rule(
    "OAI002", P, "error",
    "All keys in properties must be listed in required in OpenAI strict mode",
    SO, True, True, _oai002,
))
register(Rule(
    "OAI004", P, "error",
    "Root schema must be an object and must not use anyOf in OpenAI strict mode",
    SO, False, True, _oai004,
))
register(Rule(
    "OAI005", P, "error",
    "Keyword not supported by OpenAI strict mode "
    "(allOf, not, dependentRequired, dependentSchemas, if, then, else)",
    SO, False, True, _oai005,
))
register(Rule(
    "OAI007", P, "error",
    "$ref must point at a top-level definition ($defs or definitions) or the root '#'",
    PR1082, True, True, _oai007,
))
register(Rule(
    "OAI008", P, "error",
    "Schema nests more than 10 levels deep (OpenAI strict allows 10)",
    SO, False, True, _oai008,
))
