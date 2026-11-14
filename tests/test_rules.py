import json
import re
from pathlib import Path

import pytest

from schemacheck.rules import PROFILES, RULES, lint

ROOT = Path(__file__).parent.parent
FX = Path(__file__).parent / "fixtures" / "rules"


def obj(props=None, required=None):
    return {"type": "object", "properties": props or {},
            "required": list(props if required is None else required),
            "additionalProperties": False}


def big_properties():
    """5001 properties spread over nested objects (OAI013)."""
    return obj({"a": obj({f"p{i}": {"type": "string"} for i in range(2500)}),
                "b": obj({f"q{i}": {"type": "string"} for i in range(2500)})})


def big_enums():
    """1001 enum values over two enums (OAI014)."""
    return obj({"a": {"enum": [f"v{i}" for i in range(500)]},
                "b": {"enum": [f"w{i}" for i in range(501)]}})


def long_strings():
    """Property names + enum values + const total 120,001 chars (OAI015)."""
    return obj({"n" * 60_000: {"enum": ["e" * 40_000, "f" * 19_999]}, "c": {"const": "xx"}})


def optionals(n):
    props = {f"o{i}": {"type": "string"} for i in range(n)}
    return {"type": "object", "properties": props, "required": [], "additionalProperties": False}


def unions(n):
    props = {f"u{i}": {"anyOf": [{"type": "string"}, {"type": "null"}]} for i in range(n)}
    return obj(props)


GENERATED = {"OAI013": big_properties, "OAI014": big_enums, "OAI015": long_strings,
             "ANT010": lambda: optionals(25), "ANT011": lambda: unions(17)}


def load(name):
    if name in GENERATED:
        return GENERATED[name]()
    return json.loads((FX / f"{name}.json").read_text())


# rule id -> (extra lint kwargs, expected JSON Pointers where the rule must fire)
EXPECTED = {
    "OAI001": ({}, ["/properties/opts"]),
    "OAI002": ({}, ["/properties/b"]),
    "OAI004": ({}, ["/anyOf"]),
    "OAI005": ({}, ["/allOf"]),
    "OAI007": ({}, ["/properties/a/$ref"]),
    "OAI008": ({}, ["/properties/p" * 10]),
    "OAI013": ({}, [""]),
    "OAI014": ({}, [""]),
    "OAI015": ({}, [""]),
    "GEM001": ({}, ["/$schema"]),
    "GEM002": ({}, ["/properties/a/$ref", "/$defs"]),
    "GEM003": ({}, ["/properties/a/const", "/properties/b/enum"]),
    "GEM004": ({}, ["/properties/a/oneOf"]),
    "GEM005": ({}, ["/properties/a/anyOf"]),
    "GEM006": ({}, ["/properties/n/exclusiveMinimum", "/properties/t/type"]),
    "ANT001": ({}, [""]),
    "ANT002": ({"name": "bad name!"}, [""]),
    "ANT003": ({}, ["/properties/opts"]),
    "ANT004": ({}, ["/properties/n/minimum"]),
    "ANT005": ({}, ["/properties/ext/$ref", "/properties/c/allOf", "/properties/c/allOf/0/$ref",
                    "/properties/n/$ref", "/$defs/Node/properties/next/$ref"]),
    "ANT006": ({}, ["/properties/c/format"]),
    "ANT010": ({}, [""]),
    "ANT011": ({}, [""]),
}
BY_ID = {r.id: r for r in RULES}


def test_expected_covers_every_rule():
    assert set(EXPECTED) == set(BY_ID)


@pytest.mark.parametrize("rule_id", sorted(EXPECTED))
def test_rule_fires_at_exact_pointer(rule_id):
    kwargs, paths = EXPECTED[rule_id]
    issues = lint(load(rule_id), BY_ID[rule_id].profile, **kwargs)
    got = sorted(i.path for i in issues if i.rule == rule_id)
    assert got == sorted(paths)
    i = next(i for i in issues if i.rule == rule_id)
    assert (i.profile, i.severity, i.doc_url, i.fixable) == (
        BY_ID[rule_id].profile, BY_ID[rule_id].severity, BY_ID[rule_id].doc_url,
        BY_ID[rule_id].fixable)


def test_every_rule_has_https_doc_url_and_valid_fields():
    for r in RULES:
        assert r.doc_url.startswith("https://") and len(r.doc_url) > len("https://x"), r.id
        assert r.profile in PROFILES and r.severity in ("error", "warning")
        assert isinstance(r.verified, bool) and isinstance(r.fixable, bool)
        assert re.fullmatch(r"(OAI|GEM|ANT)\d{3}", r.id)


def rules_fired(schema, profile):
    return {i.rule for i in lint(schema, profile)}


def test_openai_limits_boundaries():
    ok_props = obj({"a": obj({f"p{i}": {"type": "string"} for i in range(2499)})})  # 2500 total
    assert not rules_fired(ok_props, "openai-strict") & {"OAI013", "OAI014", "OAI015"}
    exact = obj({f"p{i}": {"type": "string"} for i in range(5000)})
    assert "OAI013" not in rules_fired(exact, "openai-strict")
    assert "OAI013" in rules_fired(obj({f"p{i}": {"type": "string"} for i in range(5001)}),
                                   "openai-strict")
    assert "OAI014" not in rules_fired(obj({"a": {"enum": list(range(1000))}}), "openai-strict")
    assert "OAI014" in rules_fired(obj({"a": {"enum": list(range(1001))}}), "openai-strict")
    # 120,000 characters exactly is allowed
    edge = obj({"n" * 60_000: {"enum": ["e" * 59_998]}, "c": {"const": "x"}})
    assert "OAI015" not in rules_fired(edge, "openai-strict")


