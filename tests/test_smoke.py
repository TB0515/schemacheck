import subprocess
import sys

import schemacheck


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "schemacheck.cli", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_version():
    r = run("--version")
    assert r.returncode == 0
    assert r.stdout.strip() == schemacheck.__version__ == "0.1.0"


def test_invalid_json_exits_2(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{bad")
    r = run(str(f))
    assert r.returncode == 2
    assert "invalid JSON" in r.stderr


def test_missing_file_exits_2(tmp_path):
    assert run(str(tmp_path / "nope.json")).returncode == 2


def test_valid_json_output(tmp_path):
    f = tmp_path / "ok.json"
    f.write_text("{}")
    r = run("--json", str(f))
    assert r.returncode == 0
    assert r.stdout.strip() == '{"issues":[]}'
