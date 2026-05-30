import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Spike dev server. `host: true` so the page is reachable from another box
// on the LAN (proves N5/N6: same FE in a browser tab against the Linux
// sidecar). Connect with ?port=<sidecar port>.
export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173 },
});
