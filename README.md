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
examples/tools.json:/tools/0/inputSchema/$schema: [gemini] GEM001 Unverified: $schema may be rejected by Gemini in function parameters (...)
examples/tools.json:/tools/0/inputSchema/$defs: [gemini] GEM002 Unverified: $ref / $defs may be rejected by Gemini ... ($defs) (...)
examples/tools.json:/tools/0/inputSchema/properties/filter/$ref: [gemini] GEM002 Unverified: ... ($ref)
examples/tools.json:/tools/0/inputSchema/$defs/Filter: [openai-strict] OAI001 ...
examples/tools.json:/tools/0/inputSchema/$defs/Filter/properties/state: [openai-strict] OAI002 ...
```

(URLs shortened here; the real output ends each line with the doc link.)

**After** `--fix` (stderr says `note: dropped '$schema' at /`): `$schema` and `$defs` are gone, `Filter` is inlined, every object has `additionalProperties: false`, and every property is in `required`. Re-checking prints nothing and exits 0 (`--json` prints `{"issues":[]}`). Note the fix makes optional parameters required, as OpenAI strict mode demands; it does not add nullability.

## How is this different from schemafit?

[schemafit](https://github.com/OrionArchitekton/schemafit) is the closest existing tool, and it is more mature than we are. It repairs per provider; we produce one cross-provider output. What we offer on top:

- **Rules cited and checked against the docs.** v0.1 compared all 18 rules to provider docs and schemafit ([docs/rule-verification.md](docs/rule-verification.md): 8 CONFIRMED, 10 WEAK). v0.2.0 re-checked the WEAK ones against the primary doc pages (see [CHANGELOG.md](CHANGELOG.md)): 3 upgraded to confirmed (ANT001, ANT005, ANT006), 7 downgraded to unverified warnings (GEM001-GEM006, OAI007), and 5 documented limit rules added (OAI013-OAI015, ANT010, ANT011). Reports were written by AI agents; read them before trusting them.
- **Tool-envelope awareness**: OpenAI, Anthropic, MCP and Gemini wrappers, MCP `tools/list` results and JSON-RPC responses, with JSON Pointers into your original file.
- **Checks schemafit did not flag in our fixtures**: tool-name rules (ANT002), `$schema` (GEM001), `const`/non-string `enum` for Gemini (GEM003). The same comparison shows schemafit flagging things we do not, such as `pattern` and `exclusiveMinimum` under Anthropic. We have not benchmarked beyond those fixtures.

### Unverified rules (warnings only)

No primary doc confirms these, so they are warnings and never change the exit code: GEM001-GEM006 (Gemini docs say only "a subset of the OpenAPI schema is supported" and never list `$schema`, `$ref`, `const` or `oneOf` as rejected; the structured-output guide shows `$defs`/`$ref`, `anyOf`, numeric enums and type arrays working) and OAI007 (OpenAI documents `$ref` and recursion as supported; the nested-`$ref` rejection comes only from an SDK PR). Known gaps: OpenAI's 15,000-character enum sub-limit (applies above 250 enum values) is not checked; the Anthropic optional-parameter and union limits are totals across a whole request, and schemacheck checks one schema at a time, so ANT010/ANT011 can only prove a single schema is already over the limit. Objects with no `properties` are not checked.

## Rules

Every `error` rule cites an official provider doc page (re-checked against the live docs for v0.2.0). Rules with status `unverified` are warnings only: no primary doc confirms the rejection, so schemacheck will not fail your build on them by severity. Full details in [docs/rules.md](docs/rules.md).

| ID | Profile | Severity | Status | Rule | Fixable | Source |
|---|---|---|---|---|---|---|
| OAI001 | openai-strict | error | confirmed | Every object needs additionalProperties: false in OpenAI strict mode | yes | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI002 | openai-strict | error | confirmed | All keys in properties must be listed in required in OpenAI strict mode | yes | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI004 | openai-strict | error | confirmed | Root schema must be an object and must not use anyOf in OpenAI strict mode | no | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI005 | openai-strict | error | confirmed | Keyword not supported by OpenAI strict mode (allOf, not, dependentRequired, dependentSchemas, if, then, else) | no | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI007 | openai-strict | warning | unverified | Unverified: $ref other than the root '#' or a top-level $defs entry is not documented as supported by OpenAI strict mode (only a third-party SDK PR reports a rejection) | yes | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI008 | openai-strict | error | confirmed | Schema nests more than 10 levels deep (OpenAI strict allows 10) | no | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI013 | openai-strict | error | confirmed | Schema has more than 5000 object properties in total (OpenAI strict limit) | no | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI014 | openai-strict | error | confirmed | Schema has more than 1000 enum values in total (OpenAI strict limit) | no | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| OAI015 | openai-strict | error | confirmed | Total length of property names, definition names, enum values and const values exceeds 120,000 characters (OpenAI strict limit) | no | <https://developers.openai.com/api/docs/guides/structured-outputs> |
| GEM001 | gemini | warning | unverified | Unverified: $schema may be rejected by Gemini in function parameters (only a third-party report; the docs say only a subset of the OpenAPI schema is supported) | yes | <https://aistudio.google.com/docs/function-calling> |
| GEM002 | gemini | warning | unverified | Unverified: $ref / $defs may be rejected by Gemini in function declarations; inline them (only a third-party report; the structured-output guide shows $defs/$ref working) | yes | <https://aistudio.google.com/docs/function-calling> |
| GEM003 | gemini | warning | unverified | Unverified: Gemini may reject const, and the Schema reference documents enum only for STRING (only a third-party report; the structured-output guide lists numeric enums) | yes | <https://aistudio.google.com/api-reference/caching> |
| GEM004 | gemini | warning | unverified | Unverified: oneOf may be rejected by Gemini (only a third-party report; oneOf is absent from the documented Schema field list) | yes | <https://aistudio.google.com/api-reference/caching> |
| GEM005 | gemini | warning | unverified | Unverified: anyOf is documented as supported by Gemini but adds branching that can exceed complexity limits; third-party reports of rejection exist | no | <https://aistudio.google.com/docs/structured-output> |
| GEM006 | gemini | warning | unverified | Unverified: Keyword is not in Gemini's documented Schema field list (the docs say only a subset of the OpenAPI schema is supported); type arrays are accepted by the structured-output guide | yes | <https://aistudio.google.com/docs/function-calling> |
| ANT001 | anthropic | error | confirmed | input_schema must be a JSON Schema object (type: object at the root) | yes | <https://platform.claude.com/docs/en/api/messages/create> |
| ANT002 | anthropic | error | confirmed | Tool name must match ^[a-zA-Z0-9_-]{1,128}$ | yes | <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools> |
| ANT003 | anthropic-strict | error | confirmed | Strict tools require additionalProperties: false on every object | yes | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> |
| ANT004 | anthropic-strict | error | confirmed | Strict tools do not support numeric/string/array size constraints | yes | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> |
| ANT005 | anthropic-strict | error | confirmed | Strict tools do not support recursive schemas, external $ref, or allOf with $ref | no | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> |
| ANT006 | anthropic-strict | error | confirmed | Strict tools only support a fixed list of string formats | yes | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> |
| ANT010 | anthropic-strict | error | confirmed | More than 24 optional parameters (not in required); the limit is a total across all strict schemas in one request, and this checks one schema | no | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> |
| ANT011 | anthropic-strict | error | confirmed | More than 16 parameters use anyOf or type arrays; the limit is a total across all strict schemas in one request, and this checks one schema | no | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> |

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

Early (v0.2). Rules with status `unverified` are warnings and may change.

**Limitations of the action:** `action.yml` has not run on a real GitHub runner. Locally we ran its exact command line (`schemacheck --profile "$SC_PROFILE" $SC_FILES`) via `uv run` (exit 1 on `examples/tools.json`, exit 0 on the fixed file) and parsed the YAML. Untested: `astral-sh/setup-uv@v5` inside a composite action, `uvx --from "$GITHUB_ACTION_PATH"` on a runner (uvx was blocked in our sandbox), and glob expansion on a runner. It has no `--fix` mode.

## Development

```sh
uv sync
uv run ruff check . && uv run pytest -q
```

See CONTRIBUTING.md and AI_DISCLOSURE.md. Licensed under MIT.
