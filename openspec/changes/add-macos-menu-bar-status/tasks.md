# Tasks

- [x] Add OpenSpec requirements for a macOS menu bar status app.
- [x] Add pure Python summary fetching/formatting helpers with tests.
- [x] Add the macOS AppKit menu bar runtime.
- [x] Add a CLI subcommand to launch the menu bar app.
- [x] Run targeted Python verification and note platform limitations.
  - `ruff check app/menubar_summary.py app/menubar_app.py app/cli.py tests/unit/test_menubar_summary.py tests/unit/test_cli.py`
  - `ty check app/menubar_summary.py app/menubar_app.py app/cli.py tests/unit/test_menubar_summary.py tests/unit/test_cli.py`
  - `pytest tests/unit/test_menubar_summary.py tests/unit/test_cli.py`
  - `openspec validate --specs` could not run because the `openspec` executable is unavailable in this environment.
