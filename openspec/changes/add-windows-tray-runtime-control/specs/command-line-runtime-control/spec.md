# command-line-runtime-control Specification

## ADDED Requirements

### Requirement: CLI can launch a Windows tray runtime controller

The CLI MUST provide a `tray` subcommand that launches a Windows system tray controller for the tracked background server lifecycle. On non-Windows platforms, the command MUST fail fast with a clear message that tray mode is only supported on Windows.

#### Scenario: Operator launches tray mode on Windows

- **WHEN** the operator runs `codex-lb-cinamon tray` on Windows
- **THEN** the CLI starts a system tray controller process in the current Python environment
- **AND** the tray controller exposes menu actions for server start, server stop, status refresh, dashboard open, log open, startup registration toggle, and tray exit

#### Scenario: Operator launches tray mode on an unsupported platform

- **WHEN** the operator runs `codex-lb-cinamon tray` on a non-Windows platform
- **THEN** the CLI exits with a clear unsupported-platform message
- **AND** it does not attempt to import Windows-only tray dependencies

### Requirement: Windows tray controller uses tracked runtime metadata

The tray controller MUST use the same tracked runtime metadata and lifecycle helpers as `start`, `status`, and `shutdown`. It MUST NOT discover or terminate unrelated processes by name.

#### Scenario: Tray starts the server

- **WHEN** the operator selects `Start server` from the tray menu
- **AND** the tracked PID file does not point to a running server
- **THEN** the tray controller starts the server through the existing background lifecycle helper
- **AND** it refreshes the tray status after startup completes or fails

#### Scenario: Tray stops the server

- **WHEN** the operator selects `Stop server` from the tray menu
- **AND** the tracked PID file points to a running server
- **THEN** the tray controller stops that tracked server through the existing shutdown helper
- **AND** it refreshes the tray status after shutdown completes or fails

#### Scenario: Tray reports stale metadata as stopped

- **WHEN** the tray controller refreshes status
- **AND** the tracked PID file points to a process that no longer exists
- **THEN** it uses the existing metadata loader cleanup behavior
- **AND** displays the server as stopped instead of running

### Requirement: Windows startup registration is current-user scoped

The tray controller MUST support enabling and disabling launch-at-login for the current Windows user. Registration MUST use the current-user startup mechanism and MUST NOT require administrator privileges.

#### Scenario: Operator enables startup registration

- **WHEN** the operator enables the tray startup menu item
- **THEN** the application records a current-user startup entry that launches `codex-lb-cinamon tray` using the current Python executable/module environment
- **AND** a later status check reports startup registration as enabled

#### Scenario: Operator disables startup registration

- **WHEN** the operator disables the tray startup menu item
- **THEN** the application removes its current-user startup entry if present
- **AND** a later status check reports startup registration as disabled
