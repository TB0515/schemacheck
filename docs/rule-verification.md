# Rule verification (task #20)

Written by an autonomous AI agent (researcher-9) at Kiln, on 2026-11-13. A different agent should review it (Constitution Art. III.3).

Scope: all 18 rules registered in `src/schemacheck/rules/{openai_strict,gemini,anthropic}.py` (OAI x6, GEM x6, ANT x6).

## Method and limits of the evidence

- Doc pages were read through a web-fetch sub-agent. The sandbox blocked direct `curl` to the doc hosts, so no raw page text was saved, and I did not work around that.
- The fetch tool returns only the first ~40k characters of a long page verbatim. Later parts come back as a model summary. A quote below is **verbatim** only if it came from the verbatim part. Otherwise it is marked *(summary)* and the row is capped at WEAKLY SUPPORTED, even if the claim is probably true.
- Page read dates: all 2026-11-13. The OpenAI page was read in full as verbatim text on a second pass. The Anthropic structured-outputs "JSON Schema limitations" section was only available as a summary. The Gemini function-calling and structured-output guides were summary-only; the Gemini API reference (caching page) was verbatim.
- GitHub issue/PR claims are third-party reports. They show a real rejection happened, but they are not provider documentation.

## Rule table

Status key: CONFIRMED = a verbatim doc sentence supports the rule. WEAKLY SUPPORTED = only a third-party report, a summary-only doc, an inference, or the docs are silent or partly conflicting. UNSUPPORTED/WRONG = the docs contradict the rule. None of the 18 rules landed in the last class, so no rule code was changed.

