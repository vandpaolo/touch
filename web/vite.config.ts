import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base: './' is load-bearing. The packaged Electron renderer loads the built
// bundle over file://; an absolute base ('/') 404s every asset → blank window.
// Set from day one (phase-T2 plan, HANDOVER gotcha).
//
// server.host: true binds all interfaces so the headless dev box is reachable
// from the laptop browser over Tailscale (browser-dev mode, N5/N6).
export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: {
    alias: {
      // @protocol → the generated wire types. Single source of truth lives in
      // protocol/schema.json; `make codegen` regenerates this file. Consumed
      // only through web/protocol-types.
      '@protocol': fileURLToPath(
        new URL('../protocol/generated/ts/protocol.ts', import.meta.url),
      ),
    },
  },
  server: {
    host: true,
    port: 5173,
  },
})
