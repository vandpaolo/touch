---
id: T13
title: Auto-update + signed CI build
status: planned
started: null
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T12]
---

# Phase T13 — Auto-update + signed CI build

- **Goal:** Promote F27 to **must**. GitHub Actions tags-and-uploads; the `.exe` is code-signed; the app checks for updates and notifies.
- **Min:** Tagged push → signed `Touch-vX.Y.Z-setup.exe` on the Release page; auto-update notification in-app on launch.
- **Max:** Background download + apply-on-restart.
- **Exit criterion:** a friend's running install detects + applies a new release without re-downloading manually.

## Sprint / day breakdown
<!-- Filled by /pm-phase-plan when this phase is next to start. -->

## Known risks for this phase
<!-- Filled by /pm-phase-plan. -->
