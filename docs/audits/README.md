# Audits

Pre-phase audit reports produced by `/pm-audit` (Auditor sub-agent).

Filename: `YYYY-MM-DD-pre-phase-N.md`. Each report covers the 9 checks
from the framework (coverage, NFR satisfaction, reference integrity,
ADR coverage, glossary, phase readiness, stale TODOs, notes hygiene,
frontmatter validity).

A phase cannot flip to `in_progress` with open `FAIL`s in its most recent
audit unless the user explicitly overrides (override is recorded in the
audit file).
