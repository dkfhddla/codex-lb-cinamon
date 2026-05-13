# add-macos-menubar-runtime-control

## Summary

Allow the macOS menu bar app to manage the tracked background API server lifecycle from the same UI.

## Motivation

Operators currently need to start the API server and the macOS menu bar app separately. The menu bar app should be able to start, stop, and report the tracked background server using the same PID and log metadata as the CLI lifecycle commands.

## Scope

- Add managed-server options to the `menubar` CLI command.
- Reuse existing background runtime helpers for server start, status, and shutdown.
- Add macOS menu bar actions for server start, stop, status refresh, dashboard open, and log open.
- Show a stopped server state without repeatedly polling unavailable dashboard endpoints.

## Out of Scope

- Packaging a `.app` bundle.
- Adding a macOS LaunchAgent or login item registration.
- Managing unrelated server processes that are not tracked by the PID file.
