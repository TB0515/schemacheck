# schemacheck

**Find out which of OpenAI strict, Gemini and Anthropic will reject your tool's JSON Schema, offline, and get one fixed schema that all of them accept.**

> Built and maintained by autonomous AI agents at Kiln, an AI-only company. No human wrote this code or this README. See [AI_DISCLOSURE.md](AI_DISCLOSURE.md).

For people writing MCP servers and agent tools who keep finding that one provider rejects a schema another accepts (`$ref`/`$defs`, `anyOf`, missing `additionalProperties: false`, stray `$schema` keys). No network calls, no API keys, no runtime dependencies (Python >= 3.11, standard library only).

## 30-second quickstart

```sh
git clone https://github.com/TB0515/schemacheck && cd schemacheck
uv run schemacheck examples/tools.json                       # check (exit 1 if errors)
uv run schemacheck --fix examples/tools.json > fixed.json    # write a fixed copy
uv run schemacheck fixed.json                                # re-check (exit 0)
```

Without cloning: `uvx --from git+https://github.com/TB0515/schemacheck schemacheck tools.json`.

**Before** (`examples/tools.json`, an MCP `tools/list` result with a `$schema` key, a `$ref`, no `additionalProperties`, an optional property):

```
examples/tools.json:/tools/0/inputSchema: [openai-strict] OAI001 Every object needs additionalProperties: false in OpenAI strict mode (...)
examples/tools.json:/tools/0/inputSchema/properties/filter: [openai-strict] OAI002 All keys in properties must be listed in required in OpenAI strict mode ('filter') (...)
examples/tools.json:/tools/0/inputSchema/$schema: [gemini] GEM001 $schema is rejected by Gemini in function parameters (...)
examples/tools.json:/tools/0/inputSchema/$defs: [gemini] GEM002 $ref / $defs are rejected by Gemini in function declarations; inline them ($defs) (...)
examples/tools.json:/tools/0/inputSchema/properties/filter/$ref: [gemini] GEM002 ... ($ref)
examples/tools.json:/tools/0/inputSchema/$defs/Filter: [openai-strict] OAI001 ...
examples/tools.json:/tools/0/inputSchema/$defs/Filter/properties/state: [openai-strict] OAI002 ...
```

(URLs shortened here; the real output ends each line with the doc link.)

**After** `--fix` (stderr says `note: dropped '$schema' at /`): `$schema` and `$defs` are gone, `Filter` is inlined, every object has `additionalProperties: false`, and every property is in `required`. Re-checking prints nothing and exits 0 (`--json` prints `{"issues":[]}`). Note the fix makes optional parameters required, as OpenAI strict mode demands; it does not add nullability.

## How is this different from schemafit?

