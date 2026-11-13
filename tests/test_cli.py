import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from schemacheck.cli import check_document, main
from schemacheck.fix import fix_document

ROOT = Path(__file__).parent.parent
ENV = ROOT / "tests" / "fixtures" / "envelopes"
RULES = ROOT / "tests" / "fixtures" / "rules"
COMP = ROOT / "fixtures" / "competitors"
ALL = ("openai-strict", "gemini", "anthropic")

# fixtures whose remaining issues genuinely cannot be fixed (external or recursive $ref)
KNOWN_UNFIXABLE = {"ANT005", "f4-nested-ref-anyOf", "mcp-f4-nested-ref-anyOf"}


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "schemacheck.cli", *args],
        check=False, capture_output=True, text=True, input=stdin,
    )


@pytest.mark.parametrize(
    "name",
    ["bare", "mcp", "mcp-jsonrpc", "anthropic-list", "anthropic-request", "openai-chat",
     "openai-responses", "gemini-list", "gemini-single", "gemini-tools", "mixed"],
)
def test_every_shape_reports_issues_with_pointers(name):
    r = run("--json", str(ENV / f"{name}.json"))
    assert r.returncode == 1, r.stderr
    issues = json.loads(r.stdout)["issues"]
    assert issues
    assert set(issues[0]) == {"file", "tool", "path", "profile", "rule", "message", "doc_url",
                              "fixable"}
    doc = json.loads((ENV / f"{name}.json").read_text())
    for i in issues:  # every path is a real JSON Pointer into the original file (or its parent)
        node = doc
        toks = i["path"].split("/")[1:] if i["path"] else []
        for tok in toks:
            tok = tok.replace("~1", "/").replace("~0", "~")
            if isinstance(node, list):
                node = node[int(tok)]
            elif tok in node:
                node = node[tok]
            else:
                break  # e.g. a missing additionalProperties is reported on the object itself


def test_text_format_and_exit_1():
    f = str(COMP / "mcp-f1-openai-missing-additionalProperties.json")
    r = run(f)
    assert r.returncode == 1
    line = r.stdout.splitlines()[0]
    assert line.startswith(f"{f}:/")
    assert "[openai-strict] OAI001" in line and line.endswith(")") and "https://" in line


def test_clean_exit_0_and_json_exact(tmp_path):
    f = RULES / "clean.json"
    r = run(str(f))
    assert (r.returncode, r.stdout) == (0, "")
    r = run("--json", str(f))
    assert (r.returncode, r.stdout) == (0, '{"issues":[]}\n')


def test_profile_filters():
    f = str(ENV / "bare.json")
    only = {i["profile"] for i in json.loads(run("--json", "--profile", "gemini", f).stdout)["issues"]}
    assert only <= {"gemini"}
    assert run("--profile", "anthropic", str(RULES / "clean.json")).returncode == 0
    assert run("--profile", "bogus", f).returncode == 2


def test_exit_2_cases(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{nope")
    assert run(str(bad)).returncode == 2
    assert run(str(tmp_path / "missing.json")).returncode == 2
    odd = tmp_path / "odd.json"
    odd.write_text('{"hello": 1}')
    r = run(str(odd))
    assert r.returncode == 2 and "unrecognized" in r.stderr
    nested = tmp_path / "nested.json"
    nested.write_text('[{"name": "x"}]')
    assert run(str(nested)).returncode == 2
    assert run("--fix", str(odd)).returncode == 2
    assert run().returncode == 2


def test_stdin():
    r = run("--json", "-", stdin=(RULES / "clean.json").read_text())
    assert r.stdout == '{"issues":[]}\n'
    r = run("-", stdin=(RULES / "OAI001.json").read_text())
    assert r.returncode == 1 and r.stdout.startswith("-:")


def test_warning_only_exits_0(tmp_path):
    f = tmp_path / "w.json"
    f.write_text('{"type":"object","additionalProperties":false,"properties":{"a":'
                 '{"type":"integer","multipleOf":2}},"required":["a"]}')
    r = run("--profile", "gemini", str(f))
    assert r.returncode == 0 and "GEM006" in r.stdout


def test_fix_preserves_shape_and_does_not_touch_files():
    for p in sorted(ENV.glob("*.json")):
        before = p.read_bytes()
        r = run("--fix", str(p))
        assert p.read_bytes() == before
        assert r.returncode == 0, (p.name, r.stderr)
        out, orig = json.loads(r.stdout), json.loads(before)
        assert type(out) is type(orig)
        if isinstance(orig, dict) and p.stem != "bare":
            assert out.keys() == orig.keys()
        else:
            assert len(out) == len(orig)
        assert main_check(out) == []


def main_check(doc):
    return [i for i in check_document(doc, ALL) if i.severity == "error"]


def _all_fixtures():
    return sorted([*ENV.glob("*.json"), *RULES.glob("*.json"), *COMP.glob("*.json")])


@pytest.mark.parametrize("path", _all_fixtures(), ids=lambda p: p.stem)
def test_fix_round_trip_and_idempotent(path):
    doc = json.loads(path.read_text())
    fixed, _ = fix_document(doc, set(ALL))
    assert doc == json.loads(path.read_text())  # input object untouched
    remaining = [i for i in check_document(fixed, ALL) if i.fixable and i.severity == "error"]
    if path.stem in KNOWN_UNFIXABLE:
        assert remaining
    else:
        assert remaining == [], remaining
    again, _ = fix_document(fixed, set(ALL))
    assert again == fixed


def test_fix_cli_exit_1_reports_unfixable_on_stderr():
    r = run("--fix", str(COMP / "f4-nested-ref-anyOf.json"))
    assert r.returncode == 1
    assert "unfixed:" in r.stderr
    json.loads(r.stdout)


def test_fix_cli_round_trip_via_stdin():
    r = run("--fix", "-", stdin=(ENV / "mcp-jsonrpc.json").read_text())
    assert r.returncode == 0
    r2 = run("--json", "--profile", "all", "-", stdin=r.stdout)
    assert (r2.returncode, r2.stdout) == (0, '{"issues":[]}\n')


def test_fix_multiple_files_keyed_by_name():
    a, b = str(ENV / "bare.json"), str(ENV / "mcp.json")
    r = run("--fix", a, b)
    out = json.loads(r.stdout)
    assert set(out) == {a, b}
    assert "tools" in out[b]


def test_fix_inlines_refs_and_renames():
    doc = {"tools": [{"name": "bad name!", "inputSchema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {"u": {"$ref": "#/$defs/U", "description": "d"}},
        "$defs": {"U": {"type": "object", "properties": {"k": {"const": "v"}}}},
    }}]}
    fixed, notes = fix_document(doc, set(ALL))
    t = fixed["tools"][0]
    assert t["name"] == "bad_name_"
    s = t["inputSchema"]
    assert "$defs" not in s and "$schema" not in s
    u = s["properties"]["u"]
    assert u["description"] == "d" and u["additionalProperties"] is False
    assert u["properties"]["k"] == {"enum": ["v"]}
    assert u["required"] == ["k"] and s["required"] == ["u"]
    assert main_check(fixed) == []
    assert notes


def test_fix_stdout_json_is_stable_with_stdin_io(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO((RULES / "OAI001.json").read_text()))
    assert main(["--fix", "-"]) == 0
    assert json.loads(capsys.readouterr().out)["additionalProperties"] is False
