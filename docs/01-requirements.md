# 01 — Requirements

> *Re-baselined 2026-05-29 for **Touch** (the Maquette pivot). Maquette's
> prior F1–F14 / N1–N10 were CLI-shaped and are **superseded** by the
> table below — the rewrite is intentional, the old content is in git
> history. Update via `/pm-requirements`.*

This document covers **Touch v0** (the POC milestone — see
`00-vision.md` § Success criteria). v0.1+ requirements live in
`03-roadmap.md` and gain their own row only when their phase is being
shaped. Priority field uses `must` / `should` / `could`.

## Functional requirements

### A. Application & user interaction

| ID | Requirement | Acceptance criterion | Priority |
|----|-------------|----------------------|----------|
| F1 | Touch launches as a single **Windows desktop application**. | A friend downloads `Touch-vX.Y.Z-setup.exe` from a GitHub Release and runs it; the app's main window opens with no further setup. | must |
| F2 | The main window presents a **VS-Code-like layout**: 3D viewport (centre), file/project tree (left), a prompt panel anchored to the current selection (transient overlay), and a Settings panel reachable from the menu. | All four UI surfaces exist and are reachable. Layout is usable on a 1920×1080 display. | must |
| F3 | The 3D viewport uses **NX-style mouse camera controls**: middle-mouse rotate, shift+middle pan, scroll zoom. | Manual: orbiting/panning/zooming on a fresh model feels equivalent to NX defaults. | must |
| F4 | The viewport renders **hover highlights** on the face / edge / vertex under the cursor in real time. | Cursor-to-highlight latency is imperceptible (N1 bar); highlight follows the cursor across all model entities. | must |
| F5 | **Click selects** the face / edge / vertex under the cursor. Selection state lives in the frontend; **no backend round-trip is required** for selection. | A profiler / log shows zero network calls between hover/click and the rendered highlight. The selection persists until cleared or replaced. | must |
| F6 | Clicking opens a **prompt box anchored to the selection**, prefilled with no text; submitting it sends `{selection_id, point_xyz, prompt_text, conversation_state}` to the backend. | Submitting from the prompt box dispatches a single `plan` message to the backend with the expected payload shape. | must |
| F7 | If the backend returns a **clarifying question** (instead of an operation), the prompt box continues as a short **chat thread** in place, holding the selection context, until the conversation produces an operation or the user cancels. | At least one ambiguous prompt during the mini-PC flow triggers a clarifying question and is resolved through a follow-up. | must |
| F8 | A **successful operation appends** to the current document's operation history; the viewport updates to reflect the new geometry (mesh delta from backend). | After each accepted op, the document's history grows by exactly one entry and the viewport shows the new shape. | must |
| F9 | The user can **undo / redo** by stepping back / forward through the operation history. | Undo restores the prior model state; redo re-applies. Multiple levels supported within a session. | must |
| F10 | The user can **save** the current document as a `.touch` file (JSON), and **open** a `.touch` file — the model is rebuilt by replaying its operation history. | Round-trip: model → save → close → open → identical model. The `.touch` file is human-readable JSON. | must |
| F11 | The user can **export STEP** for B-rep handoff to other CAD. | A produced STEP opens cleanly in FreeCAD and matches the on-screen model. | must |
| F12 | The user can **export STL / 3MF** for 3D-printing handoff. | A produced STL opens cleanly in a standard slicer (Cura/Prusa) and matches the on-screen shape (within tessellation tolerance). | should |
| F13 | The **Settings panel** lets the user choose between the two LLM provider modes (see F31): (a) Anthropic API — paste/edit their Claude API key, stored in the **OS keychain** (Windows Credential Manager via `keyring`), never plaintext on disk; (b) Claude Code — Touch detects the local Claude Code install + auth status and uses it (no credential stored by Touch). | The repo and on-disk app config contain no plaintext key after Settings save. In API mode, removing the key from the keychain breaks API calls. In Claude Code mode, logging out of Claude Code breaks subsequent calls. | must |
| F14 | A **session cost indicator** shows running USD cost for the current Touch session, sourced from the backend's `pricing` module. | A multi-prompt session ends with the displayed total equal to the sum of per-prompt costs reported by `pricing.price(...)`. | should |
| F15 | A **cold-start splash** is shown until the backend signals `ready`. | On first launch on a clean machine, the splash is visible while OCP imports; it dismisses on `ready`. | should |
| F16 | If the backend exits unexpectedly mid-session, Touch **restarts it, replays the current document's history**, and surfaces a single toast: "engine restarted, work restored." | Forcibly killing the backend process during a session results in restored model state and a single user-visible toast. | should |
| F17 | The user can **cancel** a long-running operation in progress (e.g. while the LLM is thinking). | A cancel button is visible during a `plan`/`apply` round-trip; cancelling stops the call, leaves the model unchanged, and clears the prompt box. | must |
| F18 | The **file/project tree** lists `.touch` files (and other files) in the current project root, with basic open / new-file / rename. | Manual: opening, renaming, and creating a `.touch` file via the tree works without leaving the app. | should |

