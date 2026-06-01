---
phase: T2
title: Frontend skeleton (Vite + React + TS + three.js)
status: done
min_met: true
max_met: true
duration_planned_days: 10
duration_actual_days: 2
started: 2026-05-31
finished: 2026-06-01
---

# Phase T2 report — Frontend skeleton

Closed 2026-06-01 over two sessions. The `web/` frontend stands up end-to-end:
a Vite + React + TS app with a VS-Code-lite shell, a three.js viewport that
renders a backend-served mesh, NX-style camera, and a typed WS transport feeding
a doc-store. Verified **live in a browser tab** at `https://nexus/touch`
(Caddy-hosted, browser-dev mode N5/N6), connected to the sidecar, orbiting a
real backend-built cube. Delivers **F2, F3 (FE), the FE half of F19, N1
groundwork, N5, N6**. No blockers filed.

## What shipped

Against the planned 10-row sprint table:

| Day | Task | State | Evidence |
|-----|------|-------|----------|
| 1 | Vite + React + TS scaffold, `base:"./"` | ✅ done | `c1127e7`; build + Tailscale-reachable dev server |
| 2 | `web/app` three-panel shell + `web/platform` shim | ✅ done | `c1127e7`; + activity bar, status bar, resizable sidebar (tweaks) |
| 3 | protocol-types wiring (`@protocol` alias) | ✅ done | `c1127e7`; `tsc -b` + vite resolve the generated TS |
| 4 | `web/transport` WS client + Vitest decode | ✅ done | `fcefb03`; 6 tests; live `ready` verified |
| 5 | connect-time demo mesh (BE dev flag) | ✅ done | uncommitted; `demo_mesh` → 40 mm cube via real adapter→executor→tessellate |
| 6 | `web/doc-store` + Vitest | ✅ done | uncommitted; 4 tests incl. transport→doc-store integration (fake WS) |
| 7 | `web/viewport` (three.js) + app wiring | ✅ done | uncommitted; `Viewport.ts`, engine wiring; live cube at nexus/touch |
| 8 | NX camera | ✅ done | rebound to the user's scheme (middle=rotate, scroll=zoom) |
| 9 | exit-criterion verification | ✅ done | live browser tab → connect → orbit a backend mesh |
| 10 (Max) | VS-Code-lite styling + HMR polish | ✅ met | dark theme + activity/status bars + resizable splits (exceeds); Vite HMR functional on-box |

Beyond the plan:
- **Live browser-dev hosting** (the T2-era ops task): `https://nexus/touch` —
  Caddy serves the static bundle (`/touch/*`) and reverse-proxies the sidecar
  WS (`/touch/ws`). Captured in auto-memory `browser-dev-hosting`.
- **Full FE receive-pipe with tests**: transport → doc-store → viewport,
  10/10 Vitest (decode + URL resolution + store + a transport→store integration
  via a fake WebSocket).
- **Interaction model captured** for T3 (`docs/notes/interaction.md`).

## What slipped (and why)

Min fully met; closure is `done`. Deliberate omissions / deferrals:
- **No pan gesture** — the user's mouse scheme (left=select+prompt, right=context
  menu, middle=rotate, scroll=zoom) has no pan; left unbound by choice.
- **Remote HMR** — the hosted `nexus/touch` is a static build (no live refresh);
  HMR works on-box via the Vite dev server. Static hosting was the user's choice
  for simplicity (graceful reload, no container recreate).
- **Bidirectional FE↔BE contract tests** (T1b carry-over) — partial: decode unit
  tests + a transport→doc-store integration test + live end-to-end verification,
  but not formal generated-type contract tests in both directions. Carry to T3+.
- **`dependency-cruiser`** — deferred per plan (decisions P2); FE module set still
  small.
- **Bundle is 693 KB** (three.js, no code-splitting) — chunk-size warning noted;
  a pre-release polish item, not blocking dev.

## Surprises

- **Host firewall dropped the docker-bridge→host hop.** `ufw` default-deny
  silently DROPs container→host on `8765` (Caddy 502 / host-side timeout to the
  bridge IP). Fix: `ufw allow from 172.16.0.0/12 to any port 8765 proto tcp`.
  Caddy's 80/443 work without it because Docker publishes them (bypasses ufw);
  raw host ports (5173 dev server, 8765 sidecar) do not — which is also why a
  direct `:5173` is unreachable remotely. (→ memory `browser-dev-hosting`.)
- **Caddy file_server needs the files inside the container.** Reused the existing
  `/etc/caddy` bind mount (`touch-dist/`) to host the static bundle — a reload,
  not a container recreate.
- **SNI when testing Caddy via curl** — `--resolve <name>:443:127.0.0.1` is
  required; connecting to `localhost` sends SNI=localhost, for which Caddy has no
  cert/site → TLS handshake fails (misleading exit 35), independent of the `Host`
  header.
- **Auto-mode classifier correctly gated** the network-exposure Caddy edit until
  explicit user approval — a good guardrail; the WS exposure was then approved.
- **Tooling**: TS 5.8-only `erasableSyntaxOnly` flag dropped for pinned TS 5.7;
  used React 19 ref-as-prop instead of `forwardRef`.

## Decisions taken mid-phase

No `/pm-blocker` filed. Logged in `docs/notes/decisions.md` (2026-05-31):
- **/pm-phase-plan T2** — connect-time demo mesh (G1); `dependency-cruiser`
  deferred (P2); targeted Vitest only (P3).
- **/pm-architecture pre-pass** — named `web/app` (F2 shell owner) + `web/platform`
  (N5 capability shim); fixed the generated-protocol layout drift.
- **WS network exposure** (user-approved live, 2026-06-01): sidecar
  `TOUCH_BACKEND_WS_HOST=0.0.0.0` + Caddy `/touch/ws` + ufw rule, Tailscale-gated,
  dev-box only (shipped app stays localhost-only per ADR-0005).
- **Static-build hosting** chosen over a Vite-dev-server reverse proxy.
- **Interaction model** captured for T3 (`docs/notes/interaction.md`).

## Recommended changes for next phase (T3 — picking + click-to-prompt)

1. **Implement the captured interaction model**: left-click select→prompt,
   right-click context menu; the FE picking reads the per-face IDs + finder hints
   already streamed in the mesh (N1 — instant local highlight, no round-trip).
2. **Remove the throwaway `demo_mesh`** once real ops drive geometry; replace the
   demo cube with the click→prompt→op→mesh round-trip.
3. **Write the formal bidirectional FE↔BE contract tests** against the generated
   types now that the FE exists (T1b carry-over).
4. **Wire `dependency-cruiser`** (deferred from T2) as the FE module graph grows.
5. **Document the dev bring-up** (sidecar 0.0.0.0 + demo_mesh + Caddy + ufw) as a
   `make`/doc target; auto-memory `browser-dev-hosting` has the recipe meanwhile.
6. **Bundle code-splitting** (dynamic-import three.js) — pre-release polish.
7. **Pan gesture** — add if the user wants one (candidate: shift+middle).
