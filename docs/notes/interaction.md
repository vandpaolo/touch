# Interaction model — viewport & mouse

Raw notes on how the user drives the viewport. Source for T3 (picking +
click-to-prompt) and the F3 camera requirement.

## 2026-06-01 — User's mouse scheme (stated in T2 day 8)

- **Left click** → select a part/face and open the prompt on it.
- **Right click** → open a context menu on the selected part.
- **Middle (press scroll wheel) drag** → rotate/orbit.
- **Scroll wheel up/down** → zoom in/out.
- (No pan gesture specified — left unbound for now.)

Bearing on phases:
- **T2 (camera, F3):** implemented the camera-only parts — middle-drag
  orbit + scroll zoom (zoom-to-cursor). Left/right intentionally unbound in
  `web/viewport` so they're free for T3. `web/viewport/Viewport.ts`.
- **T3 (picking + click-to-prompt):** left-click select→prompt and
  right-click context-menu are picking/UX features built there. The mesh
  already streams per-face IDs + finder hints for the left-click pick.
- Pan: revisit if the user wants it (candidate gesture: shift+middle or
  shift+left) — currently omitted per the scheme above.