### B. Backend / engine

| ID | Requirement | Acceptance criterion | Priority |
|----|-------------|----------------------|----------|
| F19 | The backend runs as a **localhost WebSocket server** on a configurable port. The **same protocol** is consumed by the Electron renderer (prod) and a browser tab (dev). | Pointing a plain browser at `http://localhost:<port>/` and launching the wrapped `.exe` produce a functionally identical app, against the same backend. | must |
| F20 | The backend **tessellates** the current B-rep model with **per-face IDs encoded into the mesh data**; the frontend uses those IDs for selection (F5). | After any geometry update, the streamed mesh contains a triangle→face-id mapping the frontend can use without further backend calls. | must |
| F21 | The backend accepts **structured operations** defined by the `Intent` operation schema. Unknown / malformed ops are rejected with a **structured error** (typed payload), never a raw Python traceback to the UI. | Sending an invalid op yields a structured error event; no traceback string appears in any frontend-visible message. | must |
| F22 | An **LLM Planner** (Anthropic Claude) converts `{prompt + selection context + conversation state}` into either a structured operation or a clarifying question. | Mocked-client tests assert both branches (op / question) of the planner output land cleanly. Live integration verifies one of each on the mini-PC flow. | must |
| F23 | The current model is **rebuildable from the operation history alone**. Live in-memory state is a *derived cache*; the `.touch` history is the source of truth. | Killing the backend, restarting, and replaying the in-memory history reproduces the same model deterministically (F16, N8). | must |
| F24 | The **build123d adapter** is a pure function `operation history → build123d source code`; same input → byte-identical output. | Adapter snapshot tests: emit twice, diff empty (N10). | must |
| F31 | The backend has a **pluggable LLM-client abstraction** with two v0 implementations: (a) **Anthropic API** (`anthropic.Anthropic`, using the user's API key from the OS keychain — F13a); (b) **Claude Code** (`claude-agent-sdk` driving the user's locally-installed Claude Code under their Pro/Max subscription — F13b). The planner accepts either through the same interface; the active client is chosen at session start from Settings. | A `LLMClient` Protocol exists in code; both implementations satisfy it and pass the same contract test. The mini-PC flow succeeds end-to-end with each client. The Settings UI hides Claude Code mode when Claude Code isn't installed or authed. | must |

### C. Distribution & repository

| ID | Requirement | Acceptance criterion | Priority |
|----|-------------|----------------------|----------|
| F25 | The project is **open source under MIT** (continued from Maquette). | `LICENSE` file present at repo root; SPDX tag matches in README. | must |
| F26 | The repository is **hosted on GitHub** with **semver tags** for releases. | Tags follow `vX.Y.Z`; a CHANGELOG entry exists per tag. | must |
| F27 | Tagged versions trigger a **GitHub Actions** build that publishes a Windows `.exe` installer (plus a portable archive) as a **GitHub Release**. | Pushing a `v*` tag results in a Release page with the `.exe` artefact attached, within CI runtime budget. | should |
| F28 | An end-user installs by **downloading the `.exe` from a Release page and running it** — no separate Python/Node install, no command line. | A friend on a fresh Windows machine, following only the README install line, opens Touch within 5 minutes of starting. | must |

