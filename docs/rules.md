# Rules

Made by autonomous AI agents (Kiln). Every rule cites an official doc or a real failing issue/PR; the `Verified` column is `no` where the rulebook quote was summary-only or the rule is inferred (a separate task re-checks those). `anthropic-strict` also applies the `anthropic` rules.

| ID | Profile | Severity | Checks | Fixable | Verified | Source |
|---|---|---|---|---|---|---|
| OAI001 | openai-strict | error | Every object needs additionalProperties: false in OpenAI strict mode. Reporting node: object schema whose `additionalProperties` is not `false`. | yes | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI002 | openai-strict | error | All keys in properties must be listed in required in OpenAI strict mode. One issue per property key missing from `required`. | yes | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI004 | openai-strict | error | Root schema must be an object and must not use anyOf in OpenAI strict mode. Root has `anyOf`, or a root `type` other than `object`. | no | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI005 | openai-strict | error | Keyword not supported by OpenAI strict mode (allOf, not, dependentRequired, dependentSchemas, if, then, else). `allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`, `then`, `else`. | no | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI007 | openai-strict | error | $ref must point at a top-level definition ($defs or definitions) or the root '#'. `$ref` that is not `#`, `#/$defs/X` or `#/definitions/X`. Source is a real failing case (non-strict path observed). | yes | yes | https://github.com/modelcontextprotocol/typescript-sdk/pull/1082 |
| OAI008 | openai-strict | error | Schema nests more than 10 levels deep (OpenAI strict allows 10). Object nested at level 11 (root object = level 1). Property-count/enum limits are not checked. | no | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| GEM001 | gemini | error | $schema is rejected by Gemini in function parameters. `$schema` key anywhere. | yes | yes | https://github.com/livekit/agents/issues/4334 |
| GEM002 | gemini | error | $ref / $defs are rejected by Gemini in function declarations; inline them. `$ref` and `$defs`. Also cites the Gemini Schema reference. | yes | yes | https://github.com/anomalyco/opencode/pull/12911 |
| GEM003 | gemini | error | Gemini rejects const, and enum is only allowed for STRING type. `const`; `enum` on a non-string `type`. | yes | yes | https://github.com/anomalyco/opencode/pull/12911 |
| GEM004 | gemini | error | oneOf is rejected by Gemini. `oneOf`. | yes | yes | https://github.com/anomalyco/opencode/pull/12911 |
| GEM005 | gemini | warning | anyOf is in Gemini's Schema field list but reported rejected or limited in practice. `anyOf` (docs list it, the PR reports rejection). | no | no | https://github.com/anomalyco/opencode/pull/12911 |
| GEM006 | gemini | warning | Keyword is not in Gemini's documented Schema field list and may be rejected or ignored. Keywords absent from the Schema field list (allOf, not, if/then/else, exclusiveMinimum/Maximum, multipleOf, patternProperties, uniqueItems, dependentRequired/Schemas, prefixItems, `$id`) and type arrays. `additionalProperties` is deliberately not flagged. | yes | no | https://aistudio.google.com/api-reference/caching |
| ANT001 | anthropic | error | input_schema must be a JSON Schema object (type: object at the root). Root has no `type`, or `type` is not `object` (inferred from the docs examples, so unverified). | yes | no | https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use |
| ANT002 | anthropic | error | Tool name must match ^[a-zA-Z0-9_-]{1,128}$. Tool name (the `name` argument) must match `^[a-zA-Z0-9_-]{1,128}$`; reported at the schema root. | yes | yes | https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use |
| ANT003 | anthropic-strict | error | Strict tools require additionalProperties: false on every object. Object without `additionalProperties: false` (strict tools). | yes | no | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT004 | anthropic-strict | error | Strict tools do not support numeric/string/array size constraints. `minimum`, `maximum`, `multipleOf`, `minLength`, `maxLength`, `minItems` other than 0/1. | yes | no | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT005 | anthropic-strict | error | Strict tools do not support recursive schemas, external $ref, or allOf with $ref. External `$ref`, recursive `$ref`, `allOf` containing `$ref`. | no | no | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT006 | anthropic-strict | error | Strict tools only support a fixed list of string formats. String `format` outside date-time, time, date, duration, email, hostname, uri, ipv4, ipv6, uuid. | yes | no | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |

Rules that also cite the Gemini Schema reference: GEM001-GEM005 (https://aistudio.google.com/api-reference/caching).

Not implemented: OAI003 (advice, not a rejection), OAI006 (supported, no rule), OAI009 (unlisted `format` rejection unverified), OAI010 (fine-tuned models only), OAI011/OAI012/ANT008 (unverified), GEM007/GEM008 (notes), GEM009 (no sourced threshold), ANT007 (numeric limits unverified), ANT009 (note).
