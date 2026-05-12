# Change: Fix Pro Lite quota capacity

## Summary

Add explicit Pro Lite plan normalization and quota capacity handling so dashboard Remaining donuts and account quota rows use the same non-zero plan capacity.

## Problem

ChatGPT Pro Lite accounts can arrive with plan labels such as `prolite`. The account card can still show remaining percentages from usage snapshots, but dashboard usage donuts compute absolute remaining credits from plan capacity. Because Pro Lite is not currently recognized as an account plan, its capacity resolves to `None`, which becomes `0` in the donut payload.

## Scope

- Normalize Pro Lite aliases to a canonical account plan.
- Add primary and secondary capacity values for Pro Lite.
- Cover the behavior with unit tests.

## Out of Scope

- Changing upstream usage refresh behavior.
- Changing free-plan weekly-only handling.
- Reworking dashboard visual layout.
