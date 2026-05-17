# Phases

Per-phase plans and closeout reports.

- `phase-N.md` — plan written by `/pm-phase-plan` before the phase starts.
  YAML frontmatter is the source of truth for status (`planned`,
  `in_progress`, `blocked`, `done`).
- `phase-N-report.md` — closeout written by `/pm-phase-report` after the
  phase ends. Captures what shipped, what slipped, what was learned.

Only one phase may have `status: in_progress` at a time. Manual status
edits are allowed but discouraged — use the skills.
