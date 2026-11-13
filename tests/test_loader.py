import json
from pathlib import Path

import pytest

from schemacheck.loader import ToolSchema, UnrecognizedShape, escape, load_tools

ENV = Path(__file__).parent / "fixtures" / "envelopes"
COMP = Path(__file__).parent.parent / "fixtures" / "competitors"
TILDE = "\x7e"


def resolve(doc, pointer):
    if pointer == "":
        return doc
    for tok in pointer[1:].split("/"):
        tok = tok.replace(TILDE + "1", "/").replace(TILDE + "0", TILDE)
        doc = doc[int(tok)] if isinstance(doc, list) else doc[tok]
    return doc


EXPECTED = {
    "mcp": [("a", "/tools/0/inputSchema", "mcp"), (f"b/c{TILDE}d", "/tools/1/inputSchema", "mcp")],
    "mcp-jsonrpc": [(f"t{i}", f"/result/tools/{i}/inputSchema", "mcp-jsonrpc") for i in range(3)],
    "anthropic-list": [("a", "/0/input_schema", "anthropic"), ("b", "/1/input_schema", "anthropic")],
    "anthropic-request": [("a", "/tools/0/input_schema", "anthropic"), ("b", "/tools/1/input_schema", "anthropic")],
    "openai-chat": [("a", "/0/function/parameters", "openai-chat"), ("b", "/1/function/parameters", "openai-chat")],
    "openai-responses": [("a", "/0/parameters", "openai-responses"), ("b", "/1/parameters", "openai-responses")],
    "gemini-single": [
        ("a", "/functionDeclarations/0/parameters", "gemini"),
        ("b", "/functionDeclarations/1/parametersJsonSchema", "gemini"),
    ],
    "gemini-list": [
        ("a", "/0/functionDeclarations/0/parameters", "gemini"),
        ("b", "/1/functionDeclarations/0/parametersJsonSchema", "gemini"),
    ],
    "gemini-tools": [
        ("a", "/tools/0/functionDeclarations/0/parameters", "gemini"),
        ("b", "/tools/0/functionDeclarations/1/parameters", "gemini"),
    ],
    "mixed": [
        ("m", "/0/inputSchema", "mcp"),
        ("an", "/1/input_schema", "anthropic"),
        ("oc", "/2/function/parameters", "openai-chat"),
        ("or", "/3/parameters", "openai-responses"),
        ("g", "/4/functionDeclarations/0/parameters", "gemini"),
    ],
    "bare": [(None, "", "bare")],
}


@pytest.mark.parametrize("fx", sorted(EXPECTED))
def test_fixture(fx):
    doc = json.loads((ENV / f"{fx}.json").read_text())
    got = load_tools(doc)
    assert [(t.name, t.pointer, t.envelope) for t in got] == EXPECTED[fx]
    for t in got:
        assert isinstance(t, ToolSchema)
        assert resolve(doc, t.pointer) == t.schema
        assert resolve(doc, t.pointer) is t.schema


def test_bare_single_entry_with_special_keys():
    doc = json.loads((ENV / "bare.json").read_text())
    (t,) = load_tools(doc)
    assert t.pointer == "" and t.schema is doc
    assert "a/b" in t.schema["properties"] and f"c{TILDE}d" in t.schema["properties"]


def test_escaping():
    assert escape("a/b") == f"a{TILDE}1b"
    assert escape(f"c{TILDE}d") == f"c{TILDE}0d"
    assert escape(f"{TILDE}/") == f"{TILDE}0{TILDE}1"
    doc = {"a/b": {f"c{TILDE}d": 1}}
    assert resolve(doc, "/" + escape("a/b") + "/" + escape(f"c{TILDE}d")) == 1
    # tool names with / and the tilde never leak into pointers (index-based) and stay intact
    t = load_tools(json.loads((ENV / "mcp.json").read_text()))[1]
    assert t.name == f"b/c{TILDE}d" and t.pointer == "/tools/1/inputSchema"


@pytest.mark.parametrize("doc", [["a", "b"], {"foo": 1}, 5, "x"])
def test_unrecognized(doc):
    with pytest.raises(UnrecognizedShape):
        load_tools(doc)


def test_element_without_schema_names_pointer():
    doc = {"tools": [{"name": "ok", "inputSchema": {"type": "object"}}, {"name": "bad"}]}
    with pytest.raises(UnrecognizedShape, match="/tools/1"):
        load_tools(doc)
    with pytest.raises(UnrecognizedShape, match="/2"):
        load_tools([{"name": "a", "input_schema": {}}, {"name": "b", "input_schema": {}}, {"x": 1}])
    with pytest.raises(UnrecognizedShape, match="/functionDeclarations/1"):
        load_tools({"functionDeclarations": [{"name": "a", "parameters": {}}, 7]})


def test_no_parameters_skipped():
    doc = [
        {"type": "function", "function": {"name": "noargs"}},
        {"type": "function", "name": "noargs2"},
        {"type": "function", "function": {"name": "x", "parameters": {"type": "object"}}},
    ]
    assert [(t.name, t.pointer) for t in load_tools(doc)] == [("x", "/2/function/parameters")]


@pytest.mark.parametrize("p", sorted(COMP.glob("*.json")), ids=lambda p: p.name)
def test_competitors(p):
    doc = json.loads(p.read_text())
    got = load_tools(doc)
    if p.name.startswith("mcp-"):
        assert len(got) == len(doc) and all(t.envelope == "mcp" for t in got)
        assert [t.pointer for t in got] == [f"/{i}/inputSchema" for i in range(len(doc))]
    else:
        assert [(t.pointer, t.envelope) for t in got] == [("", "bare")]
    for t in got:
        assert resolve(doc, t.pointer) == t.schema
