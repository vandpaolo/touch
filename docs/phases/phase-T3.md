---
id: T3
title: Picking + click-to-prompt (first end-to-end round-trip)
status: done
started: 2026-06-01
finished: 2026-06-01
min_goal_met: true
max_goal_met: false
blocker: null
depends_on: [T2]
---

# Phase T3 — Picking + click-to-prompt

- **Goal:** The first end-to-end click→prompt→geometry round-trip — the first
  time the user actually drives Touch. Click a face, type an intent, see the
  geometry change.

## Depends on

- **T2 done** — viewport renders a backend mesh; transport → doc-store →
  viewport pipe; the mesh already carries `faceTagPerTriangle` +
  `face_id_to_finder_hint`.
- **ADR-0008** (picking + finders + append-only) — the load-bearing design.
- **Architecture/classes** — FE `picking`/`selection`/`prompt`; BE
  `planner`/`operation_adapter`/`executor`/`tessellate`.
- **Requirements** F4, F5, F6, F8, F20, F22 approved.
- **A working Anthropic key** on the dev box (`.env`/keychain) — T3 runs the
  *real* planner; the Settings UI to configure it is T6.
- **Interaction model** captured in [notes/interaction.md](../notes/interaction.md):
  left-click = select + prompt, right-click = context menu (right-click menu is
  a Max/T-later item), middle = orbit.

## Minimum deliverable

