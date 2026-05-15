# add-menubar-provider-sync-action

## Summary

Add a macOS menu bar action that runs `codex-provider sync` without requiring the operator to open a terminal.

## Motivation

Operators already use the macOS menu bar app for local runtime controls. Provider metadata sync is another common local operational action, and putting it in the same menu reduces context switching.

## Scope

- Add a `Sync Providers` action to the macOS menu bar menu.
- Run `codex-provider sync` in a background thread so the menu bar UI remains responsive.
- Show basic provider sync status and surface failures in the menu.

## Out of Scope

- Building provider sync into the API server.
- Adding cross-platform tray integrations.
