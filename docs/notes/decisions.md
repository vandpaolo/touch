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

## 2026-05-29 — /pm-architecture (Touch full re-baseline)

- Rewrote 02-architecture.md, 02-data-model.md, 02-classes.md fresh for
  Touch. Maquette versions superseded (in git history).
- 5 new ADRs (Touch-era, monotonic continuation from Maquette's 0001-0004):
  - 0005 — Editor↔engine coupling: localhost WebSocket + our protocol.
  - 0006 — `.touch` JSON as native (operation history, not snapshot).
  - 0007 — Pluggable LLMClient + Claude Code subscription path.
  - 0008 — Picking & face-identity: kernel IDs in mesh + finders +
    append-only v0 (sidesteps full topological naming).
  - 0009 — Desktop shell: Electron + Python sidecar; packaging spike is
    the gating v0 phase-0 risk.
- Four bounded contexts identified: Frontend Shell / Coupling-Protocol
  / Engine / Distribution.
- Repo layout proposed (top-level src/touch_backend/ + web/ + shell/ +
  protocol/) — implements the rename cascade by adopting `touch_backend`
  as the new package name (Maquette `maquette` retained until then).
- "Decisions deferred" list flags FE UI framework (defaulted React) +
  custom binary mesh format + WS auth (v0 binds 127.0.0.1 only).

## 2026-05-30 — /pm-phase-plan (T1a)
- Q (probe): F30 out_root — change the global default to /srv/touch/, or keep portable + dev-host override?
- A: Claude's call — keep the portable dataclass default (Path("output")); set /srv/touch/ as a dev-host-only override via pyproject [tool.touch_backend] or env. Shipped app needs a per-user dir.
- → docs/phases/phase-T1a.md § day 5 + risk R-T1a-1
- Q (probe): CLI binary name after rename (touch / touch-backend / keep maquette)?
- A: Claude's call — rename console script to `touch` (touch = "touch_backend.cli:app"). Matches the product name.
- → docs/phases/phase-T1a.md § day 1 + risk R-T1a-3
- Q (push-back): 3-day gantt vs 5 work-units?
- A: Keep split (units ≠ calendar days; safer pause/resume). Gantt ordering unchanged.
- → docs/phases/phase-T1a.md § sprint breakdown

## 2026-05-30 — T1a Day 1 correction (CLI binary name)
- Q: console script name after rename — `touch`?
- A: NO. `touch` shadows GNU `/usr/bin/touch` inside an active venv (the venv bin precedes /usr/bin on PATH), so `touch newfile` would invoke the CLI instead of creating a file. Renamed the console script to `touch-backend` (matches dist name `touch-backend` + import pkg `touch_backend`). Caught by testing during Day 1.
- → pyproject.toml [project.scripts]; docs/phases/phase-T1a.md § day 1 + R-T1a-3

## 2026-05-30 — T1a scope: rename cascade split
- Q: "rename everything to touch" — what's in scope, and is the repo/dir rename part of T1a?
- A: Split the cascade. T1a = code+tooling identity only (package touch_backend ✓, CLI touch-backend ✓, tests, coverage, import-linter). The repo-identity cascade — local dir maquette→touch, GitHub repo rename + remote + pyproject Documentation URL, CLAUDE.md/README/HANDOVER rewrites — is a SEPARATE focused step between T1a and T1b (deferred from the handover's "part of T1a" framing because the dir mv has venv/memory-dir/VSCode friction best done deliberately). Historical Maquette docs (phase-0..3.5, pre-pivot audits, ADR 0001-0004, blockers) are NEVER renamed — they are preserved history per the 2026-05-29 pivot decision.
- → docs/phases/phase-T1a.md § "Scope boundary"

## 2026-05-31 — /pm-phase-plan (T1b)
- Q (P1, crux): Operation schema in Min, or only on the wire?
- A: Protocol/wire shape is Operation (authoritative from Day 1); the mocked planner returns an Operation and Min's mesh comes from a sample solid. The real Intent→Operation engine + adapter refactor (geometry generated from an Operation history) is Max. Matches the roadmap Min/Max split; keeps Min a true skeleton.
- → docs/phases/phase-T1b.md § Min/Max + R-T1b-1
- Q (P2): new deps this phase?
- A: Yes — websockets, keyring, datamodel-code-generator (py codegen), an OCP tessellation path (ocp_tessellate or direct OCP); claude-agent-sdk import-guarded; TS codegen via npx json-schema-to-typescript (no web/ toolchain yet).
- → docs/phases/phase-T1b.md § days 1-4
- Q (P3): executor process-model (carryover audit FAIL #7)?
- A: Record the decision now — subprocess/worker (running user build123d in-process can crash the server); implement when the adapter→executor path lands (Max). Resolves the 02-classes.md:331 TBD.
- → docs/phases/phase-T1b.md § R-T1b-5
- Q (B1, push-back): spike deletion belongs to T1b?
- A: Keep it as the final cleanup unit (Day 6) in T1b per the roadmap; low risk, releases/tags preserve the artifacts.
- → docs/phases/phase-T1b.md § day 6

## 2026-05-31 — /pm-phase-plan (T2)
- Q (G1+B1, mesh source): how does the FE get a backend-served mesh in T2 before picking/prompt (T3)?
- A: Connect-time demo mesh — the sidecar emits a known cube meshFrame on connect behind a dev flag (~few lines in session.py), deleted once T3 picking drives real geometry. Keeps Min's "backend-served mesh" intact and proves the live WS path end-to-end (rejected: pure FE fixture, requestMesh message, mocked plan path).
- → docs/phases/phase-T2.md § Day 5 + R2
- Q (C1+C2, arch pre-pass): run /pm-architecture before /pm-phase-start T2?
- A: Yes — full pass: name the F2 shell-owner module (web/app), add the browser/Electron capability shim, fix the protocol-layout doc drift (generated py moved to src/touch_backend/_generated/ in T1b). Scope freeze is OFF now. Blocks /pm-phase-start.
- → docs/phases/phase-T2.md § Depends on + R1/R3
- Q (P2, FE dep rules): wire dependency-cruiser in T2?
- A: Defer to a later FE phase (T3+) — T2's module set is too small to be worth it yet.
- → docs/phases/phase-T2.md § R5
- Q (P3, FE tests): test coverage in T2?
- A: Targeted Vitest unit tests for transport (binary frame decode) + doc-store; manual exit-criterion verification for viewport/camera; full E2E + Playwright from T3.
- → docs/phases/phase-T2.md § Days 4/6 + test strategy

## 2026-05-31 — /pm-architecture (pre-T2 scoped pass)
- Q: name + shape the F2 shell-owner and the N5 capability shim; fix the generated-protocol layout drift.
- A: Added `web/app` (shell: three-panel layout owner, mounts every UI surface, app-level wiring; mounted only by `web/main`) and `web/platform` (capability shim: sole owner of Electron-preload/`window.electron`; native file dialogs + keychain with browser fallbacks). FE dep rules added (cruiser-enforced later — deferred per T2 P2). Fixed docs: generated pydantic lives at `src/touch_backend/_generated/` (not `protocol/generated/py/`); TS stays at `protocol/generated/ts/`; `web/main.ts`→`main.tsx`. No new ADR (both modules are direct consequences of the locked F2 + N5).
- → docs/02-architecture.md (FE component view, responsibilities, repo tree, N5 row); docs/02-classes.md (module map, FE class diagram, bounded contexts, dep rules, test strategy, glossary)

## 2026-06-01 — /pm-phase-plan (T3)
- Q (C1/B1, modifier scope): T3's chamfer exit needs the deferred ADR-0008 modifier+finder work — how to scope?
- A: Chamfer in T3, tightly — exactly one modifier (chamfer) + one finder predicate (contains_point). First round-trip is the real click→chamfer. Other modifiers (fillet/hole/shell/pattern) + richer finders stay deferred to the focused Intent→Operation effort.
- → docs/phases/phase-T3.md § Min + R1
- Q (B2/G1, chamfer target): clicking a FACE then "chamfer here" — chamfer applies to edges?
- A: Selecting a face chamfers all edges bounding that face. Picking stays face-only this phase (no edge picking). Finder resolves contains_point → the face → its bounding edges → build123d chamfer.
- → docs/phases/phase-T3.md § Days 5-6 + R2
- Q (B3, planner): which planner for T3's NL→op?
- A: Real AnthropicAPIClient with the dev .env/keychain key now; live verification in T3 (matches roadmap F22). The Settings UI to configure provider/credentials stays T6.
- → docs/phases/phase-T3.md § Depends-on + R3

## 2026-06-01 — /pm-phase-plan (T4)
- Q (scope/R1): one phase or split T4a/T4b?
- A: One phase (~11 days, at the cap) — the persistence + explorer + undo/redo pieces interlock; tight Min, trimmed Max. Split only if it over-runs.
- → docs/phases/phase-T4.md § sprint table + R1
- Q (file I/O): how are .touch files read/written?
- A: Backend over WS — the sidecar owns file I/O under out_root; FE save/open/list go over the WebSocket (identical browser-dev + Electron; works at nexus/touch today). Native OS dialogs via the capability shim deferred to T9.
- → docs/phases/phase-T4.md § Min + R3
- Q (new doc / demo seed): empty new doc or keep the demo cube?
- A: Keep the demo cube as the DEFAULT canvas; "New" creates an empty doc; create-from-scratch (no-selection primary) seeds geometry. demo_mesh stays on by default (make up unchanged). Undo-to-empty still works (demo cube is op[0]).
- → docs/phases/phase-T4.md § Min + R4
- Q (C1, forced): T4 exit needs creating a cube from scratch (skipped T3 Max).
- A: Folded into Day 6 as required scope (no-selection primary → box/cylinder/sphere); the FE gap is a prompt entry without a face click.
- → docs/phases/phase-T4.md § Min + Day 6 + R2

## 2026-06-01 — /pm-requirements (T4 re-scope: folder workspace)

Resolving blocker 2026-06-01-folder-workspace-explorer.
- Q: explorer model? → A: VS-Code/Cursor folder workspace. Open Folder → Explorer mirrors a folder 1:1; create/open `.touch` parts in it. F18 revised + bumped should→must; F10 revised to part save/open; F32 (Open Folder, files on the user's machine), F33 (activity rail: Explorer real, Search/Git/Extensions inert stubs for a future extensions story, Settings), F34 (top menu dropdowns), N13 (cross-mode file access). → 01-requirements.md
- Q: file ownership? → A: frontend owns the folder; backend rebuilds from streamed op-history. The *mechanism* (File System Access API in browser / Electron native dialog / react-arborist + Codicons, built in-stack not copied) is deferred to /pm-architecture (kept out of requirements). → 01-requirements.md §F32 + /pm-architecture next
- Q (roadmap): T14 (multi-file/folder model) + open-decision #5 (multi-doc) pulled forward? → A: T4 absorbs the folder Explorer + Open Folder + menus; editor tabs + the multi-doc model become the next phase (T14 pulled up). One /pm-roadmap touch to re-sequence.
- Q (tabs timing, conflict resolved): → A: Explorer now, editor tabs next phase. F35 stays `should`/follow-on.

## 2026-06-01 — /pm-architecture critic panel → revised ADR-0010

Ran a 5-pass adversarial critic panel on the folder-workspace architecture; 4/5 returned "reconsider". Outcome — revised the design (ADR-0010 rewritten):
- **File ownership flipped back to backend-owns-the-folder + frontend-owns-the-interaction** (user delegated the call; agreed BE is functionally correct). The sidecar lists/reads/writes the workspace tree over the WS and stays the single source of truth; `web/platform` provides only the folder *picker* (Electron native dialog → local sidecar; browser-dev a host folder). Same Open-Folder→1:1-tree UX, reuses the T4 backend, no FSA quirks / split-brain / O(history) opens. Electron desktop = a real local folder (files never leave the machine). Browser File System Access API (laptop folder in the tab) = deferred nicety.
- **Hand-rolled recursive tree (~200 lines) + Codicons (MIT)** — dropped `react-arborist` (single-maintainer / React-19 risk; virtualization premature for shallow part-folders).
- **State is multi-doc-ready now** — `Session` keys documents by id with per-document undo/redo + dirty; `web/doc-store` mirrors per-id; UI shows one active. Editor-tab strip ships next phase without re-architecting.
- **Content-addressed rebuild cache** (hash of op-history prefix → STEP/mesh) → open/undo/redo/tab-switch O(1), not O(history).
- → docs/adr/0010-workspace-and-file-ownership.md; 02-architecture.md; 02-classes.md; 02-data-model.md

## 2026-06-04 — conversation: pivot to a Claude-Code-driven CAD IDE ("Touch as the port between CAD and LLMs")

A direction-setting brainstorm (full decision board worked through one-by-one).
Research + a throwaway spike (claude 2.1.132, subscription/OAuth, a FastMCP
stdio server) confirmed the feasibility BEFORE these decisions: stream-json in/out
for a custom panel, --mcp-config, tool-call loop, and the agent SEEING a render
returned by an MCP tool — all on the subscription, zero API tokens. Spike lives
in /tmp/touch-spike (throwaway). Locked decisions:

- **Vision** — open-source, standalone CAD IDE; the user's OWN Claude Code is the
  brain via MCP; FEM/CAM + third-party extensions are future *workbenches over the
  MCP boundary*, not build123d. (Reframes vision from "friend installs an .exe and
  types" toward "the CAD IDE you point your own coding agent at".)
- **Authoring = the Layer Stack** — a part is free build123d; each edit is a
  *layer* (code block transforming the previous solid). The layer is the
  hoverable/clickable/reorderable unit. Clickability comes from *computed
  provenance* (geometric diff per layer → which layer made each face, baked into
  the existing per-face/edge mesh ids), NOT from decompiling code into ops (general
  build123d→ops is impossible). Structured T3–T5 ops survive as *recognized
  templates* (parametric cards); everything else is a code card. Reliability spine:
  deterministic ordered re-execution from clean state + per-layer content-addressed
  cache (reuse the mesh cache). Durability rules: selections via finder/datum
  helpers, fail-loud on ambiguous selection, lint raw positional `.faces()[i]`.
  (Four parallel evaluator agents converged "sound-with-changes"; central risk =
  topological naming, mitigated by append-only v0.)
- **Why MCP if it's all build123d** — MCP is not how Claude writes code; it's how
  Claude touches the LIVE app: current selection, render-as-eyes, kernel queries,
  live layer-stack mutation w/ undo. It's also the extensibility port (FEM/CAM/
  extensions). build123d is the geometry layer; FEM/CAM *consume* the solid, so
  pure-build123d for geometry is correct (and OCC aligns with the open FEM/CAM
  ecosystem). Don't over-abstract the document now.
- **Session coordination** — ONE shared live document in the backend; viewport +
  agent act on the same part. (Evolve Session from strictly per-connection; the
  deferred T4b multi-doc refactor pulled in. v0 = one part open at a time.)
- **MCP placement** — a separate stdio process Claude Code spawns, forwarding to
  the running backend over the existing WS protocol; thin adapter, not a 2nd engine.
- **Two brains** — keep BOTH: the built-in T5 planner (quick click-to-prompt, no
  login, emits recognized-template layers) AND Claude Code (power agent). Both emit
  layers into the one shared stack.
- **Apply model** — live-apply + undo; explicit confirm only for destructive ops.
- **Agent panel UI** — right-side, VS-Code-Claude style. Left = Explorer + a Layer
  Stack panel (the feature tree). Center = viewport with 3D/code editor-tab views.
  Two-way selection bridge (click face → highlight owning layer + drop a context
  chip into the agent input; click layer → highlight its faces; agent has
  get_selection). MCP tools (from the eval): list_layers (ids+summary+thumbnail,
  not code), get_layer, add_layer, edit_layer, render(scope), reorder, delete_layer,
  get_selection — every mutation returns {error|success, thumbnail, manifold check,
  downstream-delta + finder-rebind warnings}. Prefer append; edit_layer is the
  risky exception. Keep layer code out of context (reference by id) to protect the
  prompt cache. One semantic op per layer.
- **Recognized-template scope (v0)** — box, cylinder, sphere, chamfer (the existing
  vocabulary); grow later.
- **Re-edit/reorder earlier layers** — DEFERRED; append-only v0 (+ delete-last +
  undo). The reference-re-resolution subsystem (toponaming) is a later phase.
- **Executor sandboxing** — START workspace-confined + lightweight: subprocess
  cwd=workspace, no secrets in env, network off by default, existing timeout, soft
  import-lint warning on os/socket/subprocess. Make the Executor the single
  chokepoint so a REAL OS sandbox (bubblewrap/landlock/sandbox-exec/container,
  network-deny, fs-confined) slots in later, gated on "open an untrusted part /
  run an extension". In-process Python sandboxing is a speed bump, not a wall.
- **v0 sequencing** — MCP-FIRST: backend Layer Stack + shared doc + MCP server,
  driven from the user's EXISTING Claude Code (validate the loop, usable
  immediately) → THEN embed Claude + the right-side panel (Path A).
- **Deferred decisions** — CLI packaging (bundle `claude` vs require it) → decide
  at the embed milestone; open-source license + public repo → decide before going
  public.

Correction to existing design: F31/ADR-0007 assumed a "Claude Code mode via
claude-agent-sdk under the subscription" — research shows the Agent SDK now
requires a paid API key (OAuth restricted to Claude Code + claude.ai, Feb 2026),
so the token-free path is MCP, not the SDK. To reconcile in the architecture pass.

- → feeds /pm-vision, /pm-requirements, /pm-architecture (new ADRs: Layer Stack
  authoring; session coordination; MCP boundary; two-brain; sandboxing), /pm-roadmap.

## 2026-06-04 — conversation/context architecture (4-agent analysis) — locked

Resolves "one Claude Code conversation vs two / memory-stacks bloat". Four
parallel evaluator agents (topology, context/memory, CAD context-packet,
routing) converged. Locked model: **one brain (the user's Claude Code),
reached via two surfaces; the backend Layer Stack is the source of truth.**

- **Topology** — a persistent **main thread = the side panel** (the project
  brain of record) that **spawns ephemeral positional subagents** for
  click-to-prompt (Claude Code subagent/Task mechanic). Subagents spawn *from
  the main thread* (so the main conversation keeps project context/history),
  run with isolated context seeded by a positional packet, do the local edit,
  and **summarize ONE line back** to the parent. The "click → discuss → accept
  → implement" bubble is a scoped sub-session. NOT one giant conversation
  (bloats), NOT two independent persistent brains (divergence).
- **Built-in T5 planner** — demoted from co-equal brain to an **optional
  no-account fallback** (keep cheaply or drop later). Claude Code is the brain
  for both surfaces. ("Both can be a thing" was about the two *surfaces*, not
  two LLM brains.)
- **Context/memory (the worry, solved)** — backend is canonical; the
  conversation references state **by id**. Agent holds a compact layer
  *manifest*, pulls full code/renders **on demand**. **Renders = thumbnails,
  on demand** (never auto-attached every turn — the #1 bloat; images ~1.6–4.8K
  tokens). Click context enters as a small structured packet, not raw data.
  Scoped click-threads collapse to a one-line summary. Keep the system prompt +
  MCP tool list byte-stable for prompt-cache hits. Subscription currency =
  tokens-per-edit → id-referencing + thumbnail-gating keep it low.
- **Two distinct context packets** — *positional*: selection-anchored (entity
  kind+id, owning layer, a **finder reference**, picked point + normal, surface
  type, 1-ring neighbors, touchable params, units, stack revision). *macro*:
  part-overview (param table, compact layer-stack outline, part bbox, units,
  recent selection) — NO picked point / no 1-ring. Across both: inject **finder
  references, never raw indices**; picked-point+normal is the disambiguator.
- **Routing & consistency** — surface chosen by the **act** (clicked geometry →
  positional; typed in panel → macro), not by asking the user. Both surfaces
  are **stateless views over a versioned backend**: every edit bumps a
  layer-stack revision; mutations carry their expected revision and are
  **compare-and-swap'd** (reject → re-plan) → no stale-context races. A local
  edit **self-implements only if it's a leaf append** (top layer, no
  shared-param mutation); otherwise it **escalates** to macro for placement.
  Macro always receives a one-line feed of every accepted edit. **Single
  backend executor** = one code path, one place to enforce stack invariants.
- **Click resolves to a stable entity id** (re-resolved at accept, fail loud if
  it vanished) — never a frozen screen coordinate.

Caveat surfaced: Claude Code subagents are single-shot from the parent's view,
so a multi-turn interactive refine *inside* a click bubble isn't natively a
parent-visible resumable loop — implement the bubble as a short subagent run
(it may take a few autonomous turns) or a harness-managed `--resume` sub-session
with a turn cap (reuse F7's cap). To validate in the MCP-first spike.

- → feeds /pm-architecture (ADRs: conversation topology + context model;
  routing/consistency = versioned layer stack + CAS; two context packets) and
  /pm-requirements (the two surfaces; finder-reference selection). Refines the
  2026-06-04 pivot entry above (two brains → one brain, two surfaces).

## 2026-06-22 — /pm-phase-plan (TP2)
- Q (push-back B1): TP2 hit 10 days (cutover folded in). Keep one phase or split into TP1.5?
- A: Keep the cutover as TP2 sprint 1 (its first real consumer — the agent/second writer — arrives in the same phase).
- → docs/phases/phase-TP2.md § Sprint 1 / Depends on

- Q (probe P1): Exit benchmark's extrusion + hole — code layers or new recognized templates?
- A: Code layers (chamfer stays a template). Matches the v0 vocabulary; exercises the code-layer path (the agent's main authoring mode); no new recognition work.
- → docs/phases/phase-TP2.md § Exit criterion / Day 6

- Q (push-back B2 / gap G1): N15 (flat per-turn context) — Min or Max? What bar?
- A: Min, with the flat-token bar (≥20-edit session: per-turn input tokens ~flat + prompt-cache read-hits > 0).
- → docs/phases/phase-TP2.md § Day 9 / Exit criteria

- Q (conflict C1): F41 names edit_layer/reorder_layer but v0 is append-only (F38). v0 tool semantics?
- A: **Resolved → option A (last-layer-only edit/delete + structured reorder refusal).** Initial pick was "implement fully", but that reopens toponaming (R16), contradicts F38's "append-only in v0" must, and pulls T15 (which needs T11 evaluator + T12 schema-v2a first) into TP2 — for zero exit-benchmark payoff (the build is a pure append sequence). The user asked for my opinion + an unbiased panel: 3 independent evaluators (architecture/risk, product/scope, agent-UX) + the plan author were unanimous on A at high confidence. All independently flagged the same residual risk + mitigation: the refusal must be a **permanent/non-retryable, actionable** envelope (name the legal alternative `delete_layer`→`add_layer` + the last-layer id) so the agent re-plans instead of retry-thrashing. Full re-edit/reorder stays T15.
- → docs/phases/phase-TP2.md § Day 6 / § Known risks (C1)

## 2026-06-25 — TP2 D2 implementation: full layer-native cutover (wire + persistence)
- Q: Implementing the layer-native `.touch` save/open (D2) surfaced that a code
  layer can't be serialized over the op-history wire (`MsgDocument.history:
  Operation[]`) — the layer→op reverse is lossy (chamfer distance lives in
  source; F40 forbids decompiling it). The op-wire and FE stay op-based through
  TP2 (the FE layer panel is TP3), so persistence and wire conflicted.
- A (user, 2026-06-25): "migrate to layers immediately, who cares about the old
  architecture — swap it without regret." Full cutover: no op-history compat.
  `MsgDocument` now carries a compact `LayerSummary[]` manifest (id/kind/template/
  params/has_selection, no source — N15) + the stack `revision`. The session
  drops `_wire_ops`; undo/redo are delete-last/re-add of Layers. `.touch` is
  layer-native (an old op-history file still migrates forward on open).
- This **folds the wire half of D3 into D2** (a code layer can't go over an
  op-shaped wire). D3 remainder = the live change-feed push (revision-driven).
- → src/touch_backend/session.py, protocol/schema.json (+LayerSummary), regen;
  web/src/doc-store + App.tsx. Commit 241ab04. Reshapes docs/phases/phase-TP2.md
  Days 2-3 (an implementation re-sequence within the phase, not a scope change).

## 2026-06-26 — TP2 D5-prep: isolate OCP to a worker subprocess (GL-clean backend)
- Q: Wiring `render_view` (Day 5) surfaced that the long-lived backend process is
  permanently **OSMesa-poisoned**: `live_build.build_mesh` imported build123d/OCP
  *in-parent* (to `import_step` the per-layer solids + tessellate + bake
  provenance), and once OCP grabs the process-global Mesa GL context, any
  in-process off-screen render returns blank (auto-memory `render-backend`). So
  the backend could never render. Two fixes considered: (A) keep poisoning, render
  in a separate clean process; (B) push **all** OCP behind a subprocess boundary so
  the backend orchestrator imports zero OCP — then it renders in-process.
- A (user, 2026-06-26): **fix the root cause — approach B, combined worker.** The
  user explicitly wanted the long-term-correct boundary, not a render-only patch.
  Decided the *combined* worker variant (build + tessellate + provenance in ONE
  subprocess) over a two-hop STEP-mediated worker, because the combined worker
  pays the OCP import once per build (protects N2 latency) and is cohesive.
- Why it's more than rendering: this also advances **N8** (a geometry segfault
  kills a worker, not the server) and **R13** (OCP confined to the worker makes the
  executor the *real* sandbox chokepoint). The boundary is lifecycle-agnostic — if
  N2 later needs a *persistent* geometry worker, swap the per-build spawn for RPC
  behind the same `Mesh` serialization interface, with no orchestrator change.
- Implementation: new `mesh_dump.py` (in-subprocess worker → `mesh.npz`+`mesh.json`);
  `build_mesh` appends a `dump_mesh` epilogue to the emitted stack and reconstructs
  the `Mesh` numpy/json-only; a 15th import-linter contract forbids *direct*
  build123d/OCP imports in the orchestrator (`allow_indirect_imports` so the
  Mesh/ProvenanceEntry type refs through the lazily-OCP modules are fine). 331
  tests green (incl. the existing exact-set provenance round-trip assertions).
- → src/touch_backend/mesh_dump.py (new), live_build.py, pyproject.toml. Commit
  ca3fd4f. Candidate for a short ADR + 02-architecture reconcile at /pm-phase-report
  (the "all OCP behind the worker boundary" rule belongs in the design-of-record).
