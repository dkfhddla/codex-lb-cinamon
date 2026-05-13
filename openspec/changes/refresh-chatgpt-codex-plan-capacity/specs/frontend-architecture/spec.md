## ADDED Requirements

### Requirement: Dashboard quota capacity recognizes current ChatGPT/Codex plans

Dashboard quota capacity calculations SHALL recognize current ChatGPT/Codex plan labels and aliases used by upstream account payloads. The dashboard MUST NOT report zero remaining credits solely because a supported paid plan label is represented as `prolite`, `pro_lite`, `pro100`, or another supported alias.

#### Scenario: Pro Lite account contributes to Remaining donuts during the Codex promo

- **WHEN** a ChatGPT account has plan type `prolite`, `pro_lite`, `pro100`, `pro-100`, or `pro 100`
- **AND** the capacity calculation date is on or before 2026-05-31
- **AND** its persisted usage snapshot has remaining quota
- **THEN** dashboard Remaining donut payloads calculate Pro Lite capacity using 10x the Plus Codex baseline

#### Scenario: Pro Lite account uses standard capacity after the promo

- **WHEN** a ChatGPT account has a supported Pro Lite plan alias
- **AND** the capacity calculation date is on or after 2026-06-01
- **THEN** dashboard Remaining donut payloads calculate Pro Lite capacity using 5x the Plus Codex baseline

#### Scenario: Go account is recognized without invented capacity

- **WHEN** a ChatGPT account has plan type `go`
- **THEN** the system recognizes the account plan label
- **AND** it does not assign a fixed Codex capacity unless an authoritative fixed capacity is available
