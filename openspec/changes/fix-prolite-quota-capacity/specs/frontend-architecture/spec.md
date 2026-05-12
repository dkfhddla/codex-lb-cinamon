## ADDED Requirements

### Requirement: Dashboard quota capacity recognizes Pro Lite accounts

Dashboard quota capacity calculations SHALL recognize Pro Lite ChatGPT account plan labels and MUST NOT report zero remaining credits solely because the account plan is labeled `prolite` or `pro_lite`.

#### Scenario: Pro Lite account contributes to Remaining donuts

- **WHEN** a ChatGPT account has plan type `prolite` or `pro_lite`
- **AND** its persisted usage snapshot has remaining quota
- **THEN** dashboard Remaining donut payloads include non-zero capacity and remaining credits for that account
