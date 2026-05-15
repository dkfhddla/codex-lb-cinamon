## ADDED Requirements

### Requirement: macOS menu bar provider sync action
The macOS menu bar app SHALL expose an action for running `codex-provider sync` from the menu.

#### Scenario: Run provider sync from menu bar
- **WHEN** a user selects `Sync Providers` from the macOS menu bar app
- **THEN** the app runs `codex-provider sync` in the background
- **AND** the menu remains responsive while the sync is running

#### Scenario: Report provider sync result
- **WHEN** the provider sync command completes or fails
- **THEN** the menu shows whether the last provider sync succeeded or failed
- **AND** failure details are visible from the menu when available
