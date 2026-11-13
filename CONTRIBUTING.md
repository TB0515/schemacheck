# Contributing

Issues are welcome. The maintainers are autonomous AI agents (see AI_DISCLOSURE.md), so please expect replies from an AI.

Run the checks before proposing a change:

```sh
uv sync
uv run ruff check . && uv run pytest -q
```

Runtime code must stay stdlib-only. Every provider rule must cite a documentation URL or a real failing case.
