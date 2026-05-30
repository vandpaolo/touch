# Notes — Decisions

Auto-populated by skills. Every time you answer a Gap / Probe / Conflict /
Push-back question, the Q+A pair lands here with a timestamp.

Manual additions are allowed and welcome (e.g. "decided in conversation
2026-05-16 that we'll use Postgres").

Format:

```
## 2026-05-16 — /pm-vision
- Q (gap): What's the measurable v0 success criterion?
- A: STEP file opens in FreeCAD with no warnings on the three demo prompts.
- → 00-vision.md § Success criterion
```

The `→` arrow points to where the answer landed in a formal doc. This is
the audit trail: every fact in a formal doc should be traceable back to
either a note section or a decision here.

---

## 2026-05-16 — /pm-vision

- Q (gap G1): What's the biggest risk for the PR-FAQ?
- A: Silent semantic failures — Intent valid, code runs, geometry wrong.
  Schema is expandable; if a backend (NX) becomes brittle we file a blocker
  and pivot to FreeCAD. Multi-backend pattern is robust to backend-specific
  failures.
- → docs/00-pr-faq.md § What's the biggest risk?

- Q (gap G2): What does failure look like?
- A: Option A — every prompt produces a STEP that runs but is visually wrong,
  requiring human verification anyway, defeating the speed goal.
- → docs/00-pr-faq.md § What does failure look like?

- Q (probe P1): Strategic-fit map size — keep 6 / trim to 3 / prose?
- A: Trim to 3.
- → docs/00-vision.md § Strategic-fit map (kept agentic systems, structured
  outputs, code generation for licensed APIs)

- Q (probe P2): v0.1/v0.2 scope blocks in vision vs roadmap-only?
- A: Keep both (vision tells the full arc).
- → docs/00-vision.md § Scope (no change from migrated content)

- Q (probe P3): Press release headline — technical or benefit-first?
- A: Benefit-first. "Describe a part. Get a CAD model in seconds."
- → docs/00-pr-faq.md § Press release § Headline

- Q (probe P4): Audience tertiary (NX seat owners) — promote or keep?
- A: n/a → kept tertiary (logical conclusion: primary audience IS the author,
  who happens to also use NX; the strategic-fit NX-leaning is about the
  *implementation challenge*, not the audience tier).
- → docs/00-vision.md § Audience (no change from migrated content)

- Q (probe P5): Non-goals vs decisions-deferred — separated cleanly?
- A: Yes — non-goals = "won't do"; decisions-deferred = "might do later".
- → noted as a framework convention; no doc change required

- Q (conflict C1): Provider abstraction — non-goal forever or deferred?
- A: n/a → logical conclusion: vault wording already says "not on day one"
  (deferred), framing as "premature abstraction" is consistent with the
  architecture's "Decisions deferred" entry. No real conflict; both docs
  agree once read together.
- → no doc change required (architecture's Decisions-deferred entry will be
  reconfirmed during /pm-architecture)

- Q (conflict C2): Personal tooling vs portfolio framing — load-bearing?
- A: Personal tooling first, portfolio second.
- → docs/00-vision.md § Strategic-fit map (added preface emphasizing this)

- Q (push-back B1): NX adapter in v0 — keep or move?
- A: Move to v0.1 since it simplifies v0 by ~30%.
- → docs/00-vision.md § Scope: removed NX adapter from v0, added to v0.1
  with note explaining the move; PR-FAQ "How we'll know" updated.

- Q (push-back B2): Success criterion — one prompt or three?
- A: Three passes.
- → docs/00-vision.md § Success criteria (rewritten to require all three)
- → docs/00-pr-faq.md § How will we know it worked? (updated)

- Q (push-back B3): "Mesh-only output" out-of-scope — keep or move to ADR?
- A: For now keep out of scope; we can update with new features later.
- → docs/00-vision.md § Scope § Out of scope (no change from migrated content)

## 2026-05-16 — /pm-requirements

- Q (gap G1): v0 prompt #3 (L-bracket) exact wording?
- A: Option (a) — "a 60 × 40 × 5 mm L-bracket with a 6 mm hole in the centre
  of each flange" — good for MVP.
- → docs/00-vision.md § Success criteria (prompt #3 locked)
- → docs/01-requirements.md (implicit in the success-criterion verification path)

- Q (gap G2): Cost-cap behaviour on a single run?
- A: Option (c) — just record actual cost in status.json, no special handling.
  If cost becomes a problem we fix it after MVP.
- → docs/01-requirements.md N2 (no cap), R8 (mitigation updated)

- Q (gap G3): v0 feature/modifier kind coverage — all 11 or only what the
  3 prompts need?
- A: All 11. If we only support prompt-driven intents the planner is more
  likely to succeed but the resulting code is worse.
- → docs/01-requirements.md F4 (full schema coverage), N3 (snapshot fixtures
  per kind), Constraints (11 kinds locked for v0)

- Q (probe P1): Renderer failure — block exit 0 or continue?
- A: n/a → kept current draft: renders are nice-to-have, failure doesn't block.
- → docs/01-requirements.md F7 (should priority), R6 (continue at exit 0)

- Q (probe P2): inspect/list/replay commands — keep v0 or defer to v0.1?
- A: Move to v0.1.
- → docs/01-requirements.md (F12/F13/F14 removed from v0; moved to "Deferred
  from v0" appendix); will land in v0.1 requirements via 03-roadmap.md

- Q (probe P3): Sandboxing strictness in v0?
- A: Defer to v0.1.
- → docs/01-requirements.md "Deferred from v0" (sandboxing); Assumptions
  section notes v0 trusts the LLM

- Q (probe P4): Cost-tracking precision — tokens × table or SDK-reported?
- A: Track everything for accuracy.
- → docs/01-requirements.md F9 (status.json includes tokens.{input, output,
  cache_read, cache_creation}; cost computed from pricing.py × actual SDK
  tokens; use SDK cost field directly when exposed)
- → docs/01-requirements.md F10 (trace.jsonl per-call breakdown)

- Q (probe P5): Priority labels — v0/v0.1/v0.2 buckets in this doc, or
  v0-only with must/should/could?
- A: Separation is better.
- → docs/01-requirements.md fully restructured: v0-only, priorities are
  must/should/could; v0.1 + v0.2 functional reqs removed and recorded under
  "Deferred from v0" for traceability; will be re-introduced in their
  owning version's requirements doc via /pm-requirements on a future pass

- Q (conflict C1): --no-nx / --only-nx CLI flags — keep in v0 as no-ops,
  drop, or move with NX adapter?
- A: Option (a) — move to v0.1 with the NX adapter requirement.
- → docs/01-requirements.md F14 (v0 CLI flag list = --out, --max-iter,
  --exec-timeout, --model, -q/-v only); NX flags in "Deferred from v0"

- Q (conflict C2): v0 success — STEP > 0 bytes only, or human geometric
  correctness required?
- A: Yes, requires human acceptance.
- → docs/01-requirements.md F5 acceptance (explicit human-reviewer check
  required in v0 since Evaluator is v0.1)

- Q (push-back B1): R7 silent semantic failure — ship unmitigated in v0
  or add a sanity check?
- A: Add the sanity check.
- → docs/01-requirements.md F6 (new functional requirement: dimension
  sanity check via regex extraction from prompt vs Intent params; logs
  DIMENSION_WARNING to trace.jsonl and warnings[] in status.json; does
  NOT fail the run); R7 mitigation updated; R11 added (sanity check
  false-positive risk); Assumptions section notes the check is best-effort

- Q (push-back B2): Tighten N1 to 20 s for v0 (NX out of v0)?
- A: Yes.
- → docs/01-requirements.md N1 (target tightened to < 20 s p95 for v0); v0.1
  target stays at 30 s (added there during /pm-requirements for v0.1)

- Q (push-back B3): `maquette list` O(n) scans — cap default or accept?
- A: Keep as is, add cache later.
- → no doc change required (list is now v0.1 anyway per P2; the eventual v0.1
  requirements doc will record this decision)

## 2026-05-16 — /pm-architecture

- Q (gap G1): SanityCheck tolerance — confirm ±1% or ±0.5 mm (whichever larger)?
- A: Yes, fine for now.
- → docs/adr/0002-dimension-sanity-check.md § Decision (tolerance unchanged)

- Q (gap G2): pricing.py table values — supply, hardcode TODO, or defer?
- A: Option (a) — supply current Anthropic prices.
- → docs/adr/0003-prompt-caching-for-cost.md (concrete prices added: Opus 4.7
  $5/$25/$0.50/$6.25, Sonnet 4.6 $3/$15/$0.30/$3.75, Haiku 4.5 $1/$5/$0.10/$1.25
  per Mtok, verified 2026-05-16 via web search)
- → docs/02-classes.md Pricing class diagram (concrete values in note)

- Q (gap G3): Prompt-versioning hash — single SHA-256 or per-file?
- A: Single SHA-256 is fine.
- → docs/adr/0003-prompt-caching-for-cost.md § Decision (confirmed single
  rolled-up SHA-256 of prompts/ contents)
- → docs/02-architecture.md § Cross-cutting (reproducibility) confirmed

- Q (probe P1): SanityCheck position — standalone module or inside Planner?
- A: Standalone for testing.
- → no doc change required (current draft is standalone agent.sanity)

- Q (probe P2): Adapter contract — loose convention or Protocol?
- A: Protocol for conformance and type checking.
- → docs/02-architecture.md § Layered responsibilities (adapters package
  defines Adapter Protocol; concrete adapters conform)
- → docs/02-classes.md § Adapter Protocol + concrete adapters (new diagram
  showing Adapter <<Protocol>>; Build123dTarget conforms to it; mypy/pyright
  enforce signature)

- Q (probe P3): prompts/ structure — raw .md or Python package?
- A: Keep .md.
- → no doc change required (current draft has raw .md at prompts/)

- Q (probe P4): Pricing table granularity — 4 classes or 2?
- A: Stick to Anthropic's price structure (4 classes).
- → no doc change required (current draft has 4 classes); ADR 0003 + Pricing
  class diagram both reflect 4 classes

- Q (probe P5): Render failure and N1 latency sample inclusion?
- A: Option (a) — count in the sample.
- → no doc change required (current draft is implicit a)

- Q (conflict C1): Worker as separate module or inline into Loop?
- A: Keep module.
- → no doc change required (current draft has agent.worker as its own module)

- Q (conflict C2): Loop as sole writer to output/?
- A: Confirmed.
- → docs/02-architecture.md § Dependency rules (already reflects this)

- Q (push-back B1): agent.sanity as separate module?
- A: Yes, separate.
- → no doc change required (current draft has agent.sanity as its own module)

- Q (push-back B2): pricing.py as separate module?
- A: Yes, separate.
- → no doc change required (current draft has pricing as its own module)

- Q (push-back B3): intent.py owns per-kind contracts (a), or split into
  intent.py types + intent_validation.py (b)?
- A: Option (b) — split. User noted "you can overrule if bad choice."
  Considered overruling (per-kind contracts are arguably part of the schema
  spec). Decided to respect user's choice: B is a defensible architectural
  style (separating declarative types from behaviour) and the user thought
  about it. The `@model_validator validate_references` stays inside the
  Intent pydantic model (idiomatic); only `validate_kind_contracts` moves
  out.
- → docs/02-architecture.md repo layout (added intent_validation.py); §
  Layered responsibilities (split intent row, added intent_validation row)
- → docs/02-data-model.md § Validation rules (per-kind contracts live in
  intent_validation.py now)
- → docs/02-classes.md module map (split intent / intent_validation rows);
  § Bounded contexts (Domain now includes both); § Dependency rules (added
  intent_validation depends only on intent rule); § Test strategy (added
  intent_validation test row)

## 2026-05-16 — /pm-roadmap

- Q (gap G1): Per-phase day estimates — confirm/tighten/loosen/defer?
- A: Estimates. Throughout implementation user refreshes docs to split/add
  days. OK for now.
- → no doc change required; estimates stand as gantt guesses

- Q (gap G2): CI setup — GitHub Actions / GitLab / local-only / no-CI?
- A: GitHub Actions on every push.
- → docs/03-roadmap.md Phase 0 MIN (CI workflow with ruff + pytest +
  import-linter + NX-grep guard moved from Max to Min)

- Q (gap G3): License choice — MIT or Apache-2.0?
- A: MIT (repo starts private anyway).
- → docs/03-roadmap.md Phase 0 MIN (LICENSE file required)
- → docs/03-roadmap.md § License & repo hygiene: pick is now locked

- Q (probe P1): 4 phases for v0 or 3 (merge Foundations into Adapter)?
- A: Keep 4 (now 6 after splits — see C1, P2).
- → no doc change required (no merge)

- Q (probe P2): Split Phase 2 (Pipeline) into 2a/2b?
- A: Yes, split.
- → docs/03-roadmap.md: Phase 2 replaced by Phase 2a (Planner + Sanity +
  Worker, 3d) and Phase 2b (Executor + Render + Loop, 3d)

- Q (probe P3): Split Phase 7 into 7a/7b/7c?
- A: Yes, split.
- → docs/03-roadmap.md: Phase 7 replaced by Phase 7a (Sandboxing, 2d),
  Phase 7b (Example-level regression CI, 2d), Phase 7c (Cost caps, 1d)

- Q (probe P4): v0.2 phases — more shape now or fill in at /pm-phase-plan?
- A: For now it's OK.
- → no doc change required

- Q (probe P5): Pre-commit hooks — promote to MIN or keep in MAX?
- A: Keep in MAX.
- → no doc change required (CI grep guard is in MIN; local pre-commit
  reinforcement is in MAX)

- Q (conflict C1): Keep "Smoke + 3 examples" as Phase 3.5 (separate from
  Phase 3 CLI)?
- A: Keep as 3.5.
- → docs/03-roadmap.md: Phase 3 now CLI-only (2d); Phase 3.5 = Smoke + 3
  reference examples (2d, v0 ships here)

- Q (conflict C2): v0.1 ordering — NX first then Evaluator (current) or
  Evaluator first then NX?
- A: Reorder — Evaluator first, NX second.
- → docs/03-roadmap.md: Phase 4 = Evaluator + refinement loop; Phase 5 =
  NX adapter (swapped)

- Q (push-back B1): F4 11 kinds in v0 — realistic or defer some to v0.1?
- A: Keep all 11 in v0.
- → no doc change required (Phase 1 MIN still requires all 11)

- Q (push-back B2): Phase 5 (now Phase 4) success bar — 7/10 or tighten?
- A: Tighten.
- → docs/03-roadmap.md Phase 4 Exit criterion: tightened from ≥7/10 to
  ≥8/10 of corpus prompts produce evaluator-passing STEP within
  max_iterations=3 and < $0.50/prompt. (Chose 8/10 over 9/10 because
  Evaluator is unproven at v0.1 ship; 9/10 risks unrealistic gate.)

- Q (push-back B3): Distinguish per-kind v0 vs per-example v0.1 regression CI?
- A: n/a → I decided to distinguish them explicitly.
- → docs/03-roadmap.md Phase 7b Goal section now explicitly notes the
  layered relationship: per-kind catches micro-drift in adapter logic
  (v0 N3); per-example catches drift that emerges only in combinations
  (v0.1 7b). They're complementary, not duplicates.

## 2026-05-16 — /pm-phase-plan phase-0

- Q (gap G1): Python version pin — 3.11.x, 3.12.x, or 3.13.x?
- A: 3.12.x.
- → docs/phases/phase-0.md § Policies: `requires-python=">=3.12,<3.13"`

- Q (gap G2): Runtime dep pinning strategy — strict, compatible, hybrid?
- A: Hybrid.
- → docs/phases/phase-0.md § Policies: strict (`==`) on build123d only;
  compatible (`~=X.Y.0`) on the rest (anthropic, pydantic, pyvista,
  typer, python-dotenv); compatible on all dev deps

- Q (probe P1): Promote README + .env.example to MIN?
- A: Yes, promote.
- → docs/phases/phase-0.md § MIN (both added); MAX trimmed accordingly;
  Day 1 task now includes README skeleton + .env.example as outputs

- Q (probe P2): examples/ stub form — empty .gitkeep or examples/README.md?
- A: Option (b) — examples/README.md placeholder.
- → docs/phases/phase-0.md § MIN (examples/README.md added); Day 4 output

- Q (probe P3): Type checker — mypy or pyright?
- A: Pyright.
- → docs/phases/phase-0.md § Policies + Day 1 (pyright in dev deps) +
  Day 4 (pyrightconfig.json + CI step); Phase 1 (later) is where the
  Adapter Protocol conformance check actually fires

- Q (conflict C1): Day 4 task density — keep as one day or split?
- A: Keep as Day 4 (one day).
- → no doc change required (Day 4 still bundles CI + import-linter +
  pyright + examples + (MAX) pre-commit; MAX items are <30 min each)

- Q (push-back B1): Coverage target — none / soft / hard gate?
- A: Soft target ≥80% tracked but not gating.
- → docs/phases/phase-0.md § Policies (soft 80% on intent +
  intent_validation; coverage added to CI workflow; reported but not
  gating); Exit criterion #2 updated

- Q (push-back B2): TDD discipline — strict TDD or pragmatic test-along?
- A: User's choice — "what you think is more reliable, im scared strict
  TDD gets lost at some point."
- Decision: pragmatic test-along. Strict TDD slips on solo multi-month
  projects (which the user flagged). Test-along with a per-commit rule
  ("no src/ change lands without a test for new public surface") + the
  ≥80% coverage backstop is more sustainable. Documented in § Policies
  / Testing discipline.
- → docs/phases/phase-0.md § Policies / Testing discipline

## 2026-05-28 — /pm-architecture (CF#1 adapter export contract)

- Q (probe): How to resolve carry-forward #1 (extras-only Intents emit
  no export_step)?
- A: /pm-architecture touch now (freeze lifted, no active phase).
  Confirmed live first (Opus 4.7): L-bracket → features:[] + extras
  defining `body`, emitted code had no export_step.
- Decision (ADR-0004): `body` is the reserved export var for the
  extras-only path ONLY; feature-based Intents keep exporting
  features[-1].id (uniform "always body" would break 5 snapshot
  fixtures: cylinder/extrude/loft/revolve/sphere).
- → docs/02-data-model.md § Adapter export contract; docs/adr/0004

- Q (G1): Degenerate Intent — features empty AND extras empty/absent.
  Refuse or stay silent?
- A: AdapterRefusal(where="export:empty"). A no-geometry Intent is a
  planner failure; surface it, don't produce a STEP-less run.
- → docs/02-data-model.md § Adapter export contract; ADR-0004 Decision

- Q (G2): Enforce the `body` assignment in extras — light-check + refuse
  early, or trust extras?
- A: Trust extras; do not parse. export_step(body,...) emitted
  unconditionally on the extras-only path; missing `body` → NameError at
  execution (executor → error.json, phase-2b). Preserves "never parse or
  rewrite Intent.extras".
- → docs/02-data-model.md § Adapter export contract; ADR-0004 Decision

## 2026-05-28 — /pm-architecture (render ownership) + /pm-phase-plan phase-2b

- Q (B1, phase-2b plan): Who owns rendering — Executor or Loop?
- A: Loop. Rationale: single-responsibility (executor = pure subprocess
  + sandbox, the concern phase-7a builds on); F7 non-fatal render falls
  out naturally (executor exit code stays execution-only); executor
  tests stay PyVista-free. Discovered the C4 container view already drew
  `Loop --> Render` while 02-classes.md contradicted it (executor→render
  + ExecutionResult.renders) — the move *resolves* that contradiction
  rather than introducing a pivot. Cheap now (no code yet).
- → docs/02-classes.md (module map executor/render rows; ExecutionResult
  drops `renders`; Loop class diagram + note); docs/02-architecture.md
  (L2 dataflow edge → `Loop -. STEP path .-> Render`); docs/phases/phase-2b.md

- Q (P1): Split loop.py across Day 4 (core) + Day 5 (trace/status), or merge?
- A: Merge into one Day 4 loop task. Plan now 4 min + 1 max = 5 units.
- → docs/phases/phase-2b.md § Sprint / day breakdown

## 2026-05-28 — Headless render backend (phase-2b day 2 implementation)

- Q: How to render orthographic PNGs headless on nexus (no X server)?
  Stock `vtk` wheel is X11-only and segfaults off-screen; no Xvfb/OSMesa.
- A: Swap `vtk` -> `vtk-osmesa==9.3.1` (VTK's wheel index,
  https://wheels.vtk.org). Bundled OSMesa CPU software GL; no X, no Xvfb
  subprocess, no sudo, works on bare ubuntu CI. Chosen over Xvfb (sudo +
  display process + now-legacy) after a research-agent analysis.
- Gotcha 1: OpenCascade (OCP, via build123d) and VTK-OSMesa fight over
  the Mesa GL context — loading OCP before rendering -> blank frames. Fix:
  STEP->STL conversion runs in a subprocess; the render process never
  imports build123d.
- Gotcha 2: OSMesa needs an explicit plotter.render() before screenshot,
  else blank frame.
- Web bonus (future, not built): build123d export_gltf -> .glb viewable
  in a browser <model-viewer> is ~free; possible later enhancement for
  the user's "view via web" wish. F7 (3 PNGs) unchanged.
- → src/maquette/render/orthographic.py; pyproject.toml (pyvista comment);
  .github/workflows/ci.yml (swap step)

## 2026-05-28 — /pm-phase-plan phase-3

- Q (P3-Q1): How to handle mid-run Anthropic API errors (auth/rate-limit/
  network) during planning? loop._plan only caught PlannerExhausted, so
  an APIError escaped Loop.run before a run folder existed.
- A: Harden the loop. loop._plan catches broad Anthropic API errors and
  maps them to PLANNING_FAILED / exit 10 + error.json, so every
  invocation yields a complete run folder (F8/F12/N10). CLI still wraps
  Loop.run as a backstop (exit 1 on truly unexpected errors).
- → docs/phases/phase-3.md § Min deliverable + Day 1 + P3-R2 + exit #3

- Q (day count): 3 units (2 min + 1 max) vs roadmap gantt's 2d?
- A: Keep 3 (Day 1 cli+loop-hardening, Day 2 tests+README, Day 3 MAX).
- → docs/phases/phase-3.md § Sprint / day breakdown

## 2026-05-28 — /pm-phase-plan phase-3.5

- Q (Conflict C1): v0 ship latency bar — vision says 30 s, N1 + roadmap
  exit say 20 s p95. Which?
- A: 20 s (N1, the committed NFR). Vision's 30 s left unedited but flagged;
  a /pm-vision touch could align it later. Phase-2b run was 10.1 s (margin).
- → docs/phases/phase-3.5.md § Policies + Exit criteria

- Q (probe): CI smoke / ANTHROPIC_API_KEY in CI?
- A: Mock-only push CI (no key secret, per phase-2a). The 3-prompt live
  smoke is a gated `pytest -m live` test, run manually. No billable CI.
- → docs/phases/phase-3.5.md § Policies + Max deliverable

## 2026-05-28 — /pm-vision (blocker 2026-05-28-v0-references-exceed-schema)

- Q: How to resolve the v0-references-exceed-schema blocker? (User: "do
  all four resolutions.")
- A: Sequenced. NOW (vision): restate references honestly + add a v0
  capability bound. THEN (roadmap): front-load schema edge-selection/
  hole-positioning (opt 2) + correctness guard/Evaluator (opt 4) into
  early v0.1. Nothing dropped; v0 ships honest, capability lands next.
- → docs/00-vision.md § Success criteria + capability bound; docs/00-pr-faq.md

- Q: v0 ship references — which, and how strict?
- A: Cube + cylinder ("a 2 mm chamfer", all-edges, drop "top edge") are
  the HARD gate (schema-native, reliable). L-bracket ("a 6 mm mounting
  hole", single) is a BEST-EFFORT showcase of the extras relief valve —
  demonstrated, not gating (extras un-guarded until v0.1 Evaluator).
- → docs/00-vision.md § Success criteria

- Q (Conflict C1): vision 30 s vs N1 20 s ship bar?
- A: 20 s (N1). Vision + pr-faq updated 30 s → 20 s. C1 resolved.
- → docs/00-vision.md, docs/00-pr-faq.md

- Cross-layer follow-ups (rest of the blocker resolution): /pm-requirements
  (F5 "matches within capability bound", R7 materialized + best-effort
  extras, restate N1/N2 "3 prompts" → 2 gate + 1 showcase, add v0 scope
  boundary); /pm-roadmap (phase-3.5 references; front-load opt-2 + opt-4
  into early v0.1).

## 2026-05-28 — /pm-vision (blocker 2026-05-28-l-bracket-showcase-hole-unreliable)

- Q: Phase-3.5 verification found the L-bracket showcase ships holeless —
  the extras Hole() drills on a workplane that misses the flange (volume
  identical with/without). How to handle the showcase?
- A: Narrow the showcase to the bare L-shape — `"a 60 × 40 × 5 mm
  L-bracket"` (no hole). Extras reliably produces the compound L-shape
  (the thing the schema can't name); precise hole positioning is v0.1
  phase-4.5 (first-class schema hole-positioning). Hard gate (cube +
  cylinder) unaffected.
- → docs/00-vision.md § Success criteria + capability bound; docs/00-pr-faq.md;
  mirrors to sync in docs/03-roadmap.md (phase-3.5) + docs/phases/phase-3.5.md

## 2026-05-29 — /pm-vision (Maquette → Touch pivot)

- Q: OS target for the Touch v0 POC .exe?
- A: Windows .exe primary (friends on Windows); same frontend runs as a
  browser tab on the headless Linux dev box. macOS/Linux desktop = later.
- → docs/00-vision.md § Success criteria + Scope

- Q: How to treat the existing Maquette roadmap (v0.1 phases 4–10)?
- A: FULL re-baseline for Touch — re-run /pm-requirements → /pm-architecture
  → /pm-roadmap fresh; Maquette's roadmap is superseded. Salvage what
  fits: evaluator → v0.1 correctness check; schema-v2/finders → face
  reference; conversational → now CORE (was v0.2); NX adapter + supporting
  CLI commands → reassess (CLI is now an engine entry-point, not the
  product).
- → drives the formalization sequence after this vision locks

- Positioning flip recorded: Maquette was "assistant hands you a draft and
  leaves"; Touch IS the editor (model inside it). Inverts a Maquette
  non-goal. Engine (intent/planner/adapter/executor) retained as Touch's
  headless core.

- Follow-up (downstream, not vision): the literal rename Maquette → Touch
  cascades to the repo dir, the `maquette` package, the `maquette design`
  CLI, CLAUDE.md, README. That's an implementation chore for later, not a
  design-doc edit. Docs now call the product "Touch"; code stays
  `maquette`-named until a rename pass.

## 2026-05-29 — /pm-requirements (Touch re-baseline)

- Q: Should friends be able to use their Claude Pro/Max subscription
  instead of paying per-token API?
- A: Yes — add as a v0 must (F31). Pluggable LLM-client abstraction with
  two modes: (a) Anthropic API (user's key, OS keychain), (b) Claude
  Code via `claude-agent-sdk` (user's subscription, no key in Touch).
  Settings picks the active mode; Claude Code mode hidden when not
  installed/authed. Friends with the subscription get flat-rate, no
  cost anxiety; API mode is the no-extra-install default.
- → 01-requirements.md F13, F31, Constraints, Assumptions, R12

- Decisions made on /pm-requirements probes (user directives):
  - F9 (undo/redo) → must (was should).
  - F27 (GH Actions auto-build) stays should for v0; promote v0.1.
  - F29 (SOPS dev key) → must (was should). Migrate Maquette's plaintext
    .env to secrets.env.sops.yaml as an early-roadmap task; pre-commit
    hook blocks plaintext .env commits.
  - Remaining probes (P1 planner own F-ID, P2 file-tree should, P3 GH
    asymmetry, B1 packaging spike) handled per draft / deferred to
    /pm-roadmap.
