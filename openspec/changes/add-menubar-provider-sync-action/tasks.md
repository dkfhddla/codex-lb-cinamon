# Tasks

- [x] Add OpenSpec requirements for a macOS menu bar provider sync action.
- [x] Add a runtime helper for invoking `codex-provider sync`.
- [x] Wire provider sync status and action into the AppKit menu bar app.
- [x] Validate:
  - `uv run python -m pytest tests/unit/test_menubar_runtime.py`
  - `uv run python -m ruff check app/menubar_runtime.py app/menubar_app.py tests/unit/test_menubar_runtime.py`
  - `uv run python -m ty check app/menubar_runtime.py app/menubar_app.py tests/unit/test_menubar_runtime.py`