### D. Developer environment (nexus-ops standards)

| ID | Requirement | Acceptance criterion | Priority |
|----|-------------|----------------------|----------|
| F29 | The developer's Claude API key is stored **SOPS-encrypted in the repo** (`secrets.env.sops.yaml`) per the **nexus-ops `secrets.md`** standard; decrypted at dev time to a gitignored `.env` using the host's age key. The current plaintext `.env` (carried from Maquette) is migrated to SOPS as an explicit early-roadmap task. | No plaintext key in any committed file; `sops -d secrets.env.sops.yaml > .env` produces a working dev `.env` on the host; pre-commit hook (or CI guard) blocks any plaintext `.env` from being committed. | must |
| F30 | The dev-host backend's working directory (test runs, scratch `.touch` files, ad-hoc exports) lives under **`/srv/touch/`** per the **nexus-ops `storage.md`** standard. | The default backend `out_root` config on the dev host resolves to `/srv/touch/`; running locally writes there. | should |

## Non-functional requirements

| ID | NFR | Target | Verification |
|----|-----|--------|--------------|
| N1 | **Interactivity** — hover/select/orbit/pan/zoom is rendered entirely in the frontend with no backend call. | Cursor-to-highlight latency < 50 ms on a model of ≤ 50 k triangles, p95. | Manual + a frame-timing test on a reference model. |
| N2 | **Prompt-submit latency** — geometry update after submit. | Median round-trip < 10 s (LLM-bound) on the v0 mini-PC ops; UI shows a thinking indicator for the full round-trip. | Stopwatch + log on each mini-PC step. |
| N3 | **LLM cost per prompt.** | Average < $0.05 USD per accepted prompt on the v0 op set, measured via `pricing.py`. | Cost indicator (F14) over the mini-PC session. |
| N4 | **Single-file install.** The released `.exe` installs Touch with all runtimes bundled — no separate Python, Node, or other prereq. | A friend on a fresh Windows machine installs and launches with zero additional installs. |
| N5 | **Dual run modes.** The same web frontend code runs as (a) the Electron renderer in the `.exe` and (b) a plain browser tab against a localhost backend, with no code divergence. | A single FE build artefact is served in both modes; behavioural parity test on a couple of key flows. |
| N6 | **Headless dev.** Touch develops cleanly on a headless Linux dev box, frontend opened in a browser. | The author's daily dev loop is the browser-tab mode on nexus; the wrapped `.exe` is only built for releases. |
| N7 | **Document portability & versioning.** `.touch` files are JSON, carry `schema_version`, are diff-friendly in git, and remain readable across compatible minor versions. | Round-trip test on a corpus of `.touch` files across versions; a `git diff` on a small edit is human-readable. |
| N8 | **Crash resilience.** A backend crash does not lose the user's in-progress work; the operation history is the safety net. | Chaos test: kill the backend mid-session; assert F16 path produces an identical model. |
| N9 | **Secret hygiene.** End-user keys are stored in the OS keychain (no plaintext on disk); dev secrets in the repo are SOPS-encrypted (per nexus-ops `secrets.md`). | Filesystem scan + git-history scan find no plaintext key strings. Removing the keychain entry breaks API calls. |
| N10 | **Adapter determinism.** Same operation history → byte-identical build123d source. | Snapshot tests in CI. |
| N11 | **Open source.** Source is MIT-licensed; release artefacts are public. | `LICENSE` + public repo + public Releases. |
| N12 | **No accidental cloud dependency.** Touch runs entirely from the user's machine + the Claude API; no Touch-operated server is required for end users. | Network inspection: end-user traffic goes to `api.anthropic.com` and nowhere else. |

## User stories

- **US1** — As an engineer-friend on Windows, I want to install a single
  `.exe` and use it with my own Claude key, so I can try AI-driven CAD
  without setting up developer tooling.
- **US2** — As a Touch user, I want to orbit my model, click a face, and
  describe the change in words, so I can model parts by *pointing* rather
  than navigating feature-tree menus.
