# proxy-runtime-observability Specification

## ADDED Requirements

### Requirement: Runtime exposes active proxy request summaries

The system SHALL maintain a bounded in-memory view of currently active proxied requests after routing selection. Each active request summary MUST include the proxy request id, selected provider kind, routing-subject identifier when available, account identifier when available, requested model, reasoning effort when available, transport or route class when available, and request start time.

#### Scenario: Request appears while upstream work is active

- **WHEN** a proxied request has selected an upstream routing subject
- **AND** the upstream request has not completed, failed, or been cancelled
- **THEN** the runtime active request snapshot includes that request summary

#### Scenario: Request is removed after completion

- **WHEN** a proxied request completes, fails, or is cancelled
- **THEN** the runtime removes that request from the active request snapshot

#### Scenario: Stale active request is cleaned up

- **WHEN** an active request entry exceeds the configured stale-entry TTL
- **THEN** the runtime excludes it from active request snapshots

### Requirement: Runtime status includes 5-hour usage and active requests

The system SHALL provide a read-only local runtime status API that reports active request summaries and account-level 5-hour usage window state. The 5-hour usage state MUST report used percentage, reset time when available, and time-to-reset suitable for operator display.

#### Scenario: Runtime status has usage and active requests

- **WHEN** the local runtime status API is requested while the server is running
- **THEN** the response includes active request summaries
- **AND** it includes account-level 5-hour usage rows
- **AND** the overall usage summary is based on the highest-used account

#### Scenario: Usage data is unavailable

- **WHEN** active request data is available but 5-hour usage data cannot be loaded
- **THEN** the runtime status API still returns active request summaries
- **AND** it marks usage data as unavailable without failing the whole response
