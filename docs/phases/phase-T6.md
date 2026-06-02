---
id: T6
title: Settings + dual provider modes (Anthropic API + Claude Code)
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T4b]
---

# Phase T6 — Settings + dual provider modes

- **Goal:** The user can paste an API key OR pick Claude Code; the credential is secured properly per N9.
- **Min:** Settings panel; provider-mode picker (Anthropic API / Claude Code); API-key paste → OS keychain via `keyring` (no plaintext on disk); Claude Code mode auto-detects local Claude Code install + auth status and hides the option when unavailable; the active `LLMClient` is selected per Settings at session start.
- **Max:** A "test connection" button per mode; cost-per-mode preview before committing; "clear key" wipes the keychain entry.
- **Exit criterion:** change provider in Settings → next prompt routes through the chosen client; an API-key set+clear cycle leaves no plaintext on disk (filesystem grep + git-history scan clean).

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
