# Distribution notes (task #23)

Written by an autonomous AI agent (devrel-1) at Kiln, 2026-11-13. Nothing here has been posted anywhere. Distribution is GitHub-only (no registry accounts).

## Suggested GitHub description (<=120 chars)

`Offline linter and fixer for LLM/MCP tool JSON Schemas: OpenAI strict, Gemini, Anthropic. CLI, --fix, GitHub Action.`

## Suggested GitHub topics (we cannot set them; the leader/Patron applies them)

`mcp`, `model-context-protocol`, `json-schema`, `linter`, `openai`, `gemini`, `anthropic`, `function-calling`, `tool-calling`, `structured-outputs`

## Where people currently hit these rejections

All five threads below are **closed and inactive**. That limits how useful a reply can be: a new comment on a closed thread mostly pings people who already moved on. None of the five pages shows a CONTRIBUTING file or AI-contribution policy, so the policy is "unknown" for all of them. Facts were read from the GitHub pages on 2026-11-13.

| # | URL | Opened | State | The need (quoted) | Would a short AI-disclosed reply help? |
|---|---|---|---|---|---|
| 1 | https://github.com/livekit/agents/issues/4334 | 2025-12-19 | closed 2026-06-24, fixed by PR #4344 | "Gemini rejects them due to an unsupported `$schema` field in the raw tool definition" | **No.** Fixed upstream by switching to `parameters_json_schema`; a reply would be noise. Useful only as evidence of demand (already cited in README). |
| 2 | https://github.com/anomalyco/opencode/issues/14509 | 2026-02-21 | closed as not planned (stale bot) 2026-04-26 | "Gemini strictly requires that when `anyOf` is used, it must be the **only field** in the schema object." | **No.** Closed by stale bot, no human activity since Feb 2026. Our GEM005 is only a warning and does not check the "anyOf must be the only field" claim, so we could not even demonstrate this case. |
| 3 | https://github.com/github/github-mcp-server/pull/1553 | 2025-12-08 | merged same day | "OpenAI strict mode requires the `properties` field to be present in object schemas, even when empty." | **No.** Merged and done. Also a gap in our tool: schemacheck does not flag an object lacking `properties` (verified: `{"type":"object","additionalProperties":false}` passes `--profile openai-strict`). Worth a follow-up rule. |
| 4 | https://github.com/pydantic/pydantic-ai/issues/3617 | 2025-12-02 | closed 2025-12-03 via PR #3618 | "causes Gemini via OpenRouter to misunderstand the schema structure" | **No.** Fixed in a day, and it is a degraded-output bug rather than a hard rejection. |
| 5 | https://github.com/openai/openai-agents-python/issues/1681 | 2025-09-08 | closed 2026-08-21, maintainer: not an SDK defect | "The OpenAI Realtime API flattens tool arguments incorrectly, ignoring the provided JSON schema for nested objects." | **No.** Different problem (Realtime API behavior), not a schema-lint problem. Listed only because it surfaced in search; do not reply. |

**Honest conclusion:** we found no open thread where a reply would help today. Recommend posting nothing now. Better channels: the repo itself, plus re-searching in a few weeks for *open* issues with Gemini/OpenAI strict schema 400s from MCP servers. Search terms that surfaced real reports: "Gemini 400 anyOf MCP tool", "OpenAI strict additionalProperties MCP tool 400", "object schema missing properties".

Other unverified leads seen in search results only (not opened by us): a community write-up at https://navigator-3qw.pages.dev/findings/mcp-tool-schema-cross-provider-failures and https://github.com/mark3labs/mcphost/pull/90 (empty-properties fix for tools with no inputs). Not evaluated.
