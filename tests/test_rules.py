import json
import re
from pathlib import Path

import pytest

from schemacheck.rules import PROFILES, RULES, lint

ROOT = Path(__file__).parent.parent
FX = Path(__file__).parent / "fixtures" / "rules"


def load(name):
    return json.loads((FX / f"{name}.json").read_text())


# rule id -> (extra lint kwargs, expected JSON Pointers where the rule must fire)
EXPECTED = {
    "OAI001": ({}, ["/properties/opts"]),
    "OAI002": ({}, ["/properties/b"]),
    "OAI004": ({}, ["/anyOf"]),
    "OAI005": ({}, ["/allOf"]),
    "OAI007": ({}, ["/properties/a/$ref"]),
    "OAI008": ({}, ["/properties/p" * 10]),
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
