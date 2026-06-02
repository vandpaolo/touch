# Notes — Open Questions

Things you haven't decided. "Should we use X or Y?", "is Z in scope?",
"what happens when…?".

Each question is a candidate for:
- A **Conflict** or **Probe** question in a skill's next pass
- An **ADR** if the answer is hard to reverse
- An entry under "Decisions deferred" in `02-architecture.md`

Format suggestion:

```
- [ ] Q: <question>
      context: <why it's open>
      candidates: <option A>, <option B>
```

Tick the box and link to where the answer landed once decided.

---


## 2026-05-31 — Always-on hosted browser-dev UI behind Caddy (dev-infra)

- **Idea (user):** once UI work ramps up, host the browser-dev frontend
  24/7 behind the existing Caddy route on nexus, so it's always reachable
  (laptop/anywhere) for immediate update→check — not just a local Vite tab
  on nexus. The `.exe` build stays the release/test artefact.
- **Already planned (core):** browser-dev mode is F19 + N5 (must) + N6.
  Same web FE runs as Electron renderer (prod) or browser tab (dev);
  ADR-0009 kept "the path to a hosted-browser version later" open.
- **Framing fix:** don't host Electron (that's the `.exe` wrapper) — host
  the `web/` Vite app + reverse-proxy the sidecar WebSocket.
- **Open question / interaction:** ADR-0005 binds the WS to `127.0.0.1`
  only; auth/TLS out of v0 ("if remote, auth becomes its own ADR").
  Cleanest path that avoids app-level auth: Caddy ON nexus → `https`
  static FE + `wss`→`127.0.0.1:<port>` sidecar, access gated by Tailscale
  + Caddy. Sidecar stays localhost-bound.
- **Bearing on phases:** T1b — keep WS host/port configurable (F19 already
  says configurable port) and the FE connection URL config-driven with a
  *relative* ws path, so a reverse proxy is trivial later. T2 — the actual
  Caddy hosting / always-on dev instance would land here.
- **To formalize:** if this becomes a v0.1 requirement, run
  `/pm-requirements`; the auth piece may warrant a new ADR per ADR-0005's
  trigger.

### 2026-05-31 — User stance: web UI hosted for live iteration, repo stays clean

- **User preference:** wants the UI kept on the web during dev — always up,
  refreshable, visually improvable on the fly — *without* dirtying the
  desktop-app repo.
- **Resolution (no conflict):** `web/` is product code (the Electron renderer
  + the browser-dev tab — same bundle, N5/N6), so it belongs in the repo.
  The *hosting/serving* layer (Caddy route on nexus, any always-on
  systemd/Vite unit, Tailscale gating) stays **host-level ops, not committed**
  — that's the line that keeps the trunk clean.
- **Iteration loop:** Vite dev-server HMR is the on-the-fly edit→refresh loop;
  the "always-on" Caddy instance is just that server (or a built bundle)
  exposed 24/7 over Tailscale.
- **Design note for T2:** keep Electron-only surfaces (native file dialogs,
  OS keychain via preload) behind a thin **capability shim** so the identical
  FE runs in a plain browser tab without diverging from prod. Cheap from day
  one, painful to retrofit.

## 2026-06-01 — T3 live-use feedback (planner UX → T5 inputs)

From driving the first real click→chamfer round-trip:

- **Required params must trigger a clarifying question, not an assumption.**
  Saying just "chamfer" (no size) currently lets the LLM assume a value; the
  user expects "how many mm?" instead. → F7 / T5. Implies a per-kind
  required-params contract (chamfer: length; hole: diameter; …) that, when
  unmet, makes the planner ASK rather than default. (Touch's `intent_validation`
  per-kind contracts are the natural basis.)
- **Don't silently substitute unsupported ops.** "make a hole" produced a
  cylinder, because T3's planner offers only box/cylinder/sphere/chamfer, so the
  LLM picks the nearest allowed kind. The planner should recognize an
  unsupported intent and refuse/clarify ("I can't make holes yet") instead of
  guessing wrong. → T5 clarification + the deferred modifier set
  (hole/fillet/shell/pattern) in the focused Intent→Operation effort.

## 2026-06-01 — More live feedback (→ T4 / prompt UX)

- **Geometry must persist via the file explorer (T4).** Hard-refresh resets to
  the demo cube because nothing is saved. Want: create a `.touch` file → open it
  → the modified geometry persists (refresh-proof), since the op history is saved
  in the file. This is core T4 (.touch save/load + file-tree open/new) — the
  demo-cube throwaway seed should be replaced by a real new/open-document flow.
- **Prompt loading feedback was too subtle.** The only in-flight cue was the
  bottom-left status-bar "working…". Fix (done pre-T4): keep the prompt panel
  OPEN in a working state until the modification lands. T5 expands this into the
  full chat-thread-stays-open clarification UX.

## 2026-06-01 — T4 file explorer should mirror VS Code / Cursor

> absorbed into docs/01-requirements.md (F18/F32/F33/F34) @ 2026-06-01

The `.touch` file explorer (T4, F10/F18) should model the **VS Code / Cursor
Explorer**: collapsible file/folder tree in the left sidebar (the Explorer panel
the activity-bar icon already toggles), single-click to open a file, context
actions for new / rename / (later) delete, the active file highlighted. Fits the
VS-Code-lite shell already built in T2. Keep it familiar — same muscle memory.

---

- [ ] Q: face selection is brittle — a lot of actions fail with FinderError.
      context: surfaced 2026-06-02 while testing the live editor. Many edit
      actions died as an opaque "subprocess exited with code 1". Root cause:
      the adapter re-resolves the clicked face from a 3D point via
      `resolve_face_containing(solid, point, tol)`, which fails in two common
      ways — clicking on/near an edge or corner → "ambiguous: N faces contain
      point" (the point touches multiple faces); a pick that lands just off the
      brep surface (mesh-vs-brep float gap, tol 0.5 mm) → "no face contains
      point". So normal clicks near edges break. (A third, separate failure:
      chamfer length larger than the geometry allows → build123d ValueError
      "try a smaller length" — relates to the min-params/clarify-questions item
      for T5/F7 already noted.)
      mitigated now: the executor surfaces the real exception line instead of
      the exit code, so the user at least sees *why* (T4, error observability).
      real fix (T5 / finder phase): stop re-resolving from a 3D point. The FE
      already knows the exact clicked face (faceTag → faceId → finder hint);
      carry a stable face identifier through the selection so the backend
      selects the clicked face directly instead of a lossy point-containment
      lookup. Likely an ADR (selection / face-identity model). Out of scope for
      T4 (scope-frozen) — re-open via /pm-blocker or sequence into T5.
