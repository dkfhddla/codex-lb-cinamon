## ADDED Requirements

### Requirement: Menu bar launch command
The CLI SHALL include a command for launching the macOS menu bar status app.

#### Scenario: Launch menu bar app
- **WHEN** a user runs the menu bar launch command on macOS
- **THEN** the process creates a native menu bar status item and refreshes its dashboard summary periodically

#### Scenario: Configure API connection
- **WHEN** a user passes a base URL, refresh interval, or dashboard session cookie
- **THEN** the menu bar app uses those values when polling the dashboard APIs
