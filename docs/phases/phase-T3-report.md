---
phase: T3
title: Picking + click-to-prompt (first end-to-end round-trip)
status: done
min_met: true
max_met: false
duration_planned_days: 11
duration_actual_days: 1
started: 2026-06-01
finished: 2026-06-01
---

# Phase T3 report — Picking + click-to-prompt

Closed 2026-06-01, single session. **The first real click→prompt→geometry
round-trip works**, live with the Anthropic planner: click a cube face → prompt
→ chamfer op → finder resolves the face → its edges chamfer → re-tessellated
mesh back → viewport updates. Delivers **F4, F5, F6, F8 (in-memory), F20, F22**
and the first demonstration of **N1**. No blockers filed.

## What shipped

Against the planned 11-row sprint table:

| Day | Task | State | Evidence |
|-----|------|-------|----------|
| 1 | FE picking — hover highlight (N1) | ✅ done | `90b2e3e`; `web/picking`, raycaster→faceTag, zero WS calls on hover |
| 2 | FE selection — click → SelectionStore + finder | ✅ done | `90b2e3e`; `web/selection`, distinct persistent highlight |
| 3 | FE prompt panel (F6) | ✅ done | `90b2e3e`; one `plan` msg {selection, prompt_text} on submit |
| 4 | Planner chamfer path (real LLM) | ✅ done | `62e5d02`; LLM {kind,params} + server-injected selection; mocked + live tests |
| 5 | Finder resolution (contains_point → face) | ✅ done | `f1da6e2`; `finder.py`; 0/many → FinderError; cube tests |
| 6 | Chamfer emit (face → edges) | ✅ done | `f1da6e2`; adapter chamfer kind; round-trip 6→10 faces; deterministic |
| 7 | Round-trip wiring | ✅ done | `f1da6e2`; demo cube = real document op so chamfer has a base; live PASS |
| 8 | FE viewport update + thinking indicator | ✅ done | `1968927`; doc-store→viewport; "working…" status + error toast (F21) |
| 9 (Max) | Distinct hover/click styles + clicked point shown | ◑ partial | distinct blue-hover/orange-select shipped; **clicked-point display not done** |
| 10 (Max) | No-selection primary (create from scratch) | ✗ skipped | deferred |
| 11 | Exit verification (live) | ✅ done | headless: face selection + "add a 5 mm chamfer here" → chamfer op → 6→10 faces; user confirmed in-browser |

Verified live end-to-end (real Anthropic + OCP): `{"demoFaces":6,"op":"chamfer","chamferFaces":10,"PASS":true}`.

Beyond the plan: a **`make up`/`make down` dev sidecar toggle** (`e8d45a2`) for the
browser-dev UI; an **error toast** (F21 surfacing) on the FE.

## What slipped (and why)

Min fully met; closure is `done`. **`max_met: false`** — two Max items not done:
- **Clicked-point display in the prompt panel** (transparency) — not built.
- **No-selection primary path** ("a 40 mm cube" with no pick → create geometry
  on a base plane) — skipped. Deferred; relates to T4's new-document flow.

The distinct hover-vs-click highlight styles (the other half of Day 9 Max) did
ship.

## Surprises / live-use learnings

- **The demo cube had to become a real document op.** A chamfer modifies a prior
  solid; with the demo mesh as a throwaway, `document.history` held only the
  chamfer → adapter refusal. Fix: `session.demo_mesh` appends the cube as a real
  op so the click→chamfer flow has a base.
- **The finder hint was anchored at a face corner** (tessellate's first node),
  which resolves ambiguously across the 3 faces sharing it. Fixed
  `selectionFromHit` to build `contains_point` at the actual (interior) click
  point.
- **Emitted build123d code now imports `touch_backend.finder`** (runs in the
  Executor subprocess). New coupling: the packaged sidecar must bundle
  `touch_backend` so the subprocess can import it (PyInstaller hidden-import —
  note for packaging).
- **Live planner UX gaps (user feedback → T5):** under-specified prompts (just
  "chamfer") make the LLM *assume* a size instead of asking; unsupported intents
  ("make a hole") get *silently substituted* to the nearest allowed kind
  (cylinder) rather than refused. Captured in `notes/questions.md`.

## Decisions taken mid-phase

No `/pm-blocker` filed. Logged in `docs/notes/decisions.md` (2026-06-01):
- **/pm-phase-plan T3** — chamfer-only scope (one modifier + one finder); chamfer
  targets the selected face's edges; real Anthropic planner (Settings UI stays T6).
- **Pre-T3 audit override** (2026-06-01-pre-T3): 8 PASS / 1 FAIL (dead links in
  append-only history; one fixed, rest overridden).
- **Demo cube as a real document op** (this phase) to give chamfer a base.
- **`make up`/`make down`** sidecar lifecycle (dev): on-demand, detached, the
  user's chosen "change → up → look → down" loop (roadmap open-decision #6).

## Recommended changes for next phase (T4 — `.touch` doc + undo/redo)

1. **The document-is-history substrate is already live** (ops append; replay
   rebuilds geometry) — T4 adds `.touch` save/load + undo/redo on top.
2. **Replace the throwaway demo-cube seed**: T4's new-document flow should start
   empty; the no-selection primary path (T3 Max, skipped) is the natural way to
   seed geometry — fold it into T4 or T5.
3. **Carry the live feedback to T5 (clarification):** required-params → ask (not
   assume); unsupported ops → refuse/clarify (not substitute). `notes/questions.md`.
4. **Packaging note:** the emitted code's `touch_backend.finder` import needs a
   PyInstaller hidden-import when the sidecar is frozen (T-packaging).
5. **Deferred still:** the modifier set (hole/fillet/shell/pattern) + richer
   finders (the focused Intent→Operation effort).
