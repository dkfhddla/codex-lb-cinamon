# Tray Usage and Active Requests Context

## Purpose

This change turns the Windows tray from a lifecycle-only control into a compact local operations surface. The target user wants to answer: "Which account and model is Codex using right now, and how much of the 5-hour window is already consumed?"

## Decisions

- Use an in-memory active request registry for the first implementation. The tray runtime is already local and single-server oriented, so persistence would add migration and cleanup complexity without improving the main workflow.
- Treat active request data as volatile runtime state. If the server restarts, active requests disappear with the process.
- Compute used percentage as `100 - remaining_percent` from the existing usage window data.
- Use the highest-used account as the overall tooltip basis for both 5-hour usage percentage and reset countdown, because that is the account most likely to require operator attention.

## Alternatives Considered

- Persisting active requests in a database table would support crash recovery and multi-process views, but it requires migrations and stale-row cleanup. That is better reserved for a future multi-worker/runtime observability change.
- Reusing request logs with an `in_progress` status would avoid a new runtime registry, but request logs are currently completion records. Turning them into live state would blur their role and require update semantics.
- Showing only the latest completed request is cheaper, but it does not answer the real question: what is running right now?

## Failure Modes

- If the server is stopped, the tray continues to show stopped lifecycle state and omits usage/active request details.
- If usage status cannot be loaded, the tray shows `usage unavailable` and keeps lifecycle menu actions usable.
- If an active request cleanup path is missed, registry entries expire by TTL so stale "running" rows do not remain indefinitely.
- If multiple requests are active, the tray shows a bounded list and a remainder count.

## Example Tray Copy

```text
codex-lb running
5h usage 71% · next reset 54m
active: acc-1 · gpt-5.4 · high · 42s
```

```text
5h usage by account
acc-1  28% · 1h 42m · gpt-5.4 high running
acc-2  71% · 54m · idle
acc-3  12% · 3h 10m · idle
```
