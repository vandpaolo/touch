# Touch — web frontend

Vite + React + TypeScript. Runs two ways from one codebase (N5):
- **Electron renderer** in the packaged `.exe` (prod), loaded over `file://`.
- **Browser-dev tab** pointed at a localhost sidecar (the headless-Linux dev loop, N6).

## Commands

```bash
npm install
npm run dev        # Vite dev server (HMR), bound on all interfaces (Tailscale-reachable)
npm run build      # tsc -b && vite build  → dist/
npm run preview    # serve the production build
npm run typecheck  # tsc -b (no emit)
```

`vite.config.ts` sets **`base: "./"`** — required so the packaged Electron
renderer can load assets over `file://` (an absolute base 404s → blank window).

## Wire protocol types

The FE never hand-writes wire types. They are generated from the single
source of truth, `protocol/schema.json`, and imported only through
`web/src/protocol-types` (aliased `@protocol`).

Regenerate after any schema change, from the repo root:

```bash
make codegen
```

This emits `protocol/generated/ts/protocol.ts` (TS, for here) and
`src/touch_backend/_generated/protocol.py` (pydantic, for the backend).

## Module layout (`src/`)

| Module | Role |
|--------|------|
| `app/` | shell: three-panel layout owner (F2), activity bar, status bar |
| `platform/` | capability shim — the sole browser-vs-Electron seam (N5) |
| `protocol-types/` | re-export of the generated `@protocol` wire types |
| `viewport/` | three.js scene + NX camera (Day 7) |
| `file-tree/`, `settings/` | UI placeholders (fleshed out in later phases) |