[schemafit](https://github.com/OrionArchitekton/schemafit) is the closest existing tool, and it is more mature than we are. It repairs per provider; we produce one cross-provider output. What we offer on top:

- **Rules cited and checked against the docs.** We compared all 18 rules to the providers' documentation and to schemafit's output: [docs/rule-verification.md](docs/rule-verification.md). Result: 8 CONFIRMED by a verbatim doc sentence, 10 WEAKLY SUPPORTED, 0 contradicted. That report was written by an AI agent; read it before trusting it.
- **Tool-envelope awareness**: OpenAI, Anthropic, MCP and Gemini wrappers, MCP `tools/list` results and JSON-RPC responses, with JSON Pointers into your original file.
- **Checks schemafit did not flag in our fixtures**: tool-name rules (ANT002), `$schema` (GEM001), `const`/non-string `enum` for Gemini (GEM003). The same comparison shows schemafit flagging things we do not, such as `pattern` and `exclusiveMinimum` under Anthropic. We have not benchmarked beyond those fixtures.

### Rules that are only WEAKLY SUPPORTED

"Weakly supported" means the only evidence is a third-party issue/PR, a summary-only doc read, or inference from the docs being silent. These rules may be too strict or too lenient:

- **Gemini (all six, GEM001-GEM006)**: based on issue/PR reports and the Gemini field list. The docs are partly conflicting: Gemini's `parametersJsonSchema` accepts fuller JSON Schema, so `$ref`/`$defs`/type arrays may be fine on that path. GEM005 (`anyOf`) and GEM006 are warnings for this reason.
- **OAI007** (nested `$ref` forms): backed by a real OpenAI error quoted in an SDK PR, not by the OpenAI docs.
- **ANT001** (root `type: object`), **ANT005** (recursive/external `$ref`, `allOf`+`$ref`), **ANT006** (`format` list): the Anthropic page text was only available as a summary.

CONFIRMED: OAI001, OAI002, OAI004, OAI005, OAI008, ANT002, ANT003, ANT004. Known gaps: we do not check OpenAI's total property/enum-size limits, Anthropic's complexity limits, or objects with no `properties`. Details in the report.

## Use in CI (GitHub Action)

```yaml
# .github/workflows/schemacheck.yml
name: schemacheck
on: [push, pull_request]
jobs:
  schemacheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: TB0515/schemacheck@main
        with:
          files: "schemas/*.json tools.json"   # space-separated, globs allowed
          profile: all                         # optional: openai-strict | gemini | anthropic | anthropic-strict | all
```

The job fails when schemacheck exits 1 (any error-severity issue). The action is a composite action that installs `uv` and runs the CLI from the action's own checkout. **Not tested on a real GitHub runner** (we cannot run workflows from here); see "Limitations of the action" under Status.

## Why

One provider rejects schemas that another accepts. At least four projects have written private sanitizers for this (MCP TypeScript SDK PR #1082, opencode PR #12911, livekit/agents #4334). schemacheck checks all providers in one pass and produces one fixed output.

## Install / run

Straight from GitHub (distributed from GitHub only, not PyPI):

```sh
uvx --from git+https://github.com/TB0515/schemacheck schemacheck tools.json
pipx run --spec git+https://github.com/TB0515/schemacheck schemacheck tools.json
```

From a checkout: `uv run schemacheck tools.json`.

## Usage

```
schemacheck [--profile openai-strict|gemini|anthropic|anthropic-strict|all] [--fix] [--json] FILE...
```

`FILE` may be `-` for stdin. Default profile is `all` (= `openai-strict` + `gemini` + `anthropic`). `anthropic-strict` (Anthropic strict tools) is opt-in because it forbids constraints like `minimum` that plain Anthropic tools accept.

**Accepted inputs** (auto-detected): a bare JSON Schema; a list of tools in OpenAI (chat `{"type":"function","function":{...}}` or Responses-style flat), Anthropic (`input_schema`), MCP (`inputSchema`) or Gemini (`functionDeclarations`) form; an MCP `tools/list` result `{"tools":[...]}`, a JSON-RPC response `{"result":{"tools":[...]}}`, or a request body with a `tools` array.

**Exit codes:** `0` no errors, `1` at least one error-severity issue, `2` usage error, unreadable file, invalid JSON, or unrecognized shape (nothing else is printed to stdout in that case). Warning-severity issues (GEM005, GEM006) are printed but do not change the exit code.

### Check

```
$ schemacheck tools.json
tools.json:/tools/0/inputSchema/properties/opts: [openai-strict] OAI001 Every object needs additionalProperties: false in OpenAI strict mode (https://developers.openai.com/api/docs/guides/structured-outputs)
```

Format: `FILE:/json/pointer: [profile] RULE-ID message (doc URL)`. The pointer points into the original file, envelope included.

`--json` prints `{"issues":[{"file","tool","path","profile","rule","message","doc_url","fixable"}]}`; a clean run prints exactly `{"issues":[]}`.

### Fix

`--fix` writes the fixed document to **stdout** and never edits files. The outer shape is preserved (MCP, JSON-RPC, OpenAI, Anthropic, Gemini or bare). With several files, the output is a JSON object keyed by file name. Unfixed issues go to stderr (`unfixed: ...`) with exit 1; lossy changes are listed as `note:` lines on stderr.

```sh
schemacheck --fix tools.json > tools.fixed.json
schemacheck --profile all tools.fixed.json   # re-check
```

What `--fix` does, only for rules marked fixable: adds `additionalProperties: false`; lists every property in `required` (note: this makes optional parameters required, as OpenAI strict mode demands; it does not add nullability); inlines non-recursive local `$ref`s and removes `$defs`; removes `$schema`; turns a string `const` into a one-value `enum`; renames `oneOf` to `anyOf`; collapses `["T","null"]` to `T` + `nullable: true` for Gemini; drops keywords the provider does not support (Gemini-unknown keywords, `anthropic-strict` size constraints/formats and non-enum `const`/non-string `enum`); adds a missing root `type: object`; replaces illegal characters in tool names with `_`. It does not fix recursive or external `$ref`, root `anyOf`, unsupported combinators under OpenAI, or nesting depth; those are reported. The fix is idempotent.

## Rules

Every rule cites an official doc or a real failing issue/PR. Full details in [docs/rules.md](docs/rules.md). "Verified = no" means the source quote was summary-only or the rule is inferred.

| ID | Profile | Severity | Rule | Fixable | Source |
|---|---|---|---|---|---|
| OAI001 | openai-strict | error | every object needs `additionalProperties: false` | yes | [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| OAI002 | openai-strict | error | every property must be in `required` | yes | [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| OAI004 | openai-strict | error | root must be an object, no root `anyOf` | no | [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| OAI005 | openai-strict | error | `allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`/`then`/`else` unsupported | no | [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| OAI007 | openai-strict | error | `$ref` must be `#`, `#/$defs/X` or `#/definitions/X` | yes | [MCP TS SDK PR #1082](https://github.com/modelcontextprotocol/typescript-sdk/pull/1082) |
| OAI008 | openai-strict | error | more than 10 levels of nesting | no | [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| GEM001 | gemini | error | `$schema` rejected | yes | [livekit/agents #4334](https://github.com/livekit/agents/issues/4334) |
| GEM002 | gemini | error | `$ref` / `$defs` rejected | yes | [opencode PR #12911](https://github.com/anomalyco/opencode/pull/12911) |
| GEM003 | gemini | error | `const` rejected; `enum` only for strings | yes | [opencode PR #12911](https://github.com/anomalyco/opencode/pull/12911) |
| GEM004 | gemini | error | `oneOf` rejected | yes | [opencode PR #12911](https://github.com/anomalyco/opencode/pull/12911) |
| GEM005 | gemini | warning | `anyOf` reported rejected/limited (verified = no) | no | [opencode PR #12911](https://github.com/anomalyco/opencode/pull/12911) |
| GEM006 | gemini | warning | keyword not in Gemini's Schema field list (verified = no) | yes | [Gemini API reference](https://aistudio.google.com/api-reference/caching) |
| ANT001 | anthropic | error | root must be `type: object` (verified = no) | yes | [Anthropic tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) |
| ANT002 | anthropic | error | tool name must match `^[a-zA-Z0-9_-]{1,128}$` | yes | [Anthropic tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) |
| ANT003 | anthropic-strict | error | `additionalProperties: false` on every object (verified = no) | yes | [Anthropic structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) |
| ANT004 | anthropic-strict | error | no `minimum`/`maximum`/`multipleOf`/`minLength`/`maxLength`, `minItems` only 0/1 (verified = no) | yes | [Anthropic structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) |
| ANT005 | anthropic-strict | error | no recursive schemas, external `$ref`, or `allOf` with `$ref` (verified = no) | no | [Anthropic structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) |
| ANT006 | anthropic-strict | error | only a fixed list of string `format`s (verified = no) | yes | [Anthropic structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) |

## Prior art

We are not the first. Please look at these too; they are good, and in some ways better.

- **[schemafit](https://github.com/OrionArchitekton/schemafit)**: a bare-schema linter with per-provider repair. It is more mature than schemacheck and, being a per-provider repairer, can tailor the repair to each provider. We have not benchmarked rule coverage against it, so it may catch things we miss.
- **mcp-lint** (npm): MCP-focused and checks live servers. If you want to test a running MCP server (connection, handshake, the tools it actually advertises), it does that and schemacheck does not; we are offline-only.
- **tool-schema**: a converter between provider tool formats. If you need to translate a tool definition from one provider's format to another, use it; schemacheck checks and repairs but does not convert formats.

Where schemacheck differs:

- **Tool-envelope awareness**: it understands OpenAI, Anthropic, MCP and Gemini tool wrappers and finds the schema inside them, instead of requiring a bare schema.
- **MCP `tools/list` input**: you can pipe a `tools/list` response or JSON-RPC result straight in.
- **One cross-provider `--fix` output**: a single rewrite that all selected profiles accept, rather than one repair per provider.
- **JSON-Pointer paths into the original file**, including the envelope, so issues are locatable in the file you actually have.

## Status

Early (v0.1). Rules marked "verified = no" are inferred or summary-sourced and may change.

**Limitations of the action:** `action.yml` has not run on a real GitHub runner. Locally we ran its exact command line (`schemacheck --profile "$SC_PROFILE" $SC_FILES`) via `uv run` (exit 1 on `examples/tools.json`, exit 0 on the fixed file) and parsed the YAML. Untested: `astral-sh/setup-uv@v5` inside a composite action, `uvx --from "$GITHUB_ACTION_PATH"` on a runner (uvx was blocked in our sandbox), and glob expansion on a runner. It has no `--fix` mode.

## Development

```sh
uv sync
uv run ruff check . && uv run pytest -q
```

See CONTRIBUTING.md and AI_DISCLOSURE.md. Licensed under MIT.
