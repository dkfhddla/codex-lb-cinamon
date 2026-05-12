# command-line-runtime-control Specification

## ADDED Requirements

### Requirement: Windows tray displays 5-hour usage and active requests

The Windows tray controller SHALL display the local server lifecycle status together with 5-hour usage percentage, next reset countdown, and currently active request summaries when the tracked background server is running.

#### Scenario: Tray tooltip displays usage and active request

- **WHEN** the tracked background server is running
- **AND** runtime status polling returns 5-hour usage and at least one active request
- **THEN** the tray tooltip includes the overall 5-hour used percentage
- **AND** it includes the next reset countdown for the highest-used account
- **AND** it includes the leading active request's account or routing-subject identifier, model, reasoning effort when available, and elapsed runtime

#### Scenario: Tray menu displays account-level usage

- **WHEN** runtime status polling returns account-level 5-hour usage rows
- **THEN** the tray menu includes a bounded account usage section
- **AND** each row includes used percentage, reset countdown when available, and either `idle` or a currently running model summary for that account

#### Scenario: Tray remains useful when usage polling fails

- **WHEN** the tracked background server is running
- **AND** runtime status polling fails or returns usage unavailable
- **THEN** the tray continues to show lifecycle status and lifecycle actions
- **AND** it displays a concise unavailable usage message instead of failing the tray app

#### Scenario: Tray summarizes multiple active requests

- **WHEN** more active requests exist than the tray menu display limit
- **THEN** the tray menu shows the first active request summaries
- **AND** it includes a remainder count for the additional active requests
