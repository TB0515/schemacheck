# schemacheck

Offline linter and fixer that checks LLM/MCP tool JSON Schemas against OpenAI strict mode, Gemini, and Anthropic rules, for people who write MCP servers and agent tools.

> Built and maintained by autonomous AI agents at Kiln, an AI-only company. No human wrote this code. See AI_DISCLOSURE.md.

## Why

One provider rejects schemas that another accepts (`$ref`/`$defs`, `anyOf`, missing `additionalProperties: false`, stray `$schema` keys). At least four projects have written private sanitizers for these rejections (MCP TS SDK PR #1082, opencode PR #12911, livekit/agents #4334), and no existing OSS tool checks cross-provider compatibility. schemacheck is meant to be that tool: a CLI with JSON output, exit codes, a `--fix` mode, and (later) a GitHub Action.

## Quickstart

Run straight from GitHub (no registry needed):

```sh
uvx --from git+https://github.com/TB0515/schemacheck schemacheck --version
```

From a local checkout:

```sh
uv run schemacheck --help
echo '{}' > /tmp/x.json && uv run schemacheck --json /tmp/x.json   # {"issues":[]}
```

## Usage

```
schemacheck [--profile {openai-strict,gemini,anthropic,all}] [--fix] [--json] FILE...
```

Exit codes: 0 no issues, 1 issues found, 2 usage error / unreadable file / invalid JSON. The rules and `--fix` are not implemented yet; the CLI currently only parses each file.

## Status

pre-alpha. The CLI surface is stubbed; no rules yet.

## Development

```sh
uv sync
uv run ruff check . && uv run pytest -q
```

See CONTRIBUTING.md and AI_DISCLOSURE.md. Licensed under MIT.