def test_openai_limits_only_in_openai_profile():
    for rid in ("OAI013", "OAI014", "OAI015"):
        assert not {i.rule for i in lint(load(rid), "gemini")} & {rid}


def test_anthropic_limits_boundaries():
    assert "ANT010" not in rules_fired(optionals(24), "anthropic-strict")
    assert "ANT010" in rules_fired(optionals(25), "anthropic-strict")
    assert "ANT011" not in rules_fired(unions(16), "anthropic-strict")
    assert "ANT011" in rules_fired(unions(17), "anthropic-strict")
    mixed = obj({f"u{i}": {"type": ["string", "null"]} for i in range(17)})
    assert "ANT011" in rules_fired(mixed, "anthropic-strict")
    assert not rules_fired(optionals(25), "anthropic") & {"ANT010"}


def test_every_error_rule_has_primary_source_and_verified():
    secondary = ("github.com",)
    for r in RULES:
        if r.severity == "error":
            assert r.verified, r.id
            assert not any(h in r.doc_url for h in secondary), r.id
        if any(h in r.doc_url for h in secondary):
            assert r.severity == "warning", r.id


def test_anthropic_profile_split():
    assert {r.id for r in RULES if r.profile == "anthropic"} == {"ANT001", "ANT002"}
    plain = {i.rule for i in lint(load("ANT004"), "anthropic")}
    strict = {i.rule for i in lint(load("ANT004"), "anthropic-strict")}
    assert "ANT004" not in plain and "ANT004" in strict


def test_clean_fixture_is_clean_under_every_profile():
    clean = load("clean")
    for p in PROFILES:
        assert lint(clean, p, name="get_weather") == [], p
    assert lint(clean, PROFILES, name="get_weather") == []


def test_unknown_profile_raises():
    with pytest.raises(ValueError):
        lint({}, "nope")


def test_pointer_prefix_and_name():
    issues = lint(load("GEM001"), "gemini", name="t", pointer="/tools/0/inputSchema")
    assert issues[0].path == "/tools/0/inputSchema/$schema" and issues[0].tool == "t"


def test_gemini_flags_schema_key():
    assert [i.rule for i in lint({"$schema": "x", "type": "object"}, "gemini")] == ["GEM001"]


def test_depth_boundary():
    def chain(levels):
        node = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
        root = node
        for _ in range(levels - 1):
            nxt = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
            node["properties"]["p"] = nxt
            node["required"] = ["p"]
            node = nxt
        return root

    assert [i.rule for i in lint(chain(10), "openai-strict")] == []
    assert [i.rule for i in lint(chain(11), "openai-strict")] == ["OAI008"]


def test_root_anyof_is_oai004():
    schema = {"anyOf": [{"type": "object", "properties": {}, "required": [],
                         "additionalProperties": False}]}
    assert "OAI004" in [i.rule for i in lint(schema, "openai-strict")]


def test_oneof_flagged_under_gemini():
    assert "GEM004" in [i.rule for i in lint(load("GEM004"), "gemini")]


def test_recursive_ref_lint_terminates():
    schema = {"type": "object", "properties": {"a": {"$ref": "#"}}, "required": ["a"],
              "additionalProperties": False}
    assert {i.rule for i in lint(schema, PROFILES)} >= {"GEM002", "ANT005"}


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_competitor_fixtures(n):
    path = next((ROOT / "fixtures" / "competitors").glob(f"f{n}-*.json"))
    schema = json.loads(path.read_text())
    got = sorted((i.profile, i.rule, i.path) for i in lint(schema, PROFILES))
    want = {
        1: [("openai-strict", "OAI001", "/properties/opts"),
            ("anthropic-strict", "ANT003", "/properties/opts")],
        2: [("openai-strict", "OAI002", "/properties/units")],
        3: [("gemini", "GEM001", "/$schema"),
            ("gemini", "GEM006", "/properties/n/exclusiveMinimum")],
        4: [("anthropic-strict", "ANT005", "/$defs/User/properties/friend/$ref"),
            ("anthropic-strict", "ANT005", "/properties/target/anyOf/0/$ref"),
            ("gemini", "GEM002", "/$defs"),
            ("gemini", "GEM002", "/$defs/User/properties/friend/$ref"),
            ("gemini", "GEM002", "/properties/target/anyOf/0/$ref"),
            ("gemini", "GEM005", "/properties/target/anyOf")],
    }[n]
    assert got == sorted(want)


def test_docs_rules_md_matches_registry():
    text = (ROOT / "docs" / "rules.md").read_text()
    in_doc = re.findall(r"^\| ((?:OAI|GEM|ANT)\d{3}) \|", text, re.MULTILINE)
    assert sorted(in_doc) == sorted(r.id for r in RULES)
    for r in RULES:
        row = next(line for line in text.splitlines() if line.startswith(f"| {r.id} |"))
        assert r.profile in row and r.severity in row and r.doc_url in row
