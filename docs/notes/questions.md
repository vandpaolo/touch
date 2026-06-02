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
