# Tasks

- [x] Add OpenSpec requirements for macOS menu bar runtime control.
- [x] Add pure Python runtime-control helpers with unit tests.
- [x] Add CLI options for managed macOS menu bar mode.
- [x] Wire runtime-control actions into the AppKit menu bar app.
- [x] Run targeted Python verification and note platform limitations.
  - `.venv/bin/python -m pytest tests/unit/test_menubar_runtime.py tests/unit/test_cli.py tests/unit/test_menubar_summary.py`
  - `.venv/bin/python -m ruff check app/menubar_runtime.py app/menubar_app.py app/cli.py tests/unit/test_menubar_runtime.py tests/unit/test_cli.py`
  - `.venv/bin/python -m ty check app/menubar_runtime.py app/menubar_app.py app/cli.py tests/unit/test_menubar_runtime.py tests/unit/test_cli.py`
  - `openspec validate --specs` could not run because the `openspec` executable is unavailable in this environment.
