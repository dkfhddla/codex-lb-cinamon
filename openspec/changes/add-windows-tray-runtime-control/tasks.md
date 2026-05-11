## 1. Specs

- [x] 1.1 Add an OpenSpec delta for Windows tray runtime control.

## 2. Implementation

- [x] 2.1 Add Windows startup registration helpers for current-user Run key lifecycle.
- [x] 2.2 Add a tray application module that manages existing background server lifecycle APIs.
- [x] 2.3 Add a `tray` CLI subcommand that launches the tray app and fails clearly on unsupported platforms.
- [x] 2.4 Add optional package dependencies for tray support.

## 3. Verification

- [x] 3.1 Add unit tests for startup registration helpers.
- [x] 3.2 Add unit tests for tray CLI dispatch and unsupported-platform behavior.
- [x] 3.3 Run targeted tests and OpenSpec validation.
  - Targeted tests: `py -3.13 -m pytest tests/unit/test_windows_startup.py tests/unit/test_tray.py tests/unit/test_cli.py -q` passed.
  - Lint: `py -3.13 -m ruff check app/cli.py app/tray.py app/windows_startup.py tests/unit/test_windows_startup.py tests/unit/test_tray.py tests/unit/test_cli.py` passed.
  - OpenSpec validation blocked because `openspec` is not available on PATH in this environment.
