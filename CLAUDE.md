# Python Package Management with uv
Use `uv` exclusively. Never use pip, poetry, or conda directly.
- Install/Remove: `uv add <pkg>` / `uv remove <pkg>`
- Sync/Lock: `uv sync` / `uv lock`
- Execution: `uv run <command>` (e.g., `uv run python`, `uv run pytest`)