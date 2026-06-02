---
id: T4
title: Operation history + .touch document + folder workspace
status: in_progress
started: 2026-06-01
finished: null
min_goal_met: null
max_goal_met: null
blocker: null
depends_on: [T3]
---

# Phase T4 — Operation history + `.touch` document + folder workspace

> *Re-scoped 2026-06-01 (blocker `2026-06-01-folder-workspace-explorer`, revised
> via a 5-pass critic panel). Single-document persistence shipped (Days 1–9);
> the explorer is now widened to a VS-Code-style **folder workspace** —
> **backend owns the filesystem, frontend owns the interaction** (ADR-0010). One
> part open at a time; editor tabs are T4b.*

- **Goal:** The document *is* the operation history; persist parts in a
  VS-Code-style **folder workspace** (Open Folder → tree mirrored 1:1), with
  undo/redo from history — refresh-proof.

## Depends on

- **T3 done**; single-doc persistence foundation (Days 1–9 below) done.
- **ADR-0006** (`.touch`), **ADR-0008** (append-only history), **ADR-0010**
  (workspace / file ownership), `02-data-model.md` (Workspace, Part).
- **Requirements** F8, F9, F10, F18, F23, F32, F33, F34, N7, N8, N13.

## Minimum deliverable

- **Single-doc persistence (done):** `.touch` save/load + migration, undo/redo,
  `document` snapshots, doc-store mirror.
- **Folder workspace:** **File → Open Folder** → the Explorer mirrors the folder
  **1:1** (backend-owned tree, lazy; ADR-0010); create / open / rename / delete
  `.touch` parts; one part open at a time.
- **Shell:** the **menu bar** (File/Edit/View/Help) + the **activity rail**
  (Explorer real; Search/Git/Extensions inert stubs; Settings pinned), VS-Code
  style, hand-rolled tree + Codicons.
- **Create-from-scratch:** a no-selection prompt → a primary (box/cylinder/sphere).

## Maximum deliverable

Hand-rolled-tree polish (drag/keyboard niceties); the content-addressed rebuild
cache shipped; viewport feedback per undo step; tree delete / recent-parts.

## Sprint / day breakdown

**✅ Done — single-document foundation (Days 1–9, committed):** protocol base
(+`newDoc`/`open`/`save`/`listFiles`/`undo`/`redo`/`fileList`/`document`);
`document` save/load + migration; `session` lifecycle + undo/redo + snapshots
(path-sanitized); FE doc-store mirror, the *flat* explorer (to be replaced),
undo/redo shortcuts, save UX, create-from-scratch, busy/error. *Note: the flat
backend `listFiles`/`open`/`save` stay as the non-FSA fallback (ADR-0010).*

**Remaining — folder workspace:**

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| W1 | Protocol + backend workspace ops: `openFolder` (set root) + `listDir` (lazy folder tree) + part `open`/`save`/`new`/`rename`/`remove` by **workspace-relative path** (sanitized, contained to the root); `make codegen`. | workspace messages + BE handlers. | Server test: open a folder → tree listed; open a part by path → rebuild + snapshot; create/rename/remove reflected; `../`/absolute rejected. |
| W2 | Backend refactor: `Session` keys documents by id (per-doc undo/redo + dirty; one active today) + a **content-addressed rebuild cache** (history-prefix hash → STEP/mesh). | multi-doc-ready session + cache. | Tests: per-doc undo state isolated; a repeated history rebuild is served from cache (no re-exec). |
| W3 | FE `web/platform` `pickFolder()`: Electron native open-directory dialog (stub) + browser-dev host-folder pick (path entry). | folder picker seam. | Picking yields a workspace root that `openFolder` sends to the BE. |
| W4 | FE `web/workspace` store: `openFolder` → lazily-loaded tree + active-part id; file commands over the WS; multi-doc-ready (keyed by id). | workspace store. | Opening a folder populates the tree from the BE; opening a part loads its geometry. |
| W5 | FE **hand-rolled folder tree** + Codicons (replaces the flat list): nested collapsible rows, click-open, new/rename/delete, active highlight, dirty dot. | `web/file-tree`. | The Explorer mirrors the folder 1:1; create/open/rename a part via the tree. |
| W6 | FE menu bar dropdowns (File/Edit/View/Help → Open Folder, New Part, Save, Undo/Redo, Settings) + activity-rail stubs (Search/Git/Extensions inert). | shell chrome. | Menus invoke the actions; the rail shows the (inert) stub icons + Explorer/Settings. |
| W7 | Wire + **exit verification (live):** Open Folder → create a cube + chamfer part → it appears 1:1 in the Explorer → refresh → reopen → identical; undo→empty→redo. | verified workspace. | The exit criteria below hold live in a browser tab. |
| W8 (Max) | Rebuild-cache wins visible (instant re-open); viewport feedback per undo; tree delete / recent-parts. | polish. | Re-opening a part is instant; undo visibly steps; (optional) delete + recent shipped. |

## Exit criteria

- **File → Open Folder** → create a cube + chamfer part inside it → the Explorer
  shows the folder **1:1** → refresh/close → reopen the folder → **identical**
  model.
- **Undo** back to empty → **Redo** to the full model → unchanged.
- The `.touch` file is human-readable JSON carrying `schema_version` (N7).

## Known risks for this phase

- **R1 — still a large phase.** Foundation is done; the remaining 7 days span
  protocol/back-end folder ops, a session refactor, and a real FE explorer +
  shell. Editor tabs were split out to T4b to contain it.
- **R2 — multi-doc-ready refactor (W2) touches working undo/redo.** Keying
  `Session` documents by id risks regressing the green single-doc path.
  **Mitigation:** keep the existing tests green; "one active document" is the
  only live case until T4b.
- **R3 — workspace path security.** Part paths are workspace-relative and must
  stay contained to the opened root (reject `..`/absolute/escape). **Mitigation:**
  resolve + containment check against the root; rejection tests.
- **R4 — browser-dev folder pick is by-path** (no native dialog in a tab; FSA
  laptop-folder is the deferred nicety, ADR-0010). **Mitigation:** a simple
  path-entry/host-folder pick now; Electron native dialog later.
- **R5 — rebuild cache correctness.** The cache key must be the exact op-history
  prefix (params + selection) or stale geometry leaks. **Mitigation:** hash the
  canonical emitted source / history JSON; test a cache hit equals a fresh build.
- **R6 — explorer fidelity vs effort.** Match VS-Code/Cursor *familiarity* (tree,
  open, new/rename, active highlight) with the hand-rolled tree — not pixel-perfect.
