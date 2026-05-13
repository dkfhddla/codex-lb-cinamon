## Why

Dashboard Remaining donuts derive account capacity from stored ChatGPT plan labels. Newer upstream plan labels such as `prolite` can currently normalize to an unknown plan, causing accounts with real remaining quota to show zero remaining credits.

## What Changes

- Recognize current ChatGPT/Codex plan labels and common aliases, including Go, Pro Lite, Pro 100, Pro 200, and education labels.
- Align fixed Codex capacity calculations with the current Plus, Pro Lite, and Pro multiplier model.
- Keep Go recognized as a plan without inventing a fixed Codex capacity because official fixed credit values are not published.

## Impact

- Pro Lite accounts contribute non-zero capacity to dashboard Remaining donuts.
- Pro $200 accounts use the current 20x Plus capacity.
- Business, Team, Edu, and Enterprise fixed-capacity fallbacks remain conservative at the Plus baseline when no flexible-credit data is available.
