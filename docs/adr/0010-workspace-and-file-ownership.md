# 0010 — Workspace model & file ownership: backend owns the folder, frontend owns the interaction

- **Status:** Accepted
- **Date:** 2026-06-01
- **Deciders:** vandpaolo (with an adversarial critic panel, 2026-06-01)

## Context

T4 first shipped single-document persistence with a flat list of `.touch` files
under `out_root`. The desired experience is the **VS Code / Cursor folder
workspace** (blocker `2026-06-01-folder-workspace-explorer`, requirements
F18/F32/F33/F34): File → Open Folder → the Explorer mirrors that folder 1:1, and
the user creates `.touch` parts inside it.

This forced a decision on **who owns the files**. An initial draft put the
*frontend* in charge (File System Access API in-browser / Electron `fs`), with
the sidecar reduced to "rebuild from streamed history". A five-pass critic panel
(2026-06-01) returned **reconsider** on that flip:

- **File System Access API is a weak foundation for the canonical path:**
  Chromium-only over HTTPS; directory handles don't survive a reload without an
  IndexedDB handle-persistence subsystem; permissions re-prompt/expire. F32's
  "refresh → reopen → identical" silently depended on unbudgeted machinery.
- **The browser-dev privacy win was notional:** the sidecar runs on nexus, files
  on the laptop, so the op-history (the real IP) round-trips to the server over
  the WS anyway — "files never touch the server" buys little in dev.
- **Split-brain:** sidecar session document + FE mirror + on-disk file = three
  copies with no reconciliation (external edits, autosave).
- **`loadHistory` opens were O(history):** every open/tab-switch would replay the
  whole history through a subprocess OCP build — seconds for long parts, can hit
  the 30 s timeout.
- An `fs`-shaped `web/platform` shim keyed on string paths is a category error in
  the browser (FSA gives opaque handles, not paths).

## Decision

**The backend owns the workspace filesystem; the frontend owns the workspace
interaction.** Same Open-Folder → 1:1-tree → create-parts UX, one source of
truth, and it reuses the T4 backend.

- **Backend (sidecar) owns the files.** It is pointed at a **workspace root** and
  lists/reads/writes the folder tree (lazy per directory), creates/renames/removes
  `.touch` parts, opens a part (load its history into the session, rebuild), and
  saves. The session remains the single source of truth for the active part
  (ADR-0008 plan/undo/redo). This *extends* the T4 messages (flat `listFiles`
  → a folder-tree `listDir`; `open`/`save` become workspace-relative) — no
  `loadHistory`, no FE file I/O, no split-brain.
- **Frontend owns the interaction.** `web/platform` provides the **folder
  picker** only: in Electron a native open-directory dialog → the chosen path is
  handed to the (local) sidecar; in browser-dev the user picks/enters a folder on
  the sidecar's host. `web/workspace` holds the tree + active-part id and issues
  file commands over the WS; `web/file-tree` renders the tree.
- **The Explorer tree is hand-rolled** (~200 lines: recursive rows, keyboard,
  lazy expand) over `web/workspace` — *not* `react-arborist` (single-maintainer,
  shaky React-19 story, virtualization premature for shallow part-folders). The
  **Codicons** icon font (MIT) gives the familiar look; our own dark theme. We
  replicate the VS-Code *pattern* in our own code, no copied implementation.
- **State is multi-document-ready now.** `Session` keys documents by id
  (`documents: dict[id, …]`, one entry today) with **per-document** undo/redo +
  dirty; `web/doc-store` mirrors per-id. The UI shows one active part; the
  **editor-tab strip ships next phase** without re-architecting the containers.
- **Rebuild is cached.** A content-addressed cache (hash of the op-history prefix
  → STEP/mesh) makes open/undo/redo/tab-switch O(1) instead of O(history).
- **`web/platform` for files is a narrow capability**, not an `fs` clone:
  `pickFolder()` (+ Electron path / browser folder ref). Actual file I/O is the
  backend's.

**Electron desktop = the true "folder on your machine":** the native dialog picks
a local folder, the *local* sidecar reads it — files genuinely never leave the
machine (N12/N13). **Browser File System Access API** (laptop folder inside the
hosted tab) is a **deferred nicety**, not the foundation.

## Consequences

- Single source of truth (the sidecar) — no split-brain; crash recovery stays the
  history-replay path (N8) the sidecar already owns.
- Reuses + extends the T4 backend (document save/load, snapshots) rather than
  discarding it; smaller change than the FE-owns flip.
- The folder-workspace UX is identical to the user; what differs is *whose disk*
  (nexus box in browser-dev, the user's machine in Electron).
- Multi-doc-ready containers + the rebuild cache de-risk the next-phase editor
  tabs and keep opens fast.
- **Cost:** browser-dev opens a folder on the sidecar's host, not the laptop (the
  laptop-folder-in-browser case waits for the deferred FSA path). Acceptable: dev
  files live where the compute is.
- The `.touch` *format* (ADR-0006) is unchanged.

## Alternatives rejected

- **Frontend owns the folder (FSA / Electron fs), sidecar stateless-rebuilds**
  (the draft): rejected per the critic panel — FSA fragility, notional dev
  privacy, three-copy split-brain, O(history) opens. Salvageable later as the
  browser laptop-folder nicety, behind the same `web/workspace` seam.
- **Flat `out_root` list** (T4 day-3): too thin — not a folder workspace. Folded
  into the backend-owned *tree*.
