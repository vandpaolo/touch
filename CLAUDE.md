# Maquette — Claude project guide

This project follows the **PM Framework** at
`~/projects/vault_theonepiece/Areas/Programming/PM Framework/FRAMEWORK.md`.

**Origin:** Maquette was first designed as long-form prose in
`~/projects/vault_theonepiece/Projects/Maquette/`. Those originals are
preserved unchanged; their content was migrated into `docs/notes/inbox.md`
on 2026-05-16 as the seed for framework synthesis. The vault folder is
the historical record; `docs/` is the live working tree.

## Where things live

- `docs/notes/` — long-form prose (the source of truth for thinking).
- `docs/00-vision.md`, `docs/00-pr-faq.md` — Why (Management layer).
- `docs/01-requirements.md` — What (PM layer).
- `docs/02-architecture.md`, `docs/02-data-model.md`, `docs/02-classes.md`,
  `docs/adr/` — How (Architect layer).
- `docs/03-roadmap.md`, `docs/phases/` — When (planning).
- `docs/blockers/`, `docs/audits/` — friction tracking + pre-phase reviews.

## How to work here

1. The user writes raw notes in `docs/notes/*.md`.
2. The user invokes a `/pm-*` skill — `/pm-vision`, `/pm-requirements`,
   `/pm-architecture`, `/pm-roadmap`, `/pm-phase-plan`, `/pm-phase-start`,
   `/pm-phase-report`, `/pm-blocker`, `/pm-status`, `/pm-audit`,
   `/pm-capture`.
3. Skills read notes + current doc, draft an update, then ask only about
   what notes couldn't cover (Gaps / Probes / Conflicts / Push-back).
4. Conversation-driven capture: when the user says something note-worthy
   mid-chat, write it to the right `docs/notes/*.md` file immediately
   and confirm in one line (`> noted → notes/constraints.md`).

## Active phase

See `docs/03-roadmap.md` frontmatter (`active_phase: ...`) or run
`/pm-status` for a live dashboard.

## Scope-freeze rule

When a phase has `status: in_progress`, **no design edits** until the
phase is either `done` (`/pm-phase-report`) or `blocked` (`/pm-blocker`).