Click a face of the (backend-built) cube → instant local hover/click highlight
(N1, zero round-trip) → a prompt panel opens anchored to the selection → submit
sends `{selection, point_xyz, prompt_text}` → the **real planner** returns a
**chamfer** `Operation` (kind+size from the LLM; the `Selection`/finder comes
from the click) → the adapter **resolves the `contains_point` finder to the
clicked face and chamfers its bounding edges** → executor → re-tessellate → mesh delta
back → viewport shows the chamfered cube. The op is appended **in memory**
(persistence is T4). No clarification branch yet (that's T5).

**Scope discipline:** exactly one modifier kind (**chamfer**) and one finder
predicate (**`contains_point`**). Other modifiers (fillet/hole/shell/pattern)
and richer finders stay deferred to the focused Intent→Operation effort.

## Maximum deliverable

Also: distinct hover-vs-click highlight styles; the clicked point shown in the
prompt panel (transparency); a manually-typed prompt **without** a selection →
the planner emits a *primary* feature (box/cylinder/sphere — the adapter path
that already works, no finder) built on a base plane.

## Sprint / day breakdown

| Day | Task | Output | Done when |
|-----|------|--------|-----------|
| 1 | FE `picking`: three.js raycaster → triangle index → `faceTag` lookup (from the doc-store mesh) → **hover highlight** of the whole face (N1). | `web/picking` + face-hover. | Hovering a face highlights it; a profiler/log shows **zero** WS calls on hover (F4, N1). |
| 2 | FE `selection`: left-click → `SelectionStore` (target=face, `point_xyz`, `finder` from the mesh's `face_id_to_finder_hint`, `face_id_at_capture`); click highlight. | `web/selection`. | Clicking a face sets selection (carries a `contains_point` finder); persists until cleared/replaced (F5). |
| 3 | FE `prompt` panel (F6): opens anchored to the selection on click; text input; submit builds + sends a `plan` message `{selection, point_xyz, prompt_text}`. | `web/prompt`. | Submitting dispatches exactly one `plan` message with the expected payload shape (transport log). |
| 4 | BE planner → **modifier op**: system-prompt + parsing so "add a 5 mm chamfer here" → `Operation(kind=chamfer, params)`; the FE `Selection` is attached server-side (not from the LLM). Real `AnthropicAPIClient` wired (dev key). | `planner` chamfer path. | Mocked-client test: prompt+selection → a `chamfer` Operation carrying the FE selection. Live call produces a valid chamfer op. |
| 5 | BE **finder resolution**: resolve a `contains_point` `Selection` against the built solid → the unique **face**, then its bounding **edges** (chamfer target, decided 2026-06-01); 0/many faces → structured error (F21; clarification is T5). | `finder` resolver. | Cube solid + a face's `contains_point` → that face + its edges resolved; ambiguous/none → clean structured error. |
| 6 | BE **chamfer emit**: `operation_adapter` compiles a resolved chamfer Operation → build123d chamfer of the selected face's edges (deterministic). | adapter chamfer kind. | emit→execute yields a cube chamfered on the clicked face's edges (feature/bbox check); emit twice = byte-identical (N10). |
| 7 | Round-trip wiring: `session` handles `plan`-with-selection → planner → adapter(resolve+chamfer) → executor → tessellate → mesh delta; op appended in-memory. | end-to-end server path. | Contract test (mocked LLM → chamfer) drives a cube→chamfer mesh round-trip server-side. |
| 8 | FE viewport update on mesh delta + a "thinking" indicator across the RTT (N2 perceived latency). | FE round-trip UX. | After submit, the viewport swaps to the new mesh; a thinking indicator shows during the wait. |
| 9 (Max) | Hover-vs-click highlight styles + clicked `point_xyz` shown in the prompt panel. | highlight polish. | Hover and selected styles are visually distinct; the point is displayed. |
| 10 (Max) | No-selection primary path: typed prompt w/o selection → primary feature on a base plane (existing box/cylinder/sphere adapter). | primary-no-selection path. | "a 40 mm cube" with no selection builds + renders. |
| 11 | Exit verification (live): click a cube face → "add a 5 mm chamfer here" → chamfered cube within the N2 budget; capture. | verified round-trip. | The exit criterion below holds live in a browser tab. |

## Exit criteria

- In a browser tab, click a face of the backend-built cube, type "add a 5 mm
  chamfer here", and see the chamfered cube within the N2 latency budget.
- Hover/click highlight is instant and does zero WS round-trips (N1).
- The accepted op grows the in-memory history by exactly one entry (F8).

## Known risks for this phase

- **R1 — T3 absorbs the first slice of the deferred ADR-0008 modifier+finder
  work** (chamfer geometry + `contains_point` resolution). This is the heaviest
  unknown and was explicitly deferred from T1b as "its own focused effort."
  **Mitigation:** scope to *one* modifier (chamfer) + *one* finder
  (`contains_point`); everything else stays deferred. (See push-back — the
  alternative is to split modifiers into a dedicated phase and make T3's first
  round-trip a primary.)
- **R2 — chamfer semantics on a *face* click. Decided (2026-06-01):** selecting
  a face chamfers **all edges bounding that face**; picking stays face-only this
  phase (no edge picking). The finder resolves `contains_point` → face → its
  bounding edges → build123d chamfer.
- **R3 — real-LLM dependency.** The round-trip needs the live planner to turn NL
  into a chamfer op reliably. Prompt-engineering risk; the Settings/credential
  UI is T6, so T3 relies on the dev `.env`/keychain key. **Mitigation:** few-shot
  the planner; mocked-client tests for determinism; live test gated.
- **R4 — N2 latency.** The RTT includes a live LLM call + subprocess OCP rebuild
  + tessellation; may exceed the N2 budget. **Mitigation:** measure; the thinking
  indicator covers perceived latency; tuning is ongoing.
- **R5 — finder-resolution edge cases.** `contains_point` on a clean cube is
  easy, but face-boundary/tolerance cases exist. **Mitigation:** use the hint's
  `tol_mm`; 0/many matches → structured error (the F7 clarification UX is T5).
- **R6 — face-highlight rendering.** Mapping raycaster `faceIndex` →
  `faceTagPerTriangle` → highlighting all triangles of that face needs a
  grouping/overlay approach in three.js (vertex colors, a second draw group, or
  an overlay mesh). **Mitigation:** spike the cheapest approach on day 1.
