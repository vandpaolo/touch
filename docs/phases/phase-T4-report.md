---
phase: T4
status: done
min_met: true
max_met: false
duration_planned_days: 8
duration_actual_days: 2
---

# Phase T4 report — Operation history + `.touch` document + folder workspace

> Duration counts the folder-workspace re-scope (W1–W8, 2026-06-01 → -02). The
> single-document persistence foundation (plan Days 1–9) shipped earlier in the
> phase, before the mid-phase re-scope.

## What shipped

**Single-document foundation (plan Days 1–9) — done, committed earlier**
(`652a229`, `a03d720`, `8b80d37`): protocol extension; `.touch` save/load +
migration (`schema_version`, N7); `Session` document lifecycle + undo/redo +
`document` snapshots (path-sanitized); FE doc-store mirror, undo/redo shortcuts,
save UX, create-from-scratch, busy/error toast.

**Folder workspace (W1–W8) — done:**

| Task | Status | Artefact |
|------|--------|----------|
| W1 — protocol + backend workspace ops (`openFolder`/`listDir` + part open/save/new/rename/remove by sanitised workspace-relative path) | done | `6173a46`; [session.py](../../src/touch_backend/session.py), `protocol/schema.json` |
| W2 — content-addressed rebuild cache | done (cache half) | [mesh_cache.py](../../src/touch_backend/mesh_cache.py); the multi-doc-by-id refactor deferred to T4b |
| W3 — FE `platform.pickFolder()` seam | done | [platform/index.ts](../../web/src/platform/index.ts) (browser-dev path entry; Electron native dialog still stubbed) |
| W4 — FE `web/workspace` store (lazy tree, active part, WS file commands) | done | [workspace/index.ts](../../web/src/workspace/index.ts) |
| W5 — hand-rolled folder tree + Codicons (replaces flat list) | done | [file-tree/FileTree.tsx](../../web/src/file-tree/FileTree.tsx) |
| W6 — menu bar (File/Edit/View/Help) + activity-rail stubs | done | [MenuBar.tsx](../../web/src/app/MenuBar.tsx), [ActivityBar.tsx](../../web/src/app/ActivityBar.tsx) |
| W7 — wire + live exit verification | done | reopen-identical (history + mesh hash) + undo→empty→redo verified over the live WS |
| W8 (Max) — polish | partial | rebuild cache wins visible (instant re-open); per-undo viewport feedback / tree delete / recent-parts not done |

All work landed in `f33e634` (W3–W8) on top of `6173a46` (W1). Full CI green:
backend 238 passed + ruff/pyright/lint-imports; web 15 tests + typecheck + build.

## What slipped (and why)

- **W2 multi-document-by-id refactor** — deferred to **T4b** by design (the
  re-scope split editor tabs / multi-doc into its own phase to contain T4).
  T4 min was always "one part open at a time," so this is not a min miss. Only
  the **rebuild-cache** half of W2 shipped.
- **Max polish** (drag/keyboard tree niceties, per-undo-step viewport feedback,
  tree delete, recent-parts) — not done. Max is therefore partial; the headline
  Max item (rebuild cache) shipped.

## Surprises

- **Geometry-rebuild latency cliff.** Every undo/redo re-ran the full Executor
  subprocess (`import OCP` ~1–2 s + tessellation) → ~2.5 s per step, which made
  undo/redo feel broken. The rebuild cache (W2) was pulled forward from Max and
  turned re-visited history prefixes into ~1 ms lookups. The backend↔frontend
  file-ownership choice (ADR-0010) was confirmed **orthogonal** to this — folder
  listing is ~1 ms; the cost is OCP, which cannot move to the browser.
- **Opaque failures.** Build failures surfaced as "subprocess exited with code
  N", hiding the real cause. The executor now surfaces the exception's last line
  (e.g. `FinderError: no face contains point …`). Small change, large UX gain.
- **Face selection is brittle** (the real cause of many failed actions): the
  adapter re-resolves the clicked face from a 3D point, which breaks on
  edge/corner clicks (ambiguous) or off-surface picks (no face). Captured to
  `notes/questions.md` for the T5 finder phase (likely an ADR — carry a stable
  face identity from the FE instead of a lossy point lookup).

## Decisions taken mid-phase

- **Blocker [`2026-06-01-folder-workspace-explorer`](../blockers/2026-06-01-folder-workspace-explorer.md)**
  (resolved, `fefb8c5`): the flat backend-owned `.touch` list was re-scoped to a
  VS-Code/Cursor-style **Open-Folder workspace**. Resolved via a 5-pass critic
  panel → **ADR-0010** (backend owns the filesystem; frontend owns the
  interaction — folder picker + hand-rolled tree + WS file commands), requirements
  F10/F18/F32–F34 re-spec, roadmap re-scope, and **T4b** inserted for editor tabs.

## Recommended changes for next phase

- **T5 (finder):** replace point-based face re-resolution with a stable face
  identity carried from the FE selection; add chamfer min-params / clarify
  questions (don't silently assume a length) and a useful failure when a chamfer
  over-runs the geometry. Both already noted in `notes/questions.md`.
- **T4b (editor tabs):** complete the W2 multi-document-by-id `Session` refactor
  it was deferred into; keep the green single-doc undo/redo path intact.
- **General:** the legible-error pattern (surface the real exception) is worth
  extending to other backend failure paths.
