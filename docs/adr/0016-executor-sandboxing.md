# 0016 — Executor sandboxing: workspace-confined now, OS sandbox later

- **Status:** Accepted
- **Date:** 2026-06-04
- **Deciders:** vandpaolo
- **Relates to:** [ADR-0012](./0012-layer-stack-authoring.md) (the document is now executable code), [ADR-0009](./0009-desktop-shell-electron-sidecar.md).

## Context

With the Layer Stack (ADR-0012), a `.touch` part **is** Claude-authored
build123d that Touch executes. That is a remote-code-execution surface: harmless
for your own parts on your own machine, dangerous the moment you open *someone
else's* `.touch` or run a third-party extension. The threat level tracks the
threat model, so the sandbox level should too.

## Decision

**Start workspace-confined + lightweight; make the executor the single chokepoint
so a real OS sandbox can replace it later, gated on opening untrusted parts.**

- **v0 (personal use):** the executor subprocess runs with **cwd = the workspace
  folder**, **no secrets in env**, **network off by default**, the existing
  timeout, and a **soft import-lint** that *warns* on `os` / `socket` /
  `subprocess`. The agent (Claude Code) is launched scoped to the workspace
  (cwd + tool gating).
- **Single chokepoint.** All layer execution goes through one `Executor`
  boundary so the sandbox is *one swappable component*.
- **Later (gated on untrusted parts):** a real OS sandbox — Linux
  bubblewrap / landlock / namespaces+seccomp, macOS `sandbox-exec`, or a
  container — filesystem confined to the workspace, network denied, resource
  caps.
- **In-process Python restriction is a nudge, not a boundary** — never relied on
  for security.

## Consequences

- Cheap and right for personal v0; encodes the "work in a folder" principle.
- **Explicitly not safe to open strangers' parts / run extensions until the OS
  sandbox lands** — documented; a deliberate, tracked gate (R13).
- Upgrading the sandbox is localized to the `Executor`, not a rewrite.

## Alternatives considered

- **Full OS sandbox from day one.** Rejected: platform-specific work up front,
  premature for personal v0.
- **Status quo (subprocess + timeout only).** Rejected: no filesystem boundary
  even against your own accidental `rm`; folder-confinement is nearly free.
