# Windows Tray Runtime Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Windows system tray controller that starts, stops, inspects, and launch-at-login registers the existing tracked `codex-lb-cinamon` background server.

**Architecture:** Keep server lifecycle ownership in `app.cli_runtime`; add small Windows-specific helpers for current-user startup registration and tray UI orchestration. The CLI gets a `tray` subcommand that imports tray UI dependencies only after Windows support is confirmed.

**Tech Stack:** Python 3.13, argparse, FastAPI/uvicorn runtime helpers, Windows `winreg`, optional `pystray` and `Pillow`, pytest unit tests.

---

### Task 1: Startup Registration Helper

**Files:**
- Create: `app/windows_startup.py`
- Test: `tests/unit/test_windows_startup.py`

- [ ] Step 1: Write tests for command construction, enabled detection, enable, and disable using a fake registry object.
- [ ] Step 2: Run `uv run pytest tests/unit/test_windows_startup.py -q`; expect import failure before implementation.
- [ ] Step 3: Implement `StartupRegistration`, `build_tray_startup_command`, `is_startup_enabled`, `enable_startup`, and `disable_startup` with current-user Run key scope.
- [ ] Step 4: Run `uv run pytest tests/unit/test_windows_startup.py -q`; expect pass.

### Task 2: Tray Application Module

**Files:**
- Create: `app/tray.py`
- Test: `tests/unit/test_tray.py`

- [ ] Step 1: Write tests for unsupported platform failure and status snapshot behavior without importing pystray.
- [ ] Step 2: Run `uv run pytest tests/unit/test_tray.py -q`; expect import failure before implementation.
- [ ] Step 3: Implement typed tray state helpers and lazy dependency imports inside `run_tray_app()`.
- [ ] Step 4: Implement menu actions: start server, stop server, refresh status, open dashboard, open log, toggle startup, exit.
- [ ] Step 5: Run `uv run pytest tests/unit/test_tray.py -q`; expect pass.

### Task 3: CLI Subcommand and Packaging Metadata

**Files:**
- Modify: `app/cli.py`
- Modify: `pyproject.toml`
- Modify: `tests/unit/test_cli.py`

- [ ] Step 1: Add failing tests that `tray` dispatches to `app.tray.run_tray_app()` and unsupported-platform `SystemExit` messages propagate.
- [ ] Step 2: Run `uv run pytest tests/unit/test_cli.py -q`; expect tray tests fail before implementation.
- [ ] Step 3: Add `tray` parser subcommand and `_run_tray()` dispatcher using lazy import.
- [ ] Step 4: Add `[project.optional-dependencies].tray = ["pystray>=0.19.5", "pillow>=10.0"]`.
- [ ] Step 5: Run `uv run pytest tests/unit/test_cli.py -q`; expect pass.

### Task 4: Verification and OpenSpec Task Sync

**Files:**
- Modify: `openspec/changes/add-windows-tray-runtime-control/tasks.md`

- [ ] Step 1: Run `uv run pytest tests/unit/test_windows_startup.py tests/unit/test_tray.py tests/unit/test_cli.py -q`; expect pass.
- [ ] Step 2: Run `uv run ruff check app/cli.py app/tray.py app/windows_startup.py tests/unit/test_windows_startup.py tests/unit/test_tray.py tests/unit/test_cli.py`; expect pass.
- [ ] Step 3: Run `uv run openspec validate add-windows-tray-runtime-control --strict` if OpenSpec CLI is installed; otherwise record the blocker.
- [ ] Step 4: Mark completed OpenSpec tasks in `openspec/changes/add-windows-tray-runtime-control/tasks.md`.
