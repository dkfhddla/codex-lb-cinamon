## Why

Windows tray operators need a quick way to see whether the local proxy is actively serving Codex traffic, which account/model is currently in use, and how close the 5-hour usage window is to reset. Today the tray can start, stop, and inspect runtime state, but operators must open the dashboard or inspect logs to answer those questions.

## What Changes

- Add a lightweight in-memory active request registry for proxied requests after routing selection.
- Expose a read-only local runtime status endpoint that reports active request summaries and 5-hour usage window state.
- Extend the Windows tray tooltip and menu to show:
  - overall 5-hour used percentage,
  - time until the next usage reset,
  - account-level 5-hour used percentage/reset/active status,
  - currently running account/model/reasoning-effort summaries.
- Keep unavailable usage or active-request data non-fatal so existing tray lifecycle controls continue to work.

## Impact

- Code: request handling instrumentation, runtime status API/service, tray status polling and formatting.
- Tests: unit coverage for active request lifecycle, status formatting, and tray summary behavior; API coverage for runtime status response.
- Specs: extend `proxy-runtime-observability` and `command-line-runtime-control`.

## Capabilities

### Changed Capabilities

- `proxy-runtime-observability`
- `command-line-runtime-control`
