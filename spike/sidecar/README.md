# touch-sidecar (T0 spike)

Throwaway packaging-spike sidecar. Deleted in T1a/T1b once the real
`src/touch_backend/` lands. See [`docs/phases/phase-T0.md`](../../docs/phases/phase-T0.md).

WebSocket server that emits one hardcoded, face-tagged cube mesh per client
connection. No LLM, no real planner, no `.touch` — packaging + coupling only.

## Run (dev)

```bash
cd spike/sidecar
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e .
python -m touch_sidecar           # prints: TOUCH_READY <port>
```

In another shell, with the venv active:

```bash
python check_client.py <port>     # connects, decodes, asserts 6 face tags
```

`check_client.py` exiting `PASS` (12 triangles, 6 distinct tags) is the Day-1
"done when".

## Notes / open items

- **Python pin:** `==3.12.*` (R12 — OCP wheels pin to a Python minor; match
  exactly when OCP is bundled on Day 4).
- **Wire format** follows `docs/02-data-model.md §Mesh` (version, vertices,
  normals, indices, face_tag_per_triangle) with a concrete little-endian
  framing documented in `wire.py`. `edge_tag_per_segment` and the
  `face_id_to_finder_hint` JSON envelope are spec fields **deferred to T1b**
  (no edge wireframe or click→selection in the spike); the frame already
  carries a zero edge count so the layout is forward-shaped.
- **Ephemeral port** (R4): the server binds `127.0.0.1:0`; the real port is
  printed on the `TOUCH_READY` line.