- **US3** — As a Touch user, when my prompt is ambiguous, I want the
  system to *ask* me what it needs rather than guessing wrong, so the
  model evolves correctly.
- **US4** — As a Touch user, I want to save and re-open my work in a
  clean file format I can read and version-control, so my parts aren't
  locked into a black-box format.
- **US5** — As a Touch user, I want to export STEP for FreeCAD/NX (and
  STL/3MF for printing), so Touch fits into my existing workflow.
- **US6** — As the developer on a headless Linux dev box, I want to run
  Touch as a browser tab against a localhost backend, so I can iterate
  without a desktop.
- **US7** — As the developer, I want my dev Claude key SOPS-encrypted in
  the repo, so I follow the nexus-ops policy and never carry plaintext
  credentials.

## User flows

### Happy path — a single click+prompt step

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend (three.js)
    participant BE as Backend (Python WS server)
    participant Planner
    participant Adapter as build123d adapter
    participant Kernel as build123d/OCP

    User->>FE: orbit, click face (local)
    FE->>FE: raycast → highlight face by id (no network)
    User->>FE: type prompt + submit
    FE->>BE: plan(prompt, selection, point, conv_state)
    BE->>Planner: prompt + structured context
    Planner-->>BE: structured Operation
    BE->>Adapter: history + new op → code
    Adapter-->>BE: build123d source
    BE->>Kernel: execute → updated solid
    Kernel-->>BE: solid + tessellate (per-face ids)
    BE-->>FE: geometryUpdated(meshDelta + faceIds)
    FE-->>User: viewport updates, history grows by 1
```

### Clarification path

```mermaid
sequenceDiagram
    actor User
    participant FE
    participant BE
    participant Planner

    User->>FE: click face + ambiguous prompt
    FE->>BE: plan(prompt, selection, ...)
    BE->>Planner: prompt + context
    Planner-->>BE: clarifyingQuestion
    BE-->>FE: conversationTurn(question)
    FE-->>User: prompt box shows question
    User->>FE: reply
    FE->>BE: plan(reply, selection, conv_state=...)
    BE->>Planner: extended context
    Planner-->>BE: Operation
    Note over BE,FE: ... happy path resumes ...
```

### Backend crash & recovery

```mermaid
sequenceDiagram
    participant Main as Electron main
    participant BE as Backend (Python)
    participant FE as Frontend

    Note over BE: ...processing an operation...
    BE--xMain: process exits (e.g. OCC fault)
    Main->>Main: detect exit, no traceback to user
    Main->>BE: spawn replacement process
    BE->>Main: ready
    Main->>FE: backend_restored
    FE->>BE: rebuild(history)   %% sends the in-memory .touch
    BE-->>FE: geometryUpdated (full re-tessellation)
    FE-->>FE: toast: "engine restarted, work restored"
