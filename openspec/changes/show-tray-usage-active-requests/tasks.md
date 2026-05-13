## 1. Specs

- [x] 1.1 Add OpenSpec deltas for tray usage display and active request observability.

## 2. Runtime observability

- [x] 2.1 Add an in-memory active request registry with register, complete, snapshot, and stale-entry cleanup behavior.
- [x] 2.2 Instrument proxied request handling after routing selection so active entries include request id, routing subject/account, model, reasoning effort, route/transport metadata, and start time.
- [x] 2.3 Expose a read-only local runtime status API that combines active request summaries with 5-hour usage window rows.

## 3. Windows tray display

- [x] 3.1 Add tray status polling for runtime usage/active-request data when the background server is running.
- [x] 3.2 Format the tray tooltip with overall 5-hour used percentage, next reset countdown, and the leading active request.
- [x] 3.3 Add menu rows for account-level 5-hour usage/reset and bounded active request summaries.
- [x] 3.4 Keep lifecycle controls usable when usage/status polling fails.

## 4. Verification

- [x] 4.1 Add unit tests for active request registry lifecycle and TTL cleanup.
- [x] 4.2 Add API tests for runtime status response shape and authentication expectations.
- [x] 4.3 Add tray formatting tests for usage available, active requests, idle state, and usage unavailable state.
- [x] 4.4 Run targeted tests, lint, and OpenSpec validation.
  - Targeted tests: `python -m pytest tests/unit/test_tray.py tests/unit/test_active_requests.py tests/unit/test_tray_runtime_formatting.py tests/unit/test_runtime_status_api.py tests/integration/test_runtime_status_api.py tests/integration/test_usage_api.py -q` passed with `TMP`/`TEMP` pointed at `.tray-run`.
  - Lint: `python -m ruff check ...` passed for changed app/test files.
  - Type check: `python -m ty check ...` passed for new runtime/tray modules and tests.
  - OpenSpec validation blocked because `openspec` is not available on PATH in this environment.
