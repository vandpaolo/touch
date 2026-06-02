---
id: 2026-06-01-folder-workspace-explorer
phase: T4
severity: soft
status: resolved
discovered: 2026-06-01
resolved: 2026-06-01
re_entry: both
---

# T4 blocker — the explorer should be a VS-Code "Open Folder" workspace

## What

T4 (Days 1–9) shipped working single-document persistence (`.touch` save/load,
undo/redo, history snapshots) with a **flat, backend-owned list of `.touch`
files** in `out_root` as the Explorer.

The user wants the editor-grade VS Code / Cursor model instead: **File → Open
Folder → pick a folder → the Explorer mirrors that folder 1:1** (nested files +
subfolders, collapsible tree), and you create your project files *inside* the
opened folder. The 3D viewport is unchanged — this is purely the left Explorer
panel becoming a real folder tree backed by a chosen workspace folder.

That is the **multi-file project model** ("a project is a folder of related
`.touch` files") — which the roadmap explicitly defers to **T14**. So the ask
pulls T14 forward into T4.

## Why the design did not anticipate it

Two layers under-specified it:

- **Requirements (F10/F18).** F18 says only "file-tree shows `.touch` files in
  the project root, with open/new/rename" and F10 is single-file save/open. The
  flat list met the *letter* of those but not the folder-workspace experience.
  "Project = folder" was consciously pushed to T14 — the gap is that the user
  expects T14's model now.
- **Architecture (file ownership).** T4 decided "backend owns file I/O over the
  WS" (a flat `out_root` listing). The folder-workspace flips ownership: how
  VS Code actually does it is —
  - **Desktop (Electron, our `.exe`):** native `showOpenDialog({properties:['openDirectory']})`
    → workspace root; the tree is read via Node `fs`, **lazily per directory on
    expand**, with a file watcher for live updates.
  - **Browser (vscode.dev, our `nexus/touch` tab):** the **File System Access
    API** (`showDirectoryPicker()`) → a handle to a folder **on the user's
    machine**; read/write through the handle (Chromium + HTTPS only).
  - **Mapped to Touch:** the **frontend owns the workspace folder** (FSA API in
    the browser, native dialog in Electron), reads/writes the `.touch` JSON
    locally, and streams the **op-history** to the sidecar to rebuild geometry.
    The sidecar's role narrows to "rebuild from history" — it no longer owns the
    workspace files. The `web/platform` capability shim grows to cover folder
    access across both modes.

## Re-entry point — both

- **`/pm-requirements`:** redefine F18 (and F10) as a folder-workspace explorer
  (Open Folder → 1:1 tree, create files/folders inside, active file, dirty);
  decide formally whether T14's multi-file project model is pulled forward into
  T4 or T4 is closed and a dedicated folder-workspace phase is inserted
  (a `/pm-roadmap` touch if the phase ordering changes).
- **`/pm-architecture`:** the file-ownership flip — FE-owns-folder via the File
  System Access API (browser) / Electron native dialog (desktop), lazy per-folder
  tree + watcher, the `web/platform` shim's folder surface, and the sidecar
  reduced to history→geometry rebuild. Likely a new ADR (workspace / file
  ownership), and a decision on the now-partly-superseded backend
  `save`/`open`/`listFiles` WS messages (keep as a server-folder fallback, or
  retire).

## Proposed resolution

Options on the table (user has chosen to **re-scope T4 via this blocker**):

- **A — Re-scope T4 (chosen direction):** re-open requirements + architecture for
  the folder-workspace model, then re-plan the remaining T4 days (platform
  folder-access shim, folder-tree Explorer UI, FE `.touch` read/write,
  history-stream-to-sidecar rebuild). T4 grows.
- **B — Close + new phase:** keep T4's single-doc persistence as `done`, pull T14
  forward as the next dedicated "folder workspace" phase.

Caveats to weigh in the redesign:
- The browser File System Access API is **Chromium-only over HTTPS** (no Firefox/
  Safari); the native folder dialog is **Electron-only**. The flat
  `out_root`-over-WS path may stay as a fallback for non-Chromium browser-dev.
- Most of T4's backend (document save/load, undo/redo, snapshots) is reusable;
  the change is *where the files live* and *who lists the tree*, not the
  op-history model (the document is still the op history, ADR-0008).

## Resolution

Resolved 2026-06-01. Both re-entry layers re-opened and locked:

- **`/pm-requirements`** — F18 → Explorer mirrors the opened folder 1:1 (`must`);
  added F32 (Open Folder), F33 (activity rail), F34 (menu bar), F35 (editor tabs
  → T4b), N13 (cross-mode file access).
- **`/pm-architecture` + a 5-pass critic panel** → **ADR-0010 (revised):
  backend owns the workspace filesystem, frontend owns the interaction** (folder
  picker + tree + WS file commands). The initial *frontend-owns-folder / FSA*
  draft was rejected by the panel (FSA fragility, notional dev privacy,
  three-copy split-brain, O(history) opens). Folded in: hand-rolled tree +
  Codicons (no react-arborist), state multi-doc-ready (documents keyed by id),
  content-addressed rebuild cache.
- **`/pm-roadmap`** — T4 absorbs the folder Explorer + Open Folder + menus;
  editor tabs become new phase **T4b**; T14 reduced to cross-file refs + project
  settings.

T4 resumes (`status: in_progress`); its sprint table is re-planned via
`/pm-phase-plan T4`.