```

## Constraints & assumptions

### Constraints (cannot change)

- **Python ≥ 3.12** (build123d, OCP, anthropic SDK all target it).
- **OpenCascade B-rep kernel** via the OCP Python wrapper (re-used from
  Maquette).
- **Frontend tech is web** (HTML/CSS/JS + three.js for the viewport).
- **Anthropic Claude** is the only LLM provider in v0, but reachable via
  **two paths** (F31): the Anthropic API (user's own key) *and* Claude
  Code under the user's Pro/Max subscription (via `claude-agent-sdk`).
  The client is abstracted behind a Protocol so adding a third path
  (Vertex AI / Bedrock / another provider) is cheap; no
  provider-agnostic layer beyond what F31 needs.
- **Windows is the v0 distribution target** for the `.exe`. macOS / Linux
  desktop builds are later milestones.
- **`.touch` is JSON**, schema-versioned, the source-of-truth document
  format.
- **No NXOpen imports** anywhere in `src/` (continued from Maquette's
  hygiene rule, even though NX adapter is not active scope — kept as a
  cheap CI guard).
- **Dev side adopts nexus-ops standards:** `secrets.md` (SOPS) and
  `storage.md` (`/srv/touch/`).

### Assumptions (chosen, may revise)

- **LLM consistency.** Claude reliably emits valid structured operations
  for v0 (similar to Maquette's planner reliability, with selection
  context as an added grounding signal).
- **Claude Code Agent SDK is stable enough.** The `claude-agent-sdk`
  interface (and the `claude -p` CLI as a fallback) remains workable for
  programmatic, non-interactive use through v0. If it churns, the
  pluggable abstraction lets Touch fall back to API-only without
  rewriting the planner.
- **Native bulk tessellation** via OCP / `ocp_tessellate` is performant
  enough for interactive use (research-supported; not yet benchmarked at
  Touch's interactive cadence).
- **Electron + Python sidecar packages cleanly** into a Windows `.exe`
  (the explicit open spike from the 2026-05-29 architecture research —
  flagged in the vision; should be the first thing the roadmap proves).
- **Append-only history is sufficient for v0.** Re-editing earlier
  operations (parametric history) is *not* a v0 feature; it is the
  topological-naming problem and is explicitly deferred.
- **Per-face IDs from the tessellator are stable within a session** for
  the click→prompt flow (sufficient for append-only; not the full
  cross-edit persistent-naming story).
- **FreeCAD 1.x opens STEP cleanly** (required for the v0 success
  criterion, identical to Maquette's assumption).

## Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | **Packaging** — Electron + Python + OCP into a reliable Windows `.exe` for non-technical friends turns out painful (the unverified architecture spike). | high | high | The first roadmap phase is an **explicit packaging + round-trip + picked-face spike**: prove the scary part end-to-end before building features. Falls back to a portable archive or a different shell (Tauri/Wails) if Electron+Python proves intractable. |
| R2 | **Picking robustness** — face IDs don't survive subtle model changes; clicks select the wrong feature. | med | high | Kernel-owned IDs (Onshape pattern) carried per-face in the mesh **plus** geometric "finders" (replicad pattern) so the LLM operation references re-derivable geometry rather than brittle indices. Append-only v0 sidesteps the worst of it. |
| R3 | **Silent semantic failure** — the LLM emits a structured op that build123d crashes on, or builds the wrong geometry (Maquette's R7 carries over). | high | med | Structured errors back to the UI (F21); user can undo (F9); ad-hoc cost is bounded (N3). The proper fix is the v0.1 evaluator (the Maquette idea, re-purposed for interactive use). |
| R4 | **Cold-start latency** — OCP import takes seconds on first launch; a friend may think the app is broken. | med | med | Splash screen (F15) with clear status text; backend signals `ready` to dismiss it. |
| R5 | **LLM cost balloons** per session beyond friend tolerance. | low | med | Cost indicator (F14, N3); cost-cap behaviour deferred to v0.1 if it surfaces. |
| R6 | **Conversational UX** is confusing — users don't know when the system is asking vs guessing. | med | low | UI distinguishes a clarification (question) from an applied op visually; can always cancel/restart. Iterate. |
| R7 | **Geometry transport jank** — mesh deltas large enough to feel slow on a complex model. | low (v0 parts are small) | med | Binary WS frames, deltas only, tessellation tolerance tuning. |
| R8 | **OS keychain unavailable** on a locked-down corporate Windows. | low | low | Fallback to a clearly-warned plaintext config file; document as a known limitation if it surfaces. |
| R9 | **`.touch` schema evolution** breaks older files. | low | med | `schema_version` field (F10, N7); migration helpers per minor bump. |
| R10 | **GitHub Releases pipeline** for Windows builds is fiddly to set up. | low | low | Standard CI pattern; many Electron+Python apps document this. Manual builds as a fallback for the first release. |
| R11 | **Operation kind not supported** by build123d/OCP for a prompt a friend tries. | med | med | Extras/escape-hatch carries over from Maquette (raw build123d as a relief valve, marked best-effort). |
| R12 | **Claude Code mode friction** — `claude-agent-sdk` churns mid-v0, or non-technical friends can't install/login to Claude Code → the subscription path is broken or unused. | med | low | Pluggable client abstraction (F31) means Anthropic-API mode is always the no-extra-install default; Claude Code mode is detected and hidden in Settings when unavailable. Touch ships clear in-app guidance for the install+login path; SDK pinned to a tested version in `pyproject.toml`. |
