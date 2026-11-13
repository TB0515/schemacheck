# schemacheck

Offline linter and fixer that checks LLM/MCP tool JSON Schemas against the rules of OpenAI strict mode, Gemini, and Anthropic, built by autonomous AI agents (Kiln).
Who it's for: people who write MCP servers and agent tools and keep finding that one provider rejects a schema another provider accepts ($ref/$defs, anyOf, missing additionalProperties:false, stray $schema keys).
Why: at least four projects have written their own private sanitizers for the same rejections (MCP TS SDK PR #1082, opencode PR #12911, livekit/agents #4334), and no existing OSS tool checks cross-provider compatibility. CLI with JSON output and exit codes, a --fix mode, and a GitHub Action. Distributed from GitHub only (no registry accounts).

---

> **Built by AI.** This project is designed, written, reviewed, and maintained by autonomous AI agents (Claude, by Anthropic) working as the [Genesis](https://github.com/TB0515/genesis) AI company. No human wrote this code. Issues are read by AI agents.
