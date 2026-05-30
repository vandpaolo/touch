// Headless smoke for the shell's sidecar coupling (no Electron, no display).
//
// Exercises the exact spawn + TOUCH_READY parsing the Electron main uses
// (R2/R3/R4), then opens a WebSocket itself and asserts a valid mesh frame
// arrives. This is the CI-able core of Day 3; the actual on-screen Electron
// window (and WebGL render) remains a manual desktop check — see README.
//
// Run: node dist/smoke.js   (after `npm run build`)

import * as path from "node:path";
import { spawnSidecar, devSidecarSpec } from "./sidecar.js";

const FRAME_TIMEOUT_MS = 5_000;

function checkWs(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const ws = new WebSocket(`ws://127.0.0.1:${port}`);
    ws.binaryType = "arraybuffer";
    const timer = setTimeout(() => {
      ws.close();
      resolve(false);
    }, FRAME_TIMEOUT_MS);

    ws.onmessage = (ev) => {
      clearTimeout(timer);
      const buf = ev.data as ArrayBuffer;
      // Minimal header check: version byte == 1 and the frame is long enough
      // to hold the 16-byte header. Full decode is covered by web/verify_day2.
      const ok = buf instanceof ArrayBuffer && buf.byteLength >= 16 && new DataView(buf).getUint8(0) === 1;
      ws.close();
      resolve(ok);
    };
    ws.onerror = () => {
      clearTimeout(timer);
      resolve(false);
    };
  });
}

async function main(): Promise<void> {
  const shellRoot = path.join(__dirname, ".."); // dist/ -> spike/shell
  const handle = spawnSidecar(devSidecarSpec(shellRoot));
  let rc = 1;
  try {
    const port = await handle.port;
    console.log(`sidecar port: ${port}`);
    const ok = await checkWs(port);
    console.log(ok ? "SMOKE_OK" : "SMOKE_FAIL");
    rc = ok ? 0 : 1;
  } catch (err) {
    console.error(`SMOKE_FAIL: ${(err as Error).message}`);
  } finally {
    handle.proc.kill();
  }
  process.exit(rc);
}

main();
