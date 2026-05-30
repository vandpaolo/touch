# touch-web-spike (T0 spike, Day 2)

Throwaway frontend for the packaging spike. Vite + React + TypeScript +
three.js viewport that connects to the Day-1 sidecar, renders its face-tagged
cube, and highlights a face on hover (local raycaster + `face_tag_per_triangle`
lookup — no backend round-trip on hover). Deleted in T1a/T1b.

See [`docs/phases/phase-T0.md`](../../docs/phases/phase-T0.md) (Day 2).

## Run (browser-tab dev, proves N5/N6)

1. Start the sidecar and note its port:

   ```bash
   cd ../sidecar && . .venv/bin/activate && python -m touch_sidecar
   # -> TOUCH_READY <port>
   ```

2. Start the dev server and open the page with the sidecar port:

   ```bash
   npm install      # first time
   npm run dev      # serves http://localhost:5173 (host:true → LAN-reachable)
   ```

   Open `http://localhost:5173/?port=<port>`.

**Done when (visual):** the cube renders; mousing over each of the 6 faces
shows a distinct highlight colour; orbit with the mouse; hover latency feels
instant (< 16 ms). This is a manual browser check — WebGL needs a real GL
context.

## Headless checks (CI-able, no GPU)

```bash
npm run build              # tsc -b + vite build — type-check + bundle
bash verify_day2.sh        # start sidecar, decode its frame with src/wire.ts,
                           # assert 8 verts / 12 tris / 6 faces (FE<->BE parity)
```

`verify_day2.sh` proves the frontend decoder matches the backend encoder; it
does **not** exercise three.js rendering/hover (that's the visual check above).

## Notes

- `src/wire.ts` mirrors `spike/sidecar/touch_sidecar/wire.py`
  (docs/02-data-model.md §Mesh). Keep the two in lockstep.
- The cube is drawn as a non-indexed geometry (each triangle owns its
  vertices) so per-face colouring is crisp and the raycaster's `faceIndex`
  maps 1:1 to a triangle → `face_tag_per_triangle[faceIndex]`. This is the
  picking pattern T1b reuses against the real tessellator.
- `?port=` is injected by Electron in the packaged app (Day 3); in browser
  dev you append it by hand.
