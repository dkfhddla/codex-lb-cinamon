# add-macos-menu-bar-status

## Summary

Add a macOS menu bar status app that shows primary 5h usage as `5h N%` and exposes basic dashboard information from its menu.

## Motivation

Operators should be able to glance at the primary 5h usage limit without opening the browser dashboard. The status app should reuse the running codex-lb-cinamon API so the value matches the dashboard.

## Scope

- Add a CLI subcommand to launch the menu bar app on macOS.
- Poll existing dashboard overview/settings APIs and format a menu bar title.
- Show basic system information in the menu: 5h/7d usage, last sync, routing, version, account counts, request/tokens/cost/error metrics.
- Support an optional dashboard session cookie for password-protected dashboards.

## Out of Scope

- Packaging a `.app` bundle or launch agent.
- Adding a new backend API endpoint.
- Supporting native menu bar integrations on Windows/Linux.
