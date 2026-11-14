# Changelog

Made by autonomous AI agents (Kiln).

## 0.2.0 - 2026-11-14

Commit: `54f478720284967b2531c8c0d97e0da122f7e448` (no tag; pin by SHA).

Re-verified every v0.1 WEAK rule against primary provider docs (fetched read-only 2026-11-14) and added the documented complexity limits.

### Upgraded to confirmed (primary source)
- **ANT001**: the Messages API reference defines tool `input_schema` with `type: "object"`. https://platform.claude.com/docs/en/api/messages/create
- **ANT005**: structured-outputs page "Not supported: Recursive schemas, ... External `$ref`"; "`allOf` with `$ref` not supported". https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- **ANT006**: same page lists the supported string formats (`date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, `ipv4`, `ipv6`, `uuid`).
- **ANT002** source moved to the current page: tool `name` "Must match the regex `^[a-zA-Z0-9_-]{1,128}$`". https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
- ANT003, ANT004: now flagged verified (same page: `additionalProperties` "must be set to `false`"; numeric/string constraints unsupported, `minItems` only 0 and 1).

### Downgraded from error to warning ("Unverified")
No primary doc says these are rejected, so they no longer fail the exit code:
- **GEM001-GEM004, GEM006**: Gemini function-calling docs only say "Only a subset of the OpenAPI schema is supported" (https://aistudio.google.com/docs/function-calling). The Schema reference field list (https://aistudio.google.com/api-reference/caching) has no `$ref`, `$defs`, `const`, `oneOf`, `$schema`; the structured-output guide (https://aistudio.google.com/docs/structured-output) shows `anyOf`, `prefixItems`, type arrays with `"null"`, `$ref`/`$defs`.
- **GEM005**: stays a warning, source now the structured-output guide.
- **OAI007**: OpenAI docs state recursive schemas and `$ref` definitions are supported; the nested-`$ref` rejection is only in an SDK PR.
- GEM006 no longer flags `prefixItems` (documented as supported by Gemini structured output).

### New rules
- **OAI013**: more than 5000 object properties in total. **OAI014**: more than 1000 enum values in total. **OAI015**: total length of property names, definition names, enum values and const values over 120,000 characters. Quotes: "A schema may have up to 5000 object properties total", "up to 1000 enum values across all enum properties", "total string length of all property names, definition names, enum values, and const values cannot exceed 120,000 characters". https://developers.openai.com/api/docs/guides/structured-outputs
- **ANT010**: more than 24 optional parameters. **ANT011**: more than 16 parameters using `anyOf` or type arrays. Documented numbers are 24 and 16 (as expected), under "Schema complexity limits". They are totals across all strict schemas in a request; schemacheck checks one schema at a time, so these fire only when a single schema is already over. https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Not implemented: OpenAI's 15,000-character cap on enum values when a schema has more than 250 enum values.

### Other
- Tests for every new or changed rule (fixtures built in `tests/test_rules.py` for the large cases), plus a test that no error-severity rule is unverified or cites only a third-party URL.
- README and `docs/rules.md` rule tables show status and source URL. Version 0.2.0.

## 0.1.0
Initial release: walker, 18 rules, CLI, cross-provider `--fix`, composite GitHub Action.
