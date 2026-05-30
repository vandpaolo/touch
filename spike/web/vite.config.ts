import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `base: "./"` emits RELATIVE asset paths in the built index.html. Electron
// loads the packaged app via `file://`, where Vite's default absolute base
// ("/assets/...") resolves to the drive root (C:/assets/...) and the JS bundle
// 404s — the window opens but stays blank. Relative paths resolve next to
// index.html instead. (Not caught in Days 2–3: dev mode serves over http://
// from the Vite dev server, where "/" is correct.)
//
// `host: true` so the dev server is reachable from another box on the LAN
// (proves N5/N6: same FE in a browser tab against the Linux sidecar).
// Connect with ?port=<sidecar port>.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: { host: true, port: 5173 },
});
