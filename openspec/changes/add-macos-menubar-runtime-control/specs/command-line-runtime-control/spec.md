## ADDED Requirements

### Requirement: macOS menu bar can manage the tracked runtime

The macOS menu bar command MUST support an optional managed-server mode that uses the same tracked runtime metadata and lifecycle helpers as `start`, `status`, and `shutdown`. The menu bar controller MUST NOT discover or terminate unrelated processes by name.

#### Scenario: Menu bar starts the tracked server on demand

- **WHEN** the operator runs `codex-lb-cinamon menubar --manage-server`
- **AND** the tracked PID file does not point to a running server
- **THEN** the menu bar app exposes a start action that launches the server through the existing background lifecycle helper
- **AND** refreshes the displayed status after startup completes or fails

#### Scenario: Menu bar starts the tracked server on launch

- **WHEN** the operator runs `codex-lb-cinamon menubar --manage-server --start-on-launch`
- **AND** the tracked PID file does not point to a running server
- **THEN** the menu bar app attempts to launch the server through the existing background lifecycle helper before its first dashboard refresh
- **AND** reports startup failures in the menu instead of exiting the menu bar app

#### Scenario: Menu bar stops the tracked server

- **WHEN** the operator selects the stop action from the managed menu bar app
- **AND** the tracked PID file points to a running server
- **THEN** the menu bar app stops that tracked server through the existing shutdown helper
- **AND** refreshes the displayed status after shutdown completes or fails

#### Scenario: Menu bar opens the tracked dashboard route

- **WHEN** managed-server mode is enabled
- **AND** the operator selects the dashboard open action from the menu bar app
- **THEN** the menu bar app opens the dashboard SPA route for the tracked server URL

#### Scenario: Menu bar reports stopped state without dashboard polling

- **WHEN** managed-server mode is enabled
- **AND** no tracked server is running
- **THEN** the menu bar title reports the stopped state
- **AND** the menu shows status, dashboard URL, and log path without requiring dashboard API calls
