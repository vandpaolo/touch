---
id: T4
title: Operation history + .touch document
status: blocked
started: 2026-06-01
finished: null
min_goal_met: null
max_goal_met: null
blocker: blockers/2026-06-01-folder-workspace-explorer.md
depends_on: [T3]
---

# Phase T4 — Operation history + .touch document

- **Goal:** The document *is* the operation history. Persist it as a `.touch`
  file, browse/open via a VS-Code/Cursor-style explorer, and undo/redo by
  stepping the history — so geometry survives a refresh/restart (the source of
  truth is the saved op history, not in-memory state).

## Depends on

- **T3 done** — the click→prompt→op→mesh round-trip; `session._handle_plan`
  appends ops; `_rebuild_mesh` replays the history.
- **ADR-0006** (`.touch` format) + **ADR-0008** (append-only history) +
  **02-data-model.md** (TouchDocument fields).
- **Architecture/classes** — BE `document`; FE `doc-store`, `file-tree`,
  `history-ui`; the activity-bar Explorer + sidebar (stubbed in T2).
- **Requirements** F8, F9, F10, F23, N7, N8 (recovery *foundation*; the
  supervisor itself is T8).
- The `out_root` project dir (`/srv/touch/` on the dev host).

## Minimum deliverable

- **Backend `document`**: full `TouchDocument` (schema_version, name,
  description, parameters, history, created/modified, touch_version);
  `save(path)` → canonical human-readable JSON; `load(path)` → validate +
  a minimal `schema_version` migration helper (N7).
- **Protocol**: new messages — `newDoc` / `open` / `save` / `listFiles` /
  `undo` / `redo` (FE→BE), `fileList` + a `document` history-snapshot (BE→FE);
  `make codegen` regenerates TS + pydantic.
- **Backend `session`**: handle new/open/save/listFiles (file I/O under
  `out_root`, **filenames sanitized** — no path traversal); undo pops + replays
  + emits the new mesh, redo re-applies; every history change emits a `document`
  snapshot.
- **FE**: `doc-store` mirrors history + dirty from the snapshot; a
  **VS-Code/Cursor-style file explorer** (list / open-on-click / new / rename,
  active-file highlight) in the Explorer sidebar; **undo/redo** via keyboard
  (Ctrl+Z / Ctrl+Shift+Z) + menu; **create-from-scratch** (a prompt with *no*
  selection → a primary box/cylinder/sphere — the skipped T3 Max, now required);
  save / save-as + a dirty indicator.
- A new session keeps the **demo cube as the default canvas** (decided);
  **New** creates an empty document and create-from-scratch seeds it
  (`demo_mesh` stays on by default).

## Maximum deliverable

Also: viewport feedback at each undo step; replay-from-history positioned as the
crash-recovery path (foreshadowing T8); delete in the tree; recent-files.

## Sprint / day breakdown

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 1 | Protocol: add `newDoc`/`open`/`save`/`listFiles`/`undo`/`redo` + `fileList`/`document` snapshot to `schema.json`; `make codegen`. | extended protocol. | `make codegen` regenerates TS + pydantic clean (no drift); both import. |
| 2 | Backend `document` save/load: full fields; `save(path)` canonical JSON; `load(path)` + `schema_version` migration helper. | `document.save/load`. | Round-trip: build history → save → load → identical; a `schema_version`-bumped fixture migrates; tests. |
| 3 | Backend `session` new/open/save/listFiles under `out_root`, **filename sanitized**. | doc lifecycle handlers. | Server test: save → `listFiles` shows it; open → rebuild + mesh + snapshot; a `../` filename is rejected. |
| 4 | Backend `session` undo/redo: pop/re-apply history → rebuild → mesh + snapshot; redo stack cleared on a new op. | undo/redo handlers. | Server test: op → undo → prior mesh + shorter history; redo → restored; new op clears redo. |
| 5 | FE `doc-store`: consume the `document` snapshot (history, name, dirty); expose to file-tree/history-ui. | doc-store mirror. | A snapshot updates doc-store; subscribers see history length + dirty + name; Vitest. |
| 6 | FE create-from-scratch: a no-selection prompt entry (empty-canvas click / "+" / shortcut) → primary op (box/cylinder/sphere). | primary-create path. | On an empty doc, "a 40 mm cube" (no face click) builds + renders a cube. |
| 7 | FE file explorer (VS-Code/Cursor style): list `.touch` under the project root, single-click open, new, rename; active-file highlight. | `web/file-tree`. | Tree lists files; click opens (geometry loads); new → empty doc; rename persists. |
| 8 | FE undo/redo controls: Ctrl+Z / Ctrl+Shift+Z + Edit menu → `undo`/`redo`; viewport updates. | history-ui / shortcuts. | Undo/redo via keyboard + menu step the model both ways. |
| 9 | FE save UX: Save / Save As (name), dirty indicator (title/tab dot); cleared on save, set on edit. | save UX. | Save writes the file; the dirty dot tracks edits/saves. |
| 10 | Wire + exit verification (live): cube + chamfer → save → reopen → identical; undo→empty→redo. | verified round-trip. | The exit criteria below hold live in a browser tab. |
| 11 (Max) | Viewport feedback per undo step; replay-as-recovery foreshadow; tree delete / recent files. | polish. | Each undo visibly steps geometry; (optional) delete + recent shipped. |

## Exit criteria

- Model a cube + chamfer in a browser tab → **Save** → close/refresh → **Open**
  the `.touch` → **identical** model (refresh-proof).
- **Undo** back to empty → **Redo** to the full model → unchanged.
- The `.touch` file is human-readable JSON carrying `schema_version` (N7); a
  small edit diffs cleanly in git.

## Known risks for this phase

- **R1 — big phase (~11 days, at the cap).** Protocol extension + BE file I/O +
  undo/redo + a real FE explorer + the create-from-scratch path. **Mitigation:**
  tight Min, trimmed Max. (Push-back: split into T4a document/undo + T4b
  explorer if it over-runs.)
- **R2 — T4's exit needs the no-selection primary path** (the skipped T3 Max).
  **Folded into Day 6** as required scope — the planner/adapter already handle a
  None selection; the gap is the FE entry to prompt without a face click.
- **R3 — file-I/O security.** Save/open take a user-supplied name; must be
  sanitized to the `out_root` project dir (reject `..`/absolute paths — no
  traversal; CLAUDE.md boundary rule). **Mitigation:** resolve + containment
  check; a rejection test.
- **R4 — demo cube stays the default canvas (decided).** The connect-time demo
  cube remains the default starting point; **New** gives an empty doc. Undo-to-
  empty still works (the demo cube is op[0] — undo pops chamfer→box→empty, redo
  restores). `make up` keeps `demo_mesh` on. Watch: "open a file" must *replace*
  the demo document cleanly, not merge.
- **R5 — protocol churn.** Both ends regenerate; a codegen-drift guard + contract
  tests keep them honest.
- **R6 — undo cost.** Each undo replays the whole history (OCP rebuild per step);
  fine for v0 histories, a caching concern later. Note, don't optimize now.
- **R7 — explorer fidelity vs effort.** Match VS Code/Cursor *familiarity*
  (tree, open, new, rename, active highlight) — not pixel-perfect chrome.