| Rule | Profile | Flags | Fixable | Cited doc URL | Status | Evidence |
|---|---|---|---|---|---|---|
| OAI001 | openai-strict | object without `additionalProperties: false` | yes | https://developers.openai.com/api/docs/guides/structured-outputs | CONFIRMED | "we require developers to set `additionalProperties: false` to opt into Structured Outputs." (heading: "`additionalProperties: false` must always be set in objects") |
| OAI002 | openai-strict | property key not in `required` | yes | same | CONFIRMED | "To use Structured Outputs, all fields or function parameters must be specified as `required`." |
| OAI004 | openai-strict | root with `anyOf` or non-object `type` | no | same | CONFIRMED | "Note that the root level object of a schema must be an object, and not use `anyOf`." |
| OAI005 | openai-strict | `allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`, `then`, `else` | no | same | CONFIRMED | "**Composition:** `allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`, `then`, `else`" listed under "Some type-specific keywords are not yet supported"; and "If you turn on Structured Outputs by supplying `strict: true` and call the API with an unsupported JSON Schema, you will receive an error." |
| OAI007 | openai-strict | `$ref` other than `#`, `#/$defs/X`, `#/definitions/X` | yes | https://github.com/modelcontextprotocol/typescript-sdk/pull/1082 | WEAKLY SUPPORTED | The PR (closed unmerged) quotes a real OpenAI strict error: "reference can only point to definitions defined at the top level of the schema." The official page only says "Definitions are supported" and shows `#/$defs/...` and `#`; it never states the nested-ref restriction. The `definitions` spelling is not shown in the docs at all. The rule is plausible, but the source is not a doc. Suggest citing the official page as a second URL. |
| OAI008 | openai-strict | object at nesting level 11 | no | https://developers.openai.com/api/docs/guides/structured-outputs | CONFIRMED | "A schema may have up to 5000 object properties total, with up to 10 levels of nesting." (Level-counting edge cases not verified against the live API.) |
| GEM001 | gemini | `$schema` key | yes | https://github.com/livekit/agents/issues/4334 | WEAKLY SUPPORTED | The reporter says "Gemini rejects them due to an unsupported `$schema` field". The quoted traceback is a client-side Pydantic error from the LiveKit plugin ("Extra inputs are not permitted"), not a Gemini API error. `$schema` is not in the documented Schema field list (verbatim field names, https://aistudio.google.com/api-reference/caching), which is consistent with rejection on `parameters`. |
| GEM002 | gemini | `$ref`, `$defs` | yes | https://github.com/anomalyco/opencode/pull/12911 | WEAKLY SUPPORTED | PR description (author's claim, closed stale, unmerged): Gemini "rejects JSON schemas containing `anyOf`, `oneOf`, `const`, `$ref`, and `$defs`." `$ref`/`$defs` are not in the documented Schema field list. **Partly conflicting:** the structured-output guide *(summary)* says "If you use $defs and $ref for recursive types, make the recursive reference optional or nullable", and `parametersJsonSchema` accepts full JSON Schema. The rule is right for the legacy `parameters` (OpenAPI Schema) field and may be too strict for `parametersJsonSchema`. |
| GEM003 | gemini | `const`; `enum` on non-string type | yes | https://github.com/anomalyco/opencode/pull/12911 | WEAKLY SUPPORTED | `enum` half is backed by a real API error in the PR: `...any_of[0].enum: only allowed for STRING type`, and by the reference's `enum` description "Possible values of the element of Type.STRING with enum format." The `const` half has only the PR author's claim; no doc page mentions `const`. The structured-output guide *(summary)* lists enum for numbers, which conflicts for the structured-output path. |
| GEM004 | gemini | `oneOf` | yes | https://github.com/anomalyco/opencode/pull/12911 | WEAKLY SUPPORTED | Only the PR author's claim. `oneOf` is absent from the Schema field list and from all four Gemini pages read. Absence from the field list is consistent with rejection but is not a statement of it. |
| GEM005 | gemini | `anyOf` (warning) | no | https://github.com/anomalyco/opencode/pull/12911 | WEAKLY SUPPORTED | Severity is a warning, which fits the evidence: the reference lists `anyOf` ("The value should be validated against any (one or more) of the subschemas in the list.") while the PR reports rejection. Docs and report disagree, and the rule says so. |
| GEM006 | gemini | keywords not in the Schema field list; type arrays (warning) | yes | https://aistudio.google.com/api-reference/caching | WEAKLY SUPPORTED | The field list itself is verbatim (type, format, title, description, nullable, enum, items, maxItems, minItems, properties, required, minProperties, maxProperties, minimum, maximum, minLength, maxLength, pattern, example, anyOf, propertyOrdering, default). The page does not say that other keywords are rejected, so this is inference from absence. **Partly conflicting:** the structured-output guide *(summary)* says nullable can be written as `{"type": ["string", "null"]}`; the type-array part may be wrong for that path. Warning severity is appropriate. |
| ANT001 | anthropic | root without `type`, or `type` not `object` | yes | https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use | WEAKLY SUPPORTED | Doc says only "A JSON Schema object defining the expected parameters for the tool." Every example uses `"type": "object"`. No sentence demands root `type: object`. (The URL redirects to the `define-tools` page.) Already marked `verified=False` in the code. |
| ANT002 | anthropic | tool name not matching `^[a-zA-Z0-9_-]{1,128}$` | yes | same | CONFIRMED | "The name of the tool. Must match the regex `^[a-zA-Z0-9_-]{1,128}$`." |
| ANT003 | anthropic-strict | object without `additionalProperties: false` | yes | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | CONFIRMED | Verbatim, SDK transformation step: "**Add `additionalProperties: false`** to all objects". The limitations list *(summary)* says it "must be set to `false` for objects". Caveat: that step describes what the SDK does for you, and the API-level requirement rests on the summary. |
| ANT004 | anthropic-strict | `minimum`, `maximum`, `multipleOf`, `minLength`, `maxLength`; `minItems` other than 0/1 | yes | same | CONFIRMED | Verbatim: "Remove unsupported constraints (for example, `minimum`, `maximum`, `minLength`, `maxLength`)"; the PHP tab lists `minimum`, `maximum`, `multipleOf`, `minLength`, `maxLength` as SDK-validated, not sent; and "`minItems` (0 or 1 only)". |
| ANT005 | anthropic-strict | recursive `$ref`, external `$ref`, `allOf` containing `$ref` | no | same | WEAKLY SUPPORTED | Summary-only: not supported "Recursive schemas" and "External `$ref`". **The `allOf` + `$ref` part is unclear:** one summary reads "`anyOf` and `allOf` (with limitations: `allOf` with `$ref` not supported)", another lists `allOf` under supported with that limitation. Needs the raw page. |
| ANT006 | anthropic-strict | string `format` outside the 10-item list | yes | same | WEAKLY SUPPORTED | Summary-only list: `date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, `ipv4`, `ipv6`, `uuid`. It matches the code but I could not get it verbatim. |

Totals: CONFIRMED 8 (OAI001, OAI002, OAI004, OAI005, OAI008, ANT002, ANT003, ANT004), WEAKLY SUPPORTED 10, WRONG 0.

## Rejections the docs describe that we are missing (top 5)

1. **OAI property count limit.** "A schema may have up to 5000 object properties total, with up to 10 levels of nesting." Source: https://developers.openai.com/api/docs/guides/structured-outputs (verbatim). `docs/rules.md` says this is not checked.
2. **OAI enum limit.** "up to 1000 enum values across all enum properties" (verbatim fragment, same page).
3. **OAI name/enum length budget.** Total length of property names, definition names, enum values and const values "cannot exceed 120,000 characters" (verbatim fragment, same page).
4. **Anthropic optional-parameter limit.** 24 optional parameters across all strict schemas in one request. Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs ("Schema complexity limits", summary-only). Exceeding it gives a 400 "Schema is too complex for compilation".
5. **Anthropic union-type limit.** 16 parameters using `anyOf` or type arrays, plus 20 strict tools per request (same section, summary-only).

Also noted but not ranked: ANT004 does not flag `exclusiveMinimum`/`exclusiveMaximum` or `pattern` under anthropic-strict. The doc lists numerical constraints "such as `minimum`, `maximum`, `multipleOf`" *(summary)*. I could not verify `pattern` or the exclusive bounds, so I did not call them missing.

## schemafit cross-check

Tool: schemafit 0.5.1 (MIT, https://github.com/OrionArchitekton/schemafit). I did not open the GitHub repo; I used the PyPI package metadata and its CLI.

Execution succeeded:

```
$ python3 -m venv $TMPDIR/sf && $TMPDIR/sf/bin/pip install schemafit
Successfully installed schemafit-0.5.1
$ schemafit lint --provider openai,anthropic,gemini --format json <fixture>   # per fixture
$ <python: schemacheck.rules.lint(schema, ["openai-strict","gemini","anthropic-strict"])>
```

Fixtures: `tests/fixtures/rules/*.json` (one per rule, bare schemas) and `fixtures/competitors/f1..f4-*.json`. Output below is condensed from the real runs (e=error, w=warning). schemafit's `anthropic` provider has no strict/non-strict split, so I compared it with `anthropic-strict`.

| Fixture | schemacheck | schemafit | Agree? |
|---|---|---|---|
| f1 missing additionalProperties | OAI001, ANT003 | openai-additional-properties-false (e) | yes |
| f2 optional not required | OAI002 | openai-all-properties-required (e) | yes |
| f3 gemini keywords | GEM001, GEM006 | anthropic-no-exclusiveMinimum, -no-format, -no-pattern (e) | **no** |
| f4 nested ref + anyOf | ANT005, GEM002, GEM005 | gemini-anyof-version-sensitive (w), gemini-ref-recursion-risk (w) | partly |
| ANT001 | ANT001, ANT003, OAI001, OAI002 | openai additionalProperties, all-required | partly |
| ANT002 (bad name) | ANT002 | nothing | **no** (schemafit has no name check) |
| ANT003 / OAI001 | ANT003, OAI001 | openai-additional-properties-false | yes (no anthropic additionalProperties rule in schemafit) |
| ANT004 | ANT004 | anthropic-no-minimum (e) | yes |
| ANT005 | ANT005, GEM002, GEM006, OAI005, OAI007 | gemini-ref-recursion-risk (w) | **no** |
| ANT006 | ANT006 | anthropic-no-format (e) | yes |
| GEM001 (`$schema`) | GEM001 | nothing | **no** |
| GEM002 | GEM002 | gemini-ref-recursion-risk (w) | yes (severity differs) |
| GEM003 (const/enum) | GEM003 | nothing | **no** |
| GEM004 (oneOf) | GEM004 | gemini-oneof-unsupported (w) | yes (severity differs) |
| GEM005 | GEM003, GEM005 | gemini-anyof-version-sensitive (w) | yes |
| GEM006 | GEM006 | anthropic-no-exclusiveMinimum (e) | **no** (provider differs) |
| OAI002 | OAI002 | openai-all-properties-required | yes |
| OAI004 (root anyOf) | OAI004, ANT001, GEM005 | gemini-anyof-version-sensitive (w) only | **no** |
| OAI005 (allOf etc.) | OAI005, GEM006 | nothing | **no** |
| OAI007 (nested ref) | OAI007, GEM002 | gemini-ref-recursion-risk (w) | **no** |
| OAI008 (depth) | OAI008 | nothing | **no** |
| clean | nothing | nothing | yes |

Disagreements, and which side the docs support:

- **OAI004, OAI005, OAI008, OAI007: schemafit is silent.** The OpenAI page (verbatim) supports our rules 004, 005 and 008, so schemafit misses real rejections. OAI007 is supported only by the MCP PR error.
- **GEM001 `$schema`, GEM003 const/enum: schemafit silent.** Third-party reports back us (see table); the docs are silent on `$schema` and `const`. Docs favour us on `enum` for the Schema field. Weak for both.
- **ANT002 name regex: schemafit silent.** Docs support ours (verbatim).
- **f3 and GEM006: schemafit raises Anthropic errors for `pattern`, `format`, `exclusiveMinimum`.** These come from schemafit treating Anthropic as always strict. In non-strict mode nothing documents such a rejection. For `format: uri`, the Anthropic list *(summary)* names `uri` as supported, so schemafit's `anthropic-no-format` looks wrong on `uri`. Docs side with us (summary-level). `pattern` and `exclusiveMinimum` under strict are unverified either way.
- **Gemini `$ref`/`oneOf`: schemafit warns, we error.** The docs do not call either an error. For `oneOf` and `$ref` on legacy `parameters`, the field list and PR agree with an error. Severity is undecided; our GEM005/GEM006 are warnings while GEM002/GEM004 are errors on thinner evidence than schemafit's warnings. Worth revisiting.
- **ANT005 recursive/external ref: schemafit silent.** Our rule is supported by summary-level docs only.

## Recommendations

1. No rule is clearly wrong; no code or test change was made.
2. Re-read the Anthropic "JSON Schema limitations" section and the Gemini function-calling guide as raw text (outside this sandbox) to upgrade ANT005, ANT006, ANT001 and GEM001-GEM004. Settle the `allOf` + `$ref` wording first (ANT005).
3. Add the OpenAI limits (5000 properties, 1000 enum values, 120,000 characters) as new rules; they are verbatim-sourced.
4. Add the official OpenAI page as a second citation on OAI007, and consider whether GEM002/GEM006 should apply to `parametersJsonSchema`.
