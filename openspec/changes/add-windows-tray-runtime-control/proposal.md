## Why

Windows local operators currently have to start, stop, and inspect `codex-lb-cinamon` from a terminal. The CLI already supports tracked background runtime control, but it does not provide the tray-style workflow that Windows users expect for long-lived local services.

## What Changes

- Add a Windows tray entrypoint that can manage the existing tracked background server lifecycle.
- Add tray menu actions for start, stop, status refresh, dashboard, log file, Windows startup registration, and tray exit.
- Add current-user Windows startup registration helpers so the tray app can opt into launch-at-login without requiring administrator privileges.
- Keep non-Windows behavior explicit by failing fast with a clear message when tray mode is unavailable.
- Add package metadata for the tray optional dependency group.

## Impact

- Code: `app/cli.py`, new tray runtime helper modules under `app/`.
- Tests: unit coverage for tray availability, startup registration command construction, and CLI dispatch.
- Specs: extend `command-line-runtime-control` with Windows tray runtime control.

## Capabilities

### Changed Capabilities

- `command-line-runtime-control`
