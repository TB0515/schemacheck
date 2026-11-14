# Rules

Made by autonomous AI agents (Kiln). Status is `confirmed` when the Source URL is an official provider doc page that states the rule (re-checked against the live pages on 2026-11-14, see CHANGELOG), and `unverified` for warning-level rules that no primary doc confirms; third-party reports behind those are linked in the source comments of `src/schemacheck/rules/`. No rule is an error without a primary source. `anthropic-strict` also applies the `anthropic` rules.

| ID | Profile | Severity | Status | Checks | Fixable | Source |
|---|---|---|---|---|---|---|
| OAI001 | openai-strict | error | confirmed | Every object needs additionalProperties: false in OpenAI strict mode | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI002 | openai-strict | error | confirmed | All keys in properties must be listed in required in OpenAI strict mode | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI004 | openai-strict | error | confirmed | Root schema must be an object and must not use anyOf in OpenAI strict mode | no | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI005 | openai-strict | error | confirmed | Keyword not supported by OpenAI strict mode (allOf, not, dependentRequired, dependentSchemas, if, then, else) | no | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI007 | openai-strict | warning | unverified | Unverified: $ref other than the root '#' or a top-level $defs entry is not documented as supported by OpenAI strict mode (only a third-party SDK PR reports a rejection) | yes | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI008 | openai-strict | error | confirmed | Schema nests more than 10 levels deep (OpenAI strict allows 10) | no | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI013 | openai-strict | error | confirmed | Schema has more than 5000 object properties in total (OpenAI strict limit) | no | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI014 | openai-strict | error | confirmed | Schema has more than 1000 enum values in total (OpenAI strict limit) | no | https://developers.openai.com/api/docs/guides/structured-outputs |
| OAI015 | openai-strict | error | confirmed | Total length of property names, definition names, enum values and const values exceeds 120,000 characters (OpenAI strict limit) | no | https://developers.openai.com/api/docs/guides/structured-outputs |
| GEM001 | gemini | warning | unverified | Unverified: $schema may be rejected by Gemini in function parameters (only a third-party report; the docs say only a subset of the OpenAPI schema is supported) | yes | https://aistudio.google.com/docs/function-calling |
| GEM002 | gemini | warning | unverified | Unverified: $ref / $defs may be rejected by Gemini in function declarations; inline them (only a third-party report; the structured-output guide shows $defs/$ref working) | yes | https://aistudio.google.com/docs/function-calling |
| GEM003 | gemini | warning | unverified | Unverified: Gemini may reject const, and the Schema reference documents enum only for STRING (only a third-party report; the structured-output guide lists numeric enums) | yes | https://aistudio.google.com/api-reference/caching |
| GEM004 | gemini | warning | unverified | Unverified: oneOf may be rejected by Gemini (only a third-party report; oneOf is absent from the documented Schema field list) | yes | https://aistudio.google.com/api-reference/caching |
| GEM005 | gemini | warning | unverified | Unverified: anyOf is documented as supported by Gemini but adds branching that can exceed complexity limits; third-party reports of rejection exist | no | https://aistudio.google.com/docs/structured-output |
| GEM006 | gemini | warning | unverified | Unverified: Keyword is not in Gemini's documented Schema field list (the docs say only a subset of the OpenAPI schema is supported); type arrays are accepted by the structured-output guide | yes | https://aistudio.google.com/docs/function-calling |
| ANT001 | anthropic | error | confirmed | input_schema must be a JSON Schema object (type: object at the root) | yes | https://platform.claude.com/docs/en/api/messages/create |
| ANT002 | anthropic | error | confirmed | Tool name must match ^[a-zA-Z0-9_-]{1,128}$ | yes | https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools |
| ANT003 | anthropic-strict | error | confirmed | Strict tools require additionalProperties: false on every object | yes | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT004 | anthropic-strict | error | confirmed | Strict tools do not support numeric/string/array size constraints | yes | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT005 | anthropic-strict | error | confirmed | Strict tools do not support recursive schemas, external $ref, or allOf with $ref | no | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT006 | anthropic-strict | error | confirmed | Strict tools only support a fixed list of string formats | yes | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT010 | anthropic-strict | error | confirmed | More than 24 optional parameters (not in required); the limit is a total across all strict schemas in one request, and this checks one schema | no | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| ANT011 | anthropic-strict | error | confirmed | More than 16 parameters use anyOf or type arrays; the limit is a total across all strict schemas in one request, and this checks one schema | no | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |


Not implemented: OAI003 (advice, not a rejection), OAI006 (supported, no rule), OAI009 (unlisted `format` rejection unverified), OAI010 (fine-tuned models only), OAI011/OAI012/ANT008 (unverified), GEM007/GEM008 (notes), GEM009 (no sourced threshold), ANT007 (numeric limits unverified), ANT009 (note).
